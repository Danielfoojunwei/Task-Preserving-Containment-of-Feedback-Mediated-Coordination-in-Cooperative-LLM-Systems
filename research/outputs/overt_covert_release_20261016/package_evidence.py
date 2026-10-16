#!/usr/bin/env python3
"""Package released evidence with its exact frozen dependency closure.

No result reads, credential reads, archive creation or subprocesses at import.
Actual packaging requires --release. Tests supply synthetic temporary roots.
"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import tempfile
import zipfile

HERE=Path(__file__).resolve().parent
_binding_spec=importlib.util.spec_from_file_location("package_source_bindings",HERE/"source_bindings.py")
_binding_module=importlib.util.module_from_spec(_binding_spec);_binding_spec.loader.exec_module(_binding_module)
SourceBindings=_binding_module.SourceBindings
ROOT=HERE.parents[2]
PREFIX="overt-covert-evidence-20261016"
REL=Path("research/outputs")
MAIN="overt_covert_relaunch_20261016"
CONTINUATION="overt_covert_continuations_20261016"
TREES=("overt_covert_mechanisms_20261016","credential_transport_diagnostic_20261016",MAIN,"overt_covert_release_20261016")
OPTIONAL_FILES=("README.md","research/README.md","docs/VALIDATION.md","docs/SPRINT_CONTRIBUTIONS.md",
    "docs/SPRINT_RESEARCH_BRIEF.md","docs/UNIFIED_RESEARCH_FINDING.md","docs/RESEARCH_CONTRIBUTIONS.md",
    "docs/SPRINT_ALIGNMENT.md","docs/SPRINT_SUBMISSION_CHECKLIST.md","docs/SPRINT_TEMPLATE_MAP.md",
    "docs/SPRINT_ETHICS_REVIEW.md","docs/SPRINT_EXECUTION_PLAN.md",
    "docs/sprint_alignment_20261015/template/apart_submission_template.pdf",
    "docs/sprint_alignment_20261015/template/TEMPLATE_SOURCE.json",
    "docs/environment/STARTUP_EXTENSION_PROPOSAL_20261016.md",".github/workflows/research.yml")
OPTIONAL_TREES=("presentations/overt_covert_20261016",)
IGNORED={"__pycache__",".git",".pytest_cache",".mypy_cache",".ruff_cache",".venv","node_modules",".locks"}
PRIVATE={".env",".envrc","credentials","credentials.json","secrets.json","id_rsa","id_ed25519"}
PRIVATE_SUFFIX=(".pem",".key",".p12",".pfx",".keystore")
TRANSIENT_SUFFIX=(".pyc",".pyo",".partial",".lock",".pid",".zip",".bundle",".tar",".tgz",".gz")
KEY_PATTERN=re.compile(rb"(?:sk-or-v1-[A-Za-z0-9_-]{30,}|gh[pousr]_[A-Za-z0-9]{30,})")

README='''# Portable overt/covert study evidence

This package preserves the completed main study, the earlier halted attempt,
neutral credential diagnostics, literature and review artifacts, the release
tools and figures, any available continuation evidence, and every transitive
source/data dependency pinned by their freezes. Parent cohorts are included only
as needed by those frozen references. The original relative repository layout
is preserved. Earlier aborted or unrun cohorts are not successful experiments.

Updated central documentation, CI configuration and the new presentation tree
are copied when present. Their historical links may intentionally refer outside
this focused bundle. Pinned parent source files are dependencies, not complete
prior-study evidence. The earlier 3,996-call baseline has its own separate
standalone archive, `reciprocity-evidence-20261016-final.zip`; that archive and
its full prior cohort records are not silently included here. Nested archives
are excluded. Use the separate baseline bundle or full repository to follow
those historical evidence links.

`SOURCE_MANIFEST.json` records every included byte and frozen reference. SHA256
and local source mtimes provide reproducibility, not external attestation or a
public preregistration. Credentials, environment files, locks, caches, Git data
and nested archives are excluded; evidence bytes are never redacted or rewritten.

Use **CPython 3.12.14**, the original runtime, and install
`requirements-offline.txt` before entering an offline environment. Strict
numerical reproduction requires this runtime: the frozen bootstrap uses Python's
built-in floating-point `sum`, whose algorithm changed between Python 3.11 and
3.12 and can change the last bits of bootstrap summaries. This is not a claim of
exact reproduction across Python versions. Raw verifiers and numerical analyzers use the standard library;
the optional unit tests require jsonschema. No dependency installation or API
call is attempted by the reproduction helper. Figures can be viewed directly;
rebuilding them additionally requires Matplotlib and NumPy.

```sh
python verify_offline.py --release --output-dir /tmp/overt-covert-reproduction
```

The helper records and checks the Python implementation and version before
opening evidence, then verifies bundle bytes, runs bundled study unit tests, reconstructs
every main raw record, reproduces its frozen analysis to temporary output and
compares substantive JSON. Completed continuations receive the same checks.
`--skip-unit-tests` skips only the optional software tests, never the raw audit
or numerical reproduction. Child processes have credentials removed, socket
networking blocked, and bytecode writing disabled. No live runner is launched.
The runtime check is saved as `OFFLINE_RUNTIME_CHECK.json`, including on a runtime
mismatch. `--allow-other-python-3-12-patch` explicitly permits trying another
CPython 3.12 patch; all exact numeric comparisons still apply and agreement is
not guaranteed. Python 3.11, Python 3.13 and other implementations are rejected
even with that override. Independent exact-test verification under another
runtime is a separate, bounded check, not exact reproduction of frozen bootstrap
JSON. No numerical tolerance is introduced by this helper.

Each completed cohort also includes `SOURCE_BINDINGS.json` and its persisted
`SOURCE_SNAPSHOT_BEFORE_AUDIT.json`. The wrapper captured every calls/runs byte
before the passing frozen raw audit and required the exact inventory to remain
unchanged afterward. Packaging and offline verification check this inventory,
its raw report, frozen verifier and freeze hashes. Only the three declared
runtime lock basenames `.call.lock`, `.budget.lock` and `.scheduler.lock` are
excluded from that semantic source inventory. Unknown extra files remain bound.
The secondary review and
replay builders require the same binding, so a later coordinated edit to an
action report and its end-state copy cannot silently become evidence. These
local snapshots provide provenance, not external timestamp attestation.

The main verifier writes **INDEPENDENT_VERIFICATION_ALL.json**. The continuation
verifier writes **INDEPENDENT_VERIFICATION.json**. The archived continuation plan
continues to use its pinned archived main report; the helper first establishes
that the freshly reconstructed main report is substantively identical.

If the archived post-freeze independent primary check is present, its recorded
source hashes must match all six included inputs: verifier, plan, raw audit,
sealed reviews, analysis and source-binding validator. The helper then runs that
separate checker on the freshly
reconstructed raw audit and analysis and requires PASS. This independently
rechecks the primary metrics, exact tests, correction and unresolved-label policy;
it does not import the frozen analyzer. Its new provenance hashes and timestamp
need not equal the archived check, and are validated against the new inputs.

Only generated timestamps and top-level machine root paths are excluded when
comparing raw reports. The main analysis may differ in its review-file absolute
path. Continuation analysis provenance hashes can differ because the raw report
has a new timestamp/root; both hashes are checked against their respective raw
files and all substantive raw fields must match before that exception is used.
Outcome numbers, judgments, denominators, calls, assignments and source hashes
are not excluded. Logs and reproduced files remain outside this evidence tree.

Open `research/outputs/overt_covert_release_20261016/evidence_replay.html` when
included. Its receipt-cap checkbox is an offline calculation on fixed recorded
actions and the actual fine; it is not an additional experiment. Formation
labels do not prove covert execution, fines do not reimburse the owner, and the
context-removal branch does not isolate private memory. All work before the
October 23–25 sprint must be disclosed as prior work.
'''


def sha(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda:f.read(1024*1024),b""):h.update(block)
    return h.hexdigest()


def read(path):return json.loads(Path(path).read_text())


def excluded(path,root):
    parts=path.relative_to(root).parts;name=path.name.lower()
    return (any(p.lower() in IGNORED or p.lower() in PRIVATE or p.lower().startswith(".env.")
                or p.lower().endswith(PRIVATE_SUFFIX) for p in parts)
            or name.endswith(PRIVATE_SUFFIX+TRANSIENT_SUFFIX))


def safe_source(path,root):
    path=Path(path)
    if not path.resolve().is_relative_to(root):raise ValueError("frozen/source path escapes repository")
    if any(p.is_symlink() for p in (path,*path.parents) if p.is_relative_to(root)):
        raise ValueError("symlinks are not silently dereferenced")
    if excluded(path,root):raise ValueError("required dependency matches excluded/private file rules")
    if not path.is_file():raise ValueError("missing required source: "+str(path.relative_to(root)))
    return path.resolve()


def collect(root):
    root=Path(root).resolve();files=set();trees=[]
    names=list(TREES)
    if (root/REL/CONTINUATION).is_dir():names.append(CONTINUATION)
    for name in names:
        directory=root/REL/name
        if not directory.is_dir():raise ValueError("missing evidence tree: "+name)
        trees.append(directory)
        for path in directory.rglob("*"):
            if excluded(path,root):continue
            if path.is_symlink():raise ValueError("symlink in evidence tree")
            if path.is_file():files.add(safe_source(path,root))
    for name in OPTIONAL_FILES:
        path=root/name
        if path.exists() or path.is_symlink():files.add(safe_source(path,root))
    for name in OPTIONAL_TREES:
        directory=root/name
        if directory.is_symlink():raise ValueError("symlink in optional presentation tree")
        if not directory.is_dir():continue
        trees.append(directory)
        for path in directory.rglob("*"):
            if excluded(path,root):continue
            if path.is_symlink():raise ValueError("symlink in optional presentation tree")
            if path.is_file():files.add(safe_source(path,root))
    references=[];seen=set()
    queue=sorted(p for p in files if p.name=="FREEZE.json")
    while queue:
        frozen_path=queue.pop()
        if frozen_path in seen:continue
        seen.add(frozen_path);frozen=read(frozen_path)
        if not isinstance(frozen.get("sha256"),dict) or not frozen["sha256"]:
            raise ValueError("empty or invalid frozen dependency inventory")
        for name,expected in sorted(frozen["sha256"].items()):
            if Path(name).is_absolute():raise ValueError("absolute frozen dependency is not portable")
            source=safe_source(frozen_path.parent/name,root)
            if sha(source)!=expected:raise ValueError("frozen dependency bytes changed: "+str(source.relative_to(root)))
            files.add(source)
            references.append({"freeze_path":frozen_path.relative_to(root).as_posix(),"reference":name,
                "source_path":source.relative_to(root).as_posix(),"sha256":expected})
            if source.name=="FREEZE.json":queue.append(source)
    return sorted(files),sorted(references,key=lambda r:(r["freeze_path"],r["reference"])),trees


def signature(path):
    s=path.stat();return (s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns)


def archive_source(archive,path,relative,prefix,credential_literals=()):
    before=signature(path)
    info=zipfile.ZipInfo.from_file(path,prefix+"/"+relative);info.compress_type=zipfile.ZIP_DEFLATED
    h=hashlib.sha256();size=0;tail=b""
    with path.open("rb") as source,archive.open(info,"w") as destination:
        for block in iter(lambda:source.read(1024*1024),b""):
            sample=tail+block
            if KEY_PATTERN.search(sample) or any(value in sample for value in credential_literals):
                raise ValueError("credential-shaped literal detected; source packaging refused: "+relative)
            tail=sample[-256:];destination.write(block);h.update(block);size+=len(block)
    if signature(path)!=before or size!=before[2]:raise ValueError("source changed during packaging")
    return {"sha256":h.hexdigest(),"size":size,"mtime_ns":before[3]},before


def repository_relative(root,path):
    resolved=safe_source(path,root)
    return resolved.relative_to(root).as_posix()


def build(destination,root=ROOT,prefix=PREFIX,*,main_reviews=None,main_verification=None,
          continuation_verification=None):
    root=Path(root).resolve();destination=Path(destination).resolve()
    if not re.fullmatch(r"[A-Za-z0-9._-]+",prefix) or prefix in (".",".."):
        raise ValueError("archive prefix must be one ordinary directory name")
    if destination.exists():raise FileExistsError("refusing to overwrite evidence archive")
    main=root/REL/MAIN
    reviews=Path(main_reviews) if main_reviews else main/"manual_reviews/SEALED_PRIMARY_REVIEWS.json"
    verification=Path(main_verification) if main_verification else main/"independent/final/INDEPENDENT_VERIFICATION_ALL.json"
    actual=read(verification);analysis=read(main/"ANALYSIS.json")
    if (actual.get("passed") is not True or actual.get("phase")!="all"
            or actual.get("inventory",{}).get("verified_calls")!=6608
            or analysis.get("inference_eligible") is not True):
        raise ValueError("complete released main analysis and full passing raw audit required")
    if analysis["review_release"]["sha256"]!=sha(reviews):raise ValueError("main analysis review seal changed")
    source_bindings=[SourceBindings(main,verification)]
    files,references,trees=collect(root)
    file_set=set(files)
    if any(destination==tree or destination.is_relative_to(tree) for tree in trees):
        raise ValueError("archive destination must be outside included evidence trees")
    if verification.resolve() not in file_set or reviews.resolve() not in file_set:
        raise ValueError("main verification and review seal must be within packaged evidence")
    primary=main/"independent/primary/INDEPENDENT_PRIMARY_VERIFICATION.json"
    primary_present=primary.is_file()
    if primary_present:
        result=read(primary)
        if result.get("passed") is not True or result.get("failures")!=[]:
            raise ValueError("archived independent primary check must pass")
        expected={"verifier":main/"independent_primary.py","plan":main/"plan.json",
            "raw_audit":verification,"sealed_reviews":reviews,"analysis":main/"ANALYSIS.json",
            "source_binding_validator":root/REL/"overt_covert_release_20261016/source_bindings.py"}
        if result.get("source_hashes")!={k:sha(path) for k,path in expected.items()}:
            raise ValueError("independent primary source hashes do not bind included inputs")
    continuation=root/REL/CONTINUATION;complete=False
    completion=continuation/"continuations_completion.json"
    if completion.is_file():complete=read(completion).get("complete") is True
    continuation_report=None
    if complete:
        continuation_report=Path(continuation_verification) if continuation_verification else continuation/"independent/final/INDEPENDENT_VERIFICATION.json"
        if read(continuation_report).get("passed") is not True or read(continuation/"ANALYSIS.json").get("complete") is not True:
            raise ValueError("completed continuation needs released analysis and passing raw audit")
        if read(continuation/"ANALYSIS.json")["independent_verification_sha256"]!=sha(continuation_report):
            raise ValueError("continuation analysis provenance does not match archived raw audit")
        if continuation_report.resolve() not in file_set:raise ValueError("continuation report not included")
        source_bindings.append(SourceBindings(continuation,continuation_report))
    for binding in source_bindings:
        if any(binding.root/name not in file_set for name in binding.manifest["artifacts"]):
            raise ValueError("an audited source artifact would be excluded from the portable package")
    generated={"verify_offline.py":(HERE/"verify_offline.py").read_bytes(),
        "source_bindings.py":(HERE/"source_bindings.py").read_bytes(),
        "README_REPRODUCE.md":README.encode(),"requirements-offline.txt":b"jsonschema==4.26.0\n"}
    destination.parent.mkdir(parents=True,exist_ok=True)
    temporary=tempfile.NamedTemporaryFile(prefix=destination.name+".",suffix=".partial",dir=destination.parent,delete=False)
    temporary.close();pending=Path(temporary.name)
    entries={};signatures={}
    # Exact configured values are compared in memory, never printed or written.
    credential_literals=tuple(v.encode() for k,v in os.environ.items()
        if k.upper().endswith(("_API_KEY","_TOKEN","_SECRET")) and len(v)>=16)
    try:
        with zipfile.ZipFile(pending,"w",zipfile.ZIP_DEFLATED,compresslevel=6) as archive:
            for path in files:
                name=path.relative_to(root).as_posix()
                entries[name],signatures[path]=archive_source(archive,path,name,prefix,credential_literals)
            helpers={}
            for name,blob in generated.items():
                archive.writestr(prefix+"/"+name,blob)
                helpers[name]={"size":len(blob),"sha256":hashlib.sha256(blob).hexdigest()}
            again,again_refs,_=collect(root)
            if again!=files or again_refs!=references or any(signature(p)!=s for p,s in signatures.items()):
                raise ValueError("evidence changed before archive completion")
            for binding in source_bindings:binding.verify_unchanged()
            manifest={"manifest_version":1,"files":entries,"generated_files":helpers,"freeze_references":references,
                "main_study":(REL/MAIN).as_posix(),"main_reviews":repository_relative(root,reviews),
                "main_verification":repository_relative(root,verification),
                "main_source_bindings":repository_relative(root,source_bindings[0].path),
                "main_primary_verification":repository_relative(root,primary) if primary_present else None,
                "continuation_study":(REL/CONTINUATION).as_posix() if continuation.is_dir() else None,
                "continuation_complete":complete,
                "continuation_verification":repository_relative(root,continuation_report) if complete else None,
                "continuation_source_bindings":repository_relative(root,source_bindings[1].path) if complete else None,
                "scope":"Full new evidence trees, available updated central documentation/CI/presentation files, and recursively pinned dependencies. Halted/diagnostic and incomplete continuation records are retained without interpreting them as completed experiments. Complete prior baseline evidence is a separate archive; historical links can point outside this focused bundle.",
                "excluded":"Credential/environment/key files, caches, locks, Git metadata and nested archives.",
                "temporal_limit":"Recorded bytes and local source mtimes are not external attestation.","api_calls":0}
            archive.writestr(prefix+"/SOURCE_MANIFEST.json",json.dumps(manifest,indent=2,sort_keys=True)+"\n")
        os.link(pending,destination)
    finally:pending.unlink(missing_ok=True)
    return {"archive":str(destination),"source_files":len(files),"freeze_references":len(references),
        "bytes":destination.stat().st_size,"sha256":sha(destination),"continuation_complete":complete,"api_calls":0}


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out",type=Path,required=True);parser.add_argument("--root",type=Path,default=ROOT)
    parser.add_argument("--prefix",default=PREFIX);parser.add_argument("--main-reviews",type=Path)
    parser.add_argument("--main-verification",type=Path);parser.add_argument("--continuation-verification",type=Path)
    parser.add_argument("--release",action="store_true")
    args=parser.parse_args(argv)
    if not args.release:parser.error("explicit numerical release required before actual packaging")
    print(json.dumps(build(args.out,args.root,args.prefix,main_reviews=args.main_reviews,
        main_verification=args.main_verification,continuation_verification=args.continuation_verification),indent=2,sort_keys=True))
    return 0


if __name__=="__main__":raise SystemExit(main())
