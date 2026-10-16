#!/usr/bin/env python3
"""Verify a portable bundle, audit raw records and reproduce released analyses.

No reads at import. Actual verification requires --release. All generated logs
and analyses stay outside the bundle. Child processes have credentials removed,
network sockets blocked, and bytecode writes disabled. No runner is launched.
"""
import argparse
from copy import deepcopy
import hashlib
import importlib.util
import json
import os
from pathlib import Path, PurePosixPath
import subprocess
import sys
import tempfile

REPRODUCTION_PYTHON=(3,12,14)
_binding_spec=importlib.util.spec_from_file_location("offline_source_bindings",Path(__file__).with_name("source_bindings.py"))
_binding_module=importlib.util.module_from_spec(_binding_spec);_binding_spec.loader.exec_module(_binding_module)
SourceBindings=_binding_module.SourceBindings


NETWORK_GUARD = '''"""Force all reproduction child processes to remain offline."""
import socket
def blocked(*args, **kwargs):
    raise RuntimeError("Network access is disabled for offline reproduction")
socket.socket.connect = blocked
socket.socket.connect_ex = blocked
socket.create_connection = blocked
socket.getaddrinfo = blocked
'''


def sha(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda:f.read(1024*1024),b""):h.update(block)
    return h.hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def checked_path(root, relative):
    p=PurePosixPath(relative)
    if p.is_absolute() or not p.parts or any(x in (".","..") for x in p.parts):
        raise ValueError("invalid bundle-relative path")
    root=Path(root).resolve();path=root.joinpath(*p.parts)
    if not path.resolve().is_relative_to(root) or not path.is_file():
        raise ValueError("missing or escaped bundle artifact: "+relative)
    if any(x.is_symlink() for x in (path,*path.parents) if x.is_relative_to(root)):
        raise ValueError("symlink in bundle artifact")
    return path


def verify_manifest(root):
    root=Path(root).resolve();manifest=read(root/"SOURCE_MANIFEST.json")
    entries=dict(manifest["files"])
    for name,entry in manifest.get("generated_files",{}).items():
        if name in entries:raise ValueError("duplicate manifest artifact")
        entries[name]=entry
    for name,entry in entries.items():
        path=checked_path(root,name)
        if path.stat().st_size!=entry["size"] or sha(path)!=entry["sha256"]:
            raise ValueError("bundle byte verification failed: "+name)
    for ref in manifest["freeze_references"]:
        path=checked_path(root,ref["source_path"])
        if sha(path)!=ref["sha256"]:raise ValueError("frozen dependency bytes changed")
    if not manifest.get("main_source_bindings"):
        raise ValueError("archived pre-audit source bindings are required")
    bindings=[SourceBindings(root/manifest["main_study"],checked_path(root,manifest["main_verification"]),
        checked_path(root,manifest["main_source_bindings"]))]
    if manifest.get("continuation_complete"):
        bindings.append(SourceBindings(root/manifest["continuation_study"],checked_path(root,manifest["continuation_verification"]),
            checked_path(root,manifest["continuation_source_bindings"])))
    manifest["validated_source_bindings"]=[binding.provenance() for binding in bindings]
    return manifest


def comparable(value, kind):
    """Exclude only declared non-substantive fields; preserve all outcome data."""
    result=deepcopy(value)
    ignored=[]
    if kind in ("main_raw","continuation_raw"):
        for key in ("generated_at","root"):
            if key in result:result.pop(key);ignored.append(key)
    elif kind=="main_analysis":
        if "path" in result.get("review_release",{}):
            result["review_release"].pop("path");ignored.append("review_release.path")
    elif kind=="continuation_analysis":
        if "independent_verification_sha256" in result:
            result.pop("independent_verification_sha256");ignored.append("independent_verification_sha256")
    else:raise ValueError("unknown comparison kind")
    return result,ignored


def compare_json(archived, reproduced, kind):
    a,ai=comparable(read(archived),kind);b,bi=comparable(read(reproduced),kind)
    if ai!=bi or a!=b:raise ValueError("substantive JSON differs: "+kind)
    encoded=json.dumps(a,sort_keys=True,separators=(",",":"),allow_nan=False).encode()
    return {"kind":kind,"substantive_equal":True,"ignored_fields":ai,
        "substantive_sha256":hashlib.sha256(encoded).hexdigest(),
        "archived_sha256":sha(archived),"reproduced_sha256":sha(reproduced)}


def command_plan(bundle, output, manifest, skip_unit_tests=False):
    bundle,output=Path(bundle).resolve(),Path(output).resolve()
    main=checked_path(bundle,manifest["main_study"]+"/independent_verify.py").parent
    reviews=checked_path(bundle,manifest["main_reviews"])
    python=sys.executable
    steps=[]
    if not skip_unit_tests:
        steps.append(("main_unit_tests",[python,"-m","unittest","discover","-s",str(main),"-p","test_*.py","-q"]))
    steps.extend([
        ("main_raw",[python,str(main/"independent_verify.py"),"--root",str(main),"--phase","all","--release","--output-dir",str(output/"main_raw")]),
        ("main_analysis",[python,str(main/"analyze.py"),"--root",str(main),"--sealed-reviews",str(reviews),"--release","--output",str(output/"main_analysis.json")])])
    if manifest.get("main_primary_verification"):
        primary=checked_path(bundle,manifest["main_study"]+"/independent_primary.py")
        steps.append(("main_primary",[python,str(primary),"--root",str(main),
            "--verified-rounds",str(output/"main_raw"/"INDEPENDENT_VERIFICATION_ALL.json"),
            "--sealed-reviews",str(reviews),"--analysis",str(output/"main_analysis.json"),
            "--output",str(output/"main_primary"/"INDEPENDENT_PRIMARY_VERIFICATION.json"),"--release"]))
    if manifest.get("continuation_complete"):
        continuation=checked_path(bundle,manifest["continuation_study"]+"/independent_verify.py").parent
        if not skip_unit_tests:
            steps.append(("continuation_unit_tests",[python,"-m","unittest","discover","-s",str(continuation),"-p","test_*.py","-q"]))
        steps.extend([
            ("continuation_raw",[python,str(continuation/"independent_verify.py"),"--root",str(continuation),"--release","--output-dir",str(output/"continuation_raw")]),
            ("continuation_analysis",[python,str(continuation/"analyze.py"),"--verification",str(output/"continuation_raw"/"INDEPENDENT_VERIFICATION.json"),"--release","--output",str(output/"continuation_analysis.json")])])
    return steps


def child_environment(output):
    guard=Path(output)/"network_guard";guard.mkdir(parents=True,exist_ok=True)
    (guard/"sitecustomize.py").write_text(NETWORK_GUARD)
    env=os.environ.copy()
    removed=[]
    for key in list(env):
        upper=key.upper()
        if upper.endswith(("_API_KEY","_TOKEN","_SECRET","_PASSWORD")) or upper in ("GH_TOKEN","GITHUB_TOKEN","OPENROUTER_API_KEY"):
            env.pop(key);removed.append(key)
    env["PYTHONPATH"]=str(guard)+(os.pathsep+env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    env["PYTHONDONTWRITEBYTECODE"]="1"
    return env,sorted(removed)


def validate_primary_check(report_path,verifier_path,plan_path,raw_path,reviews_path,analysis_path,
                           source_binding_validator_path):
    report=read(report_path)
    expected={"verifier":sha(verifier_path),"plan":sha(plan_path),"raw_audit":sha(raw_path),
        "sealed_reviews":sha(reviews_path),"analysis":sha(analysis_path),
        "source_binding_validator":sha(source_binding_validator_path)}
    if report.get("passed") is not True or report.get("failures")!=[]:
        raise ValueError("independent primary verification did not pass")
    if report.get("source_hashes")!=expected:
        raise ValueError("independent primary verification input hashes differ")
    return {"passed":True,"report_sha256":sha(report_path),"source_hashes":expected}


def runtime_check(allow_other_python_3_12_patch=False):
    """Qualify exact floating-point reproduction before opening any evidence."""
    version=tuple(sys.version_info[:3]);implementation=sys.implementation.name
    final=tuple(sys.version_info[3:])==("final",0)
    exact=implementation=="cpython" and version==REPRODUCTION_PYTHON and final
    override=(allow_other_python_3_12_patch and implementation=="cpython"
              and version[:2]==REPRODUCTION_PYTHON[:2] and final and not exact)
    return {"passed":bool(exact or override),"required_implementation":"cpython",
        "required_python_version":"3.12.14","observed_implementation":implementation,
        "observed_python_version":".".join(map(str,version)),"observed_runtime":sys.version,
        "observed_release_level":list(sys.version_info[3:]),
        "exact_runtime_match":exact,"other_3_12_patch_explicitly_allowed":bool(override),
        "numeric_comparisons_relaxed":False,
        "qualification":"The frozen bootstrap uses built-in floating-point sum. Python 3.11 and 3.12 can differ in final bits. Strict numerical reproduction requires the original CPython 3.12.14 runtime. An explicit other-3.12-patch override still requires unchanged exact JSON comparisons and does not guarantee agreement."}


def reproduce(bundle, output=None, skip_unit_tests=False, allow_other_python_3_12_patch=False):
    bundle=Path(bundle).resolve()
    output=Path(output or tempfile.mkdtemp(prefix="overt-covert-offline-")).resolve()
    if output==bundle or output.is_relative_to(bundle):
        raise ValueError("reproduction outputs must be outside the evidence bundle")
    output.mkdir(parents=True,exist_ok=True)
    runtime=runtime_check(allow_other_python_3_12_patch)
    (output/"OFFLINE_RUNTIME_CHECK.json").write_text(json.dumps(runtime,indent=2,sort_keys=True)+"\n")
    if not runtime["passed"]:
        raise ValueError("strict reproduction requires CPython 3.12.14; observed "
            +runtime["observed_implementation"]+" "+runtime["observed_python_version"]
            +". Runtime check recorded in "+str(output/"OFFLINE_RUNTIME_CHECK.json")
            +". Only another CPython 3.12 patch may be tried with --allow-other-python-3-12-patch; exact numeric comparisons remain mandatory.")
    manifest=verify_manifest(bundle)
    env,removed=child_environment(output)
    comparisons=[];steps=[];primary_checks=[]
    archived_main_raw=checked_path(bundle,manifest["main_verification"])
    archived_main_analysis=checked_path(bundle,manifest["main_study"]+"/ANALYSIS.json")
    if manifest.get("main_primary_verification"):
        source_binding_validator=checked_path(bundle,(PurePosixPath(manifest["main_study"]).parent
            /"overt_covert_release_20261016"/"source_bindings.py").as_posix())
        primary_checks.append({"scope":"archived",**validate_primary_check(
            checked_path(bundle,manifest["main_primary_verification"]),
            checked_path(bundle,manifest["main_study"]+"/independent_primary.py"),
            checked_path(bundle,manifest["main_study"]+"/plan.json"),archived_main_raw,
            checked_path(bundle,manifest["main_reviews"]),archived_main_analysis,
            source_binding_validator)})
    for name,command in command_plan(bundle,output,manifest,skip_unit_tests):
        result=subprocess.run(command,cwd=bundle,env=env,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
        log=output/(name+".log");log.write_text(result.stdout)
        steps.append({"name":name,"returncode":result.returncode,"log":str(log),"command":command})
        if result.returncode:break
        if name=="main_raw":
            # The frozen main CLI writes the suffixed name. It must not be
            # confused with the continuation checker's unsuffixed output.
            produced=output/"main_raw"/"INDEPENDENT_VERIFICATION_ALL.json"
            comparisons.append(compare_json(archived_main_raw,produced,"main_raw"))
        elif name=="main_analysis":
            comparisons.append(compare_json(archived_main_analysis,output/"main_analysis.json","main_analysis"))
        elif name=="main_primary":
            primary_checks.append({"scope":"freshly reproduced",**validate_primary_check(
                output/"main_primary"/"INDEPENDENT_PRIMARY_VERIFICATION.json",
                checked_path(bundle,manifest["main_study"]+"/independent_primary.py"),
                checked_path(bundle,manifest["main_study"]+"/plan.json"),
                output/"main_raw"/"INDEPENDENT_VERIFICATION_ALL.json",
                checked_path(bundle,manifest["main_reviews"]),output/"main_analysis.json",
                source_binding_validator)})
        elif name=="continuation_raw":
            archived=checked_path(bundle,manifest["continuation_verification"])
            produced=output/"continuation_raw"/"INDEPENDENT_VERIFICATION.json"
            comparisons.append(compare_json(archived,produced,"continuation_raw"))
        elif name=="continuation_analysis":
            archived=checked_path(bundle,manifest["continuation_study"]+"/ANALYSIS.json")
            prior_raw=checked_path(bundle,manifest["continuation_verification"])
            fresh_raw=output/"continuation_raw"/"INDEPENDENT_VERIFICATION.json"
            fresh=output/"continuation_analysis.json"
            if read(archived)["independent_verification_sha256"]!=sha(prior_raw) or read(fresh)["independent_verification_sha256"]!=sha(fresh_raw):
                raise ValueError("continuation analysis provenance hash does not bind its raw audit")
            comparisons.append(compare_json(archived,fresh,"continuation_analysis"))
    planned=command_plan(bundle,output,manifest,skip_unit_tests)
    passed=len(steps)==len(planned) and all(s["returncode"]==0 for s in steps)
    report={"passed":passed,"runtime":runtime,"steps":steps,"comparisons":comparisons,"independent_primary_checks":primary_checks,"output_dir":str(output),
        "archived_source_bindings":manifest["validated_source_bindings"],
        "source_files_verified":len(manifest["files"]),"unit_tests_skipped":skip_unit_tests,
        "credential_variable_names_removed":removed,"network_blocked":True,"runners_launched":False,
        "scope":"Full raw-audit and numerical-analysis reproduction. Only declared path/time/provenance exceptions are excluded after substantive raw-report equality. No API credentials or network required."}
    (output/"OFFLINE_REPRODUCTION.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    return report


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle-root",type=Path,default=Path(__file__).resolve().parent)
    parser.add_argument("--output-dir",type=Path)
    parser.add_argument("--skip-unit-tests",action="store_true")
    parser.add_argument("--allow-other-python-3-12-patch",action="store_true",
        help="Explicitly try a CPython 3.12 patch other than 3.12.14; exact comparisons are unchanged and agreement is not guaranteed")
    parser.add_argument("--release",action="store_true")
    args=parser.parse_args(argv)
    if not args.release:parser.error("explicit release is required before opening actual evidence")
    result=reproduce(args.bundle_root,args.output_dir,args.skip_unit_tests,args.allow_other_python_3_12_patch)
    print(json.dumps(result,indent=2,sort_keys=True))
    return 0 if result["passed"] else 1


if __name__=="__main__":raise SystemExit(main())
