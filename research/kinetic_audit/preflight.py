from __future__ import annotations
import argparse
import hashlib
import importlib.metadata
import importlib.util
import json
from pathlib import Path
import subprocess

UPSTREAM="b077fe7e2f10566e92156cc12e06ffb2aac54790"
PINS={
 "experiments/common/local_protocol.py":"8b6d3d915cabe9c308b4cb06c574eeb9b4f71772",
 "experiments/collusion/run.py":"56dcfc1d66d447e5a0d9ba32935a398d36195b6e",
 "experiments/collusion/metrics.py":"a743d5c4cbf3419d53f1049faf11a36041ec8188",
 "pyproject.toml":"b65fa0b693bec6bc8636670c86e3fc2a1a4ccdae",
}
DEPENDENCY_PINS={"terrarium/blackboard.py":"0ae6ac7f6dd4ced4b49a6ff6de019a721f1bf01d",
 "envs/dcops/jira_ticket/jira_ticket_env.py":"4a9f49b072a52771f858ad6c7fa11cb56d22f695",
 "envs/dcops/jira_ticket/jira_ticket_tools.py":"3e891c2abb6490c2444897e8660170d749d99e1f"}

def git_blob(data):
    return hashlib.sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest()

def check(root: Path, *, require_runtime=True):
    failures=[];observations={}
    for name,expected in PINS.items():
        f=root/name
        observed=git_blob(f.read_bytes()) if f.is_file() else None
        observations[name]=observed
        if observed!=expected:failures.append(f"source pin mismatch/missing: {name}")
    if require_runtime:
        try:version=importlib.metadata.version("terrarium-agents")
        except importlib.metadata.PackageNotFoundError:version=None
        observations["terrarium_version"]=version
        if version!="0.1.1":failures.append("terrarium-agents==0.1.1 is required")
        for rel,expected in DEPENDENCY_PINS.items():
            module=rel.removesuffix(".py").replace("/",".")
            try:
                spec=importlib.util.find_spec(module)
                p=Path(spec.origin) if spec and spec.origin else None
                observed=git_blob(p.read_bytes()) if p and p.is_file() else None
            except (ImportError,ValueError,AttributeError):observed=None
            observations[rel]=observed
            if observed!=expected:failures.append(f"dependency pin mismatch/missing: {rel}")
    return {"ready":not failures,"failures":failures,"observations":observations,
            "upstream_commit":UPSTREAM,"evidence":"RUNTIME_PREFLIGHT_NOT_LLM_RESULT"}

def main():
    p=argparse.ArgumentParser();p.add_argument("--upstream",type=Path,required=True)
    p.add_argument("--output",type=Path);a=p.parse_args();result=check(a.upstream)
    text=json.dumps(result,indent=2);print(text)
    if a.output:a.output.write_text(text+"\n")
    raise SystemExit(0 if result["ready"] else 2)
if __name__=="__main__":main()
