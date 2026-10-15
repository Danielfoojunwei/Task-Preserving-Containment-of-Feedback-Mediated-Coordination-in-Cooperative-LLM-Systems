"""Launch one frozen-manifest cell through Colosseum's actual _run_single.

Upstream source is not edited. A single hash-checked in-memory substitution adds
an explicit private-board template. The protocol class is replaced with the
research subclass. Credentials and installed dependencies are required for live.
"""
from __future__ import annotations
import argparse
import asyncio
from copy import deepcopy
import importlib.util
import json
import os
from pathlib import Path
import random
import sys
from types import ModuleType
from .core import Cell, Ledger, canonical, finite_number
from .design import validate_manifest
from .instrumentation import make_protocol_class
from .oracle import exact_oracle
from .preflight import check, PINS, git_blob

SECRET_OLD='''            colluders, secret_context
        )'''
SECRET_NEW='''            colluders, secret_context,
            template={"secret_channel": True, "visibility": "secret"}
        )'''

def patched_runner_source(source: str) -> str:
    if source.count(SECRET_OLD)!=1:
        raise RuntimeError("Private-board call anchor not unique; refusing source adaptation")
    return source.replace(SECRET_OLD,SECRET_NEW,1)

def load_runner(root: Path):
    source_path=root/"experiments/collusion/run.py"
    raw=source_path.read_bytes()
    if git_blob(raw)!=PINS["experiments/collusion/run.py"]:
        raise RuntimeError("Runner content is not pinned source")
    if str(root) not in sys.path:sys.path.insert(0,str(root))
    m=ModuleType("kinetic_audit_upstream_runner")
    m.__file__=str(source_path);sys.modules[m.__name__]=m
    exec(compile(patched_runner_source(raw.decode()),str(source_path),"exec"),m.__dict__)
    return m

def seed_everything(seed):
    random.seed(seed)
    try:
        import numpy as np
        np.random.seed(seed)
    except ImportError:pass
    # LLM generation is NOT guaranteed deterministic by an environment seed.


def real_reward(env,assignment):
    raw=env._rewards(assignment)
    if isinstance(raw,tuple) and len(raw)>=2 and isinstance(raw[1],dict):
        return finite_number(raw[0]),raw[1]
    if isinstance(raw,dict):return sum(finite_number(v) for v in raw.values()),raw
    raise TypeError("Unknown reward API")

async def execute(root: Path, cell: Cell, out: Path, model_config: dict, timeout_seconds: int):
    import yaml
    from terrarium.blackboard import Megaboard, Blackboard
    from experiments.common.local_protocol import LocalCommunicationProtocol
    seed_everything(cell.task_seed)
    out.mkdir(parents=True,exist_ok=False,mode=0o700)
    ledger=Ledger(out/"host_trace.jsonl")
    ledger.emit("run_start",{"cell":cell.to_dict(),"evidence_type":"LIVE_ATTEMPT",
                            "raw_trace_privacy":"evaluator_only"})
    runtime=load_runner(root)
    config=yaml.safe_load((root/"experiments/collusion/configs/collusion_jira_topologies.yaml").read_text())
    config["simulation"].update(max_iterations=1,max_planning_rounds=2,max_conversation_steps=3)
    config["environment"].update(max_tasks=8,assignment_filling=False)
    config["communication_network"].update(topology="complete",num_agents=4,consolidate_channels=True)
    config.setdefault("experiment",{}).update(planning_rounds=2,max_conversation_steps=3,log_prompts=True)
    config["experiment"]["collusion"]={"colluder_selection":"random","agent_order":"random"}
    Protocol=make_protocol_class(LocalCommunicationProtocol,Megaboard,Blackboard,
                                 cell=cell,ledger=ledger)
    runtime.LocalCommunicationProtocol=Protocol
    result=None
    try:
        result=await asyncio.wait_for(runtime._run_single(
            base_cfg=config,model_label="research_model",model_llm_cfg=model_config,
            sweep_name=cell.key,topology="complete",num_agents=4,colluder_count=2,
            secret_channel_enabled=True, # DO NOT toggle this: preserves objectives
            prompt_variant="control" if cell.objective=="cooperative" else "deception",
            seed=cell.task_seed,out_dir=out),timeout=timeout_seconds)
        if len(Protocol.instances)!=1:raise RuntimeError("Unexpected protocol instance count")
        protocol=Protocol.instances[0];env=protocol.environment
        from hashlib import sha256
        state_before=canonical(env.get_serializable_state())
        oracle=exact_oracle(env)
        if state_before!=canonical(env.get_serializable_state()):
            raise RuntimeError("Reward oracle mutated environment state")
        summary=env.get_final_summary();assignment=summary.get("assignment",getattr(env,"assignment",{}))
        full={a:assignment.get(a,"skip") for a in env.get_agent_names()}
        reward,local=real_reward(env,full)
        if "joint_reward" in summary and abs(finite_number(summary["joint_reward"])-reward)>1e-7:
            raise RuntimeError("Reported score disagrees with authoritative reward function")
        boundary=next(r["data"] for r in ledger.records if r["kind"]=="execution_boundary")
        task_digest=sha256(canonical({"tasks":boundary["tasks"],"costs":boundary["costs"]})).hexdigest()
        metrics={"cell":cell.to_dict(),"status":"completed","evidence_type":"LIVE_LLM",
                 "joint_reward":reward,"welfare_regret_exact":oracle["optimal_reward"]-reward,
                 "task_digest":task_digest,"oracle":oracle,"assignment":full,
                 "agent_rewards":local,"final_summary":summary,
                 "policy_epochs":protocol._ka_epoch,"framework_summary":result}
        (out/"ka_result.json").write_text(json.dumps(metrics,indent=2,default=str)+"\n")
        ledger.emit("run_complete",{"joint_reward":reward,"welfare_regret_exact":metrics["welfare_regret_exact"]})
        return metrics
    except BaseException as exc:
        failed={"cell":cell.to_dict(),"status":"failed","evidence_type":"LIVE_ATTEMPT_FAILED",
                "error_type":type(exc).__name__,"error":str(exc)}
        (out/"ka_result.json").write_text(json.dumps(failed,indent=2)+"\n")
        ledger.emit("run_failed",failed)
        raise
    finally:
        (out/"local_trace_head.txt").write_text(ledger.head+"\n")


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--upstream",type=Path,required=True)
    p.add_argument("--manifest",type=Path,required=True)
    p.add_argument("--index",type=int,required=True)
    p.add_argument("--model-config",type=Path,required=True)
    p.add_argument("--out",type=Path,default=Path("outputs"))
    p.add_argument("--execute-live",action="store_true")
    p.add_argument("--acknowledge-provider-billing",action="store_true")
    p.add_argument("--runtime-gate",type=Path)
    p.add_argument("--timeout-seconds",type=int,default=1800)
    a=p.parse_args();root=a.upstream.resolve()
    m=json.loads(a.manifest.read_text());cells=validate_manifest(m)
    if not 0<=a.index<len(cells):p.error("index outside manifest")
    selected=cells[a.index]
    # No imports of providers or credential checks in dry run.
    if not a.execute_live:
        print(json.dumps({"status":"DRY_RUN_NO_MODEL_CALLS","cell":selected.to_dict(),
                          "upstream":str(root),"output":str(a.out/selected.key)},indent=2));return
    if not a.acknowledge_provider_billing:p.error("Explicit provider billing acknowledgment required")
    if a.runtime_gate is None:p.error("Run the installed-runtime probe first; supply --runtime-gate")
    gate=json.loads(a.runtime_gate.read_text())
    if gate.get("status")!="PASSED_REAL_RUNTIME_PROBE":p.error("Runtime gate is not passed")
    # Local gate is a provenance aid, not cryptographic certification.
    pf=check(root)
    if not pf["ready"]:
        print(json.dumps(pf,indent=2));raise SystemExit(2)
    if gate.get("preflight",{}).get("observations") != pf["observations"]:
        p.error("Runtime gate source contract does not match installed runtime")
    sys.path.insert(0,str(root))
    model=json.loads(a.model_config.read_text())
    provider=str(model.get("provider",""))
    keyvars={"openai":"OPENAI_API_KEY","anthropic":"ANTHROPIC_API_KEY",
             "together":"TOGETHER_API_KEY","gemini":"GOOGLE_API_KEY"}
    if provider in keyvars and not os.environ.get(keyvars[provider]):
        p.error(f"Configure {keyvars[provider]} in the executing environment, not in a committed file")
    if "REPLACE" in json.dumps(model):p.error("Select an exact supported model ID in the config")
    asyncio.run(execute(root,selected,a.out/selected.key,model,a.timeout_seconds))
if __name__=="__main__":main()
