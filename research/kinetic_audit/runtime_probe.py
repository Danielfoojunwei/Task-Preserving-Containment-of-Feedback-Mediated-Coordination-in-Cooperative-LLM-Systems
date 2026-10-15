"""Actual installed-runtime gate; zero model calls.

No fallback mocks. This module must fail when the pinned package is unavailable.
"""
from __future__ import annotations
import argparse
import asyncio
import json
from pathlib import Path
import sys
from .core import Cell, Ledger, score_paths
from .instrumentation import make_protocol_class
from .preflight import check
from .run import load_runner, seed_everything

async def probe(root, out):
    import yaml
    from terrarium.blackboard import Blackboard, Megaboard
    from terrarium.networks import build_communication_network
    from experiments.common.local_protocol import LocalCommunicationProtocol
    runtime=load_runner(root)
    results=[]
    for feedback in ["original","peer_snapshot","suppress_score"]:
        seed_everything(101)
        cfg=yaml.safe_load((root/"experiments/collusion/configs/collusion_jira_topologies.yaml").read_text())
        cfg["simulation"].update(seed=101,max_iterations=1,max_planning_rounds=2)
        cfg["communication_network"].update(topology="complete",num_agents=4,consolidate_channels=True)
        cfg["environment"].update(max_tasks=8,assignment_filling=False)
        ledger=Ledger(out/f"probe_{feedback}.jsonl")
        P=make_protocol_class(LocalCommunicationProtocol,Megaboard,Blackboard,
               cell=Cell(101,"cooperative",False,feedback),ledger=ledger)
        protocol=P(config=cfg)
        Env=runtime._resolve_environment_class(cfg["environment"])
        env=Env(protocol,cfg,tool_logger=type("TL",(),{"log_dir":out})())
        protocol.environment=env
        names=env.get_agent_names()
        env.set_communication_network(build_communication_network(names,cfg))
        await env.async_init()
        await protocol.generate_comm_network(names[:2],"Fixed runtime-probe private channel",
                                template={"secret_channel":True,"visibility":"secret"})
        protocol._boundary(env)
        # This probe verifies the first-assignment numerical pathway, not collusion.
        task=next(iter(env.tasks))
        response=await protocol.environment_handle_tool_call("assign_task",names[0],
                         {"task_id":task},phase="execution",iteration=1)
        if "error" in response or response.get("status")!="success":
            raise RuntimeError(f"Real task tool rejected probe: {response}")
        contexts=await protocol._prefetch_blackboard_events(names[1],phase="execution",iteration=1)
        reads=[r["data"] for r in ledger.records if r["kind"]=="board_read"]
        peer=any(x["score_paths"] for x in reads if x["agent"]==names[1])
        # The pinned runtime exposes the final reward only after every agent acts.
        # Preserve the first-action exposure check above, then finish fixed actions.
        for name, task_id in zip(names[1:], list(env.tasks)[1:]):
            receipt=await protocol.environment_handle_tool_call("assign_task",name,
                         {"task_id":task_id},phase="execution",iteration=1)
            if receipt.get("status")!="success":
                raise RuntimeError(f"Real task tool rejected completion: {receipt}")
        row={"feedback":feedback,"actor_score":bool(score_paths(response)),"peer_score":peer,
             "summary":env.get_final_summary(),"actor_receipt":response,
             "recipient_context":contexts,"evidence":"REAL_INSTALLED_RUNTIME_SCRIPTED_TOOL_CALL"}
        results.append(row)
        (out/f"probe_{feedback}_head.txt").write_text(ledger.head+"\n")
    expected=[(True,True),(True,False),(False,False)]
    observed=[(r["actor_score"],r["peer_score"]) for r in results]
    if observed!=expected:
        raise RuntimeError(f"Mechanism not reproduced: {observed}; expected {expected}. No live gate.")
    from .core import finite_number
    rewards=[finite_number(r["summary"]["joint_reward"]) for r in results]
    if max(rewards)-min(rewards)>1e-7:
        raise RuntimeError("Intervention changed fixed-action reward; inspect runtime")
    return {"status":"PASSED_REAL_RUNTIME_PROBE","llm_calls":0,"results":results,
        "evidence_boundary":"Full installed source/tool integration; no model behavior measured",
        "external_attestation":False}

def main():
    p=argparse.ArgumentParser();p.add_argument("--upstream",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True);a=p.parse_args()
    a.out.mkdir(parents=True,exist_ok=False,mode=0o700)
    root=a.upstream.resolve();sys.path.insert(0,str(root));pf=check(root)
    if not pf["ready"]:
        result={"status":"BLOCKED_MISSING_OR_MISMATCHED_RUNTIME","preflight":pf,"llm_calls":0}
        (a.out/"runtime_gate.json").write_text(json.dumps(result,indent=2)+"\n")
        print(json.dumps(result,indent=2));raise SystemExit(2)
    try:result=asyncio.run(probe(root,a.out))
    except Exception as exc:
        result={"status":"FAILED_REAL_RUNTIME_PROBE","error":str(exc),"llm_calls":0}
    result["preflight"] = pf
    (a.out/"runtime_gate.json").write_text(json.dumps(result,indent=2,default=str)+"\n")
    print(json.dumps({"status":result["status"],"llm_calls":0}))
    raise SystemExit(0 if result["status"]=="PASSED_REAL_RUNTIME_PROBE" else 2)
if __name__=="__main__":main()
