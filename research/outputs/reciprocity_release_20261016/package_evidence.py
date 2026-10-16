#!/usr/bin/env python3
"""Package released new-study evidence and offline checks; never call an API.

Building is an explicit separate action. Importing this file neither reads the
study outcomes nor creates an archive. The manifest preserves source bytes and
local nanosecond mtimes; neither is external temporal attestation.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
import time
import zipfile


ROOT = Path(__file__).resolve().parents[3]
PREFIX = "reciprocity-evidence-20261016"
STUDIES = ("reciprocity_causal_20261016", "negotiation_causal_20261016", "negotiation_defense_20261016", "reciprocity_release_20261016")
EXTRA_TREES = (Path("presentations/reciprocity_20261016"),)
CLIENT = Path("research/outputs/controlplane_20261015/api_client.py")
IGNORED_PARTS = {"__pycache__", ".git", ".locks", ".pytest_cache", ".mypy_cache", ".ruff_cache", ".venv", "node_modules"}
PRIVATE_NAMES = {".env", ".envrc", "credentials", "credentials.json", "secrets.json", "id_rsa", "id_ed25519"}
PRIVATE_SUFFIXES = (".key", ".pem", ".p12", ".pfx", ".keystore")
TRANSIENT_SUFFIXES = (".pyc", ".pyo", ".partial", ".lock", ".pid", ".zip", ".bundle")
KEY_PATTERN = re.compile(rb"sk-or-v1-[A-Za-z0-9_-]{20,}")
CORE = ("FREEZE.json", "PROTOCOL.md", "RUNTIME_INTERFACE.md", "ANALYSIS_PLAN.md", "run_study.py", "analyze.py",
        "independent_verify.py", "test_runner.py", "test_analysis.py", "test_independent.py", "plan.json", "prompt_material.json")


RESTORE = r'''#!/usr/bin/env python3
"""Verify archived source bytes, then restore recorded local nanosecond mtimes.

These times are local evidence, not external attestation or public registration.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath


def checked_path(root, name):
    relative = PurePosixPath(name)
    if relative.is_absolute() or not relative.parts or any(p in (".", "..") for p in relative.parts):
        raise SystemExit("Invalid manifest path: " + name)
    path = root.joinpath(*relative.parts)
    if any(p.is_symlink() for p in (path, *path.parents) if p != root.parent):
        raise SystemExit("Symlink in archived source path: " + name)
    resolved = path.resolve()
    if not resolved.is_relative_to(root) or not path.is_file():
        raise SystemExit("Missing or escaped archive path: " + name)
    return path


def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def verify(root, restore=True):
    root = Path(root).resolve()
    manifest = json.loads((root / "SOURCE_MANIFEST.json").read_text())
    entries = dict(manifest["files"])
    for name, entry in manifest.get("generated_files", {}).items():
        if name in entries:
            raise SystemExit("Duplicate source/generated path: " + name)
        entries[name] = entry
    paths = {}
    for name, entry in entries.items():
        path = checked_path(root, name)
        if path.stat().st_size != entry["size"] or digest(path) != entry["sha256"]:
            raise SystemExit("Byte verification failed: " + name)
        paths[name] = path
    # Verify every byte first. Never partially restore a known corrupt bundle.
    if restore:
        for name, path in paths.items():
            value = entries[name]["mtime_ns"]
            os.utime(path, ns=(value, value), follow_symlinks=False)
            if path.stat().st_mtime_ns != value:
                raise SystemExit("Filesystem did not preserve nanosecond mtime: " + name)
    for reference in manifest.get("freeze_references", []):
        path = checked_path(root, reference["source_path"])
        if digest(path) != reference["sha256"]:
            raise SystemExit("Frozen dependency verification failed: " + reference["source_path"])
    return {"source_files_verified": len(manifest["files"]), "generated_files_verified":len(manifest.get("generated_files",{})),
            "freeze_references_verified":len(manifest.get("freeze_references",[])),
            "recorded_local_mtimes_restored":restore, "api_calls":0,
            "limits":"Local bytes and timestamps are not external temporal attestation."}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify-only", action="store_true", help="Check bytes without restoring file times.")
    args = parser.parse_args()
    print(json.dumps(verify(Path(__file__).resolve().parent, not args.verify_only), sort_keys=True))
'''


VERIFY_OFFLINE = r'''#!/usr/bin/env python3
"""Run bundled offline tests and independent verifiers, with API key removed."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parent
    output = (args.output_dir or Path(tempfile.mkdtemp(prefix="reciprocity-offline-verification-"))).resolve()
    if output == root or root in output.parents:
        parser.error("Verification output must be outside the archived evidence directory")
    output.mkdir(parents=True, exist_ok=True)
    environment = os.environ.copy()
    environment.pop("OPENROUTER_API_KEY", None)
    commands = [
        [sys.executable, "restore_and_verify.py"],
        [sys.executable, "-m", "unittest", "discover", "-s", "research/outputs/reciprocity_causal_20261016", "-p", "test_*.py", "-q"],
        [sys.executable, "-m", "unittest", "discover", "-s", "research/outputs/negotiation_causal_20261016", "-p", "test_*.py", "-q"],
        [sys.executable, "-m", "unittest", "discover", "-s", "research/outputs/negotiation_defense_20261016", "-p", "test_*.py", "-q"],
        [sys.executable, "research/outputs/reciprocity_causal_20261016/independent_verify.py", "--phase", "all", "--output-dir", str(output / "main")],
        [sys.executable, "research/outputs/negotiation_causal_20261016/independent_verify.py", "--release", "--output-dir", str(output / "supplement"), "--parent-verification", str(output / "main" / "INDEPENDENT_VERIFICATION_ALL.json")],
        [sys.executable, "research/outputs/negotiation_defense_20261016/independent_verify.py", "--release", "--output-dir", str(output / "defense")],
    ]
    steps = []
    for index, command in enumerate(commands, 1):
        result = subprocess.run(command, cwd=root, env=environment, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        logfile = output / (str(index) + "_offline_check.log")
        logfile.write_text(result.stdout)
        steps.append({"command":command, "returncode":result.returncode, "log":str(logfile)})
        if result.returncode:
            break
    passed = len(steps) == len(commands) and all(step["returncode"] == 0 for step in steps)
    report = {"passed":passed,"steps":steps,"output_dir":str(output),"openrouter_key_removed":True,
              "scope":"Only bundled offline unit tests and independent verifier commands; no runner launch."}
    (output / "OFFLINE_PACKAGE_VERIFICATION.json").write_text(json.dumps(report,indent=2) + "\n")
    print(json.dumps(report,indent=2))
    raise SystemExit(0 if passed else 1)


if __name__ == "__main__":
    main()
'''


README = '''# Repeated-reciprocity evidence package

Start with `research/outputs/reciprocity_release_20261016/REPORT.md` when present,
and open the adjacent `evidence_replay.html` for recorded proposals, seven overt
pacts and settlement replay. This package contains all three complete new study
directories, the release directory, `presentations/reciprocity_20261016`, and the
unchanged borrowed transport dependency. It includes all raw
request/response and attempt records present in those directories, their frozen
protocols, local hash/time freezes, review records, analyses and independent
verifiers. Prior agreement-search nulls remain a distinct earlier release.

The main study's three causal contrasts use 16 randomized matched blocks. The
separately frozen negotiation supplement has eight fresh matched blocks and two
contrasts. Its directed-negotiation paragraph is an instruction bundle, not
spontaneous benign deployment. Assigned-pact controls are forced controls, not
independent formation. An automatic candidate is not a manually confirmed covert
agreement. See the released report, review scope and limitations for findings.

No API key or environment file is included. Packaging rejects files containing
an OpenRouter key-shaped literal and excludes credential/key/environment files,
caches, locks and Git metadata. It does not silently rewrite archived evidence.
Use Python 3.11+ and the installed dependency listed in `requirements-offline.txt`.
The optional visual rebuild also needs Matplotlib. Verifiers use the standard
library; runner unit tests import `jsonschema` and use fake transports.

ZIP timestamps lose nanoseconds. Before temporal consistency checks, verify all
archived bytes and restore their recorded **local** source mtimes:

```sh
python restore_and_verify.py
python verify_offline.py --output-dir /tmp/reciprocity-portable-verification
```

The second command runs the same byte check, all three folders' offline unit tests,
and all three independent raw-record verifiers. It removes `OPENROUTER_API_KEY` from
child-process environments, never launches a runner, writes verification outputs
outside the evidence folder, retains logs, and stops on any failure.

Individual commands, if preferred:

```sh
python -m unittest discover -s research/outputs/reciprocity_causal_20261016 -p 'test_*.py' -q
python -m unittest discover -s research/outputs/negotiation_causal_20261016 -p 'test_*.py' -q
python -m unittest discover -s research/outputs/negotiation_defense_20261016 -p 'test_*.py' -q
python research/outputs/reciprocity_causal_20261016/independent_verify.py --phase all --output-dir /tmp/reciprocity-independent
python research/outputs/negotiation_causal_20261016/independent_verify.py --release --output-dir /tmp/negotiation-independent --parent-verification /tmp/reciprocity-independent/INDEPENDENT_VERIFICATION_ALL.json
python research/outputs/negotiation_defense_20261016/independent_verify.py --release --output-dir /tmp/negotiation-defense-independent
```

To reconstruct numerical analyses without overwriting their archived release:

```sh
python research/outputs/reciprocity_causal_20261016/analyze.py --phase validation --output /tmp/reciprocity-analysis.json
python research/outputs/negotiation_causal_20261016/analyze.py --release --parent-analysis /tmp/reciprocity-analysis.json --output /tmp/negotiation-analysis.json
```

`SOURCE_MANIFEST.json` records the SHA-256, byte length and nanosecond mtime of
each source file, plus all references in all three `FREEZE.json` files. Generated
helpers are hashed separately. Historical absolute paths identify the original
workspace; imported dependencies retain their relative layout in this archive.
The archive's own SHA-256 is reported outside the archive. These checks do not
independently authenticate chronology, deleted/unrelated calls, or public
preregistration. Restoring file metadata is not external attestation.

All observations are prior work relative to the October 23–25, 2026 sprint and
must be disclosed accordingly. Documentation is AI-assisted research material,
not a claim of final team-authored submission prose. A receipt gate establishes
bounded excess-payment containment under trusted receipts and complete payment
path coverage; it does not establish the end of agreement, universal safety,
or guaranteed full reimbursement and future task performance.

The separate adaptive-defense study forks all eight directed supplemental
round-2 contexts without judge-label or profit selection, with two fresh cases
in each of three branches. It is descriptive and adds no p-values. Blocking
future notes preserves prior history; the disclosed gate changes enforcement
and information together. Historical-context links outside the included trees
need the full repository; this focused archive does not bundle older studies.
'''


def digest(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def excluded(path, root):
    relative = path.relative_to(root)
    name = path.name.lower()
    return (any(part in IGNORED_PARTS for part in relative.parts)
            or any(part.lower() in PRIVATE_NAMES or part.lower().startswith(".env.")
                   or part.lower().endswith(PRIVATE_SUFFIXES) for part in relative.parts)
            or name.endswith(PRIVATE_SUFFIXES + TRANSIENT_SUFFIXES))


def collect(root):
    root = Path(root).resolve()
    files = set()
    for name in STUDIES:
        directory = root / "research/outputs" / name
        if not directory.is_dir():
            raise ValueError("Missing packaged directory: " + name)
        if name != STUDIES[-1]:
            required_names = CORE if name != "negotiation_defense_20261016" else tuple(n for n in CORE if n not in ("ANALYSIS_PLAN.md", "test_analysis.py"))
            for required in required_names:
                if not (directory / required).is_file():
                    raise ValueError("Missing reproducibility source: " + str((directory / required).relative_to(root)))
        for path in directory.rglob("*"):
            if excluded(path, root):
                continue
            if path.is_symlink():
                raise ValueError("Symlinks are not silently dereferenced: " + str(path.relative_to(root)))
            if path.is_file():
                if not path.resolve().is_relative_to(root):
                    raise ValueError("Source path escaped the repository")
                files.add(path)
    for relative in EXTRA_TREES:
        directory=root/relative
        if not directory.is_dir():raise ValueError("Missing presentation tree: "+str(relative))
        for path in directory.rglob("*"):
            if excluded(path,root):continue
            if path.is_symlink():raise ValueError("Symlink in presentation tree")
            if path.is_file():files.add(path)
    if not (root / CLIENT).is_file() or (root / CLIENT).is_symlink():
        raise ValueError("Missing or symlinked borrowed transport dependency")
    files.add(root / CLIENT)
    return sorted(files)


def freeze_references(root, files):
    included = set(files)
    references = []
    for name in STUDIES[:-1]:
        frozen_path = root / "research/outputs" / name / "FREEZE.json"
        frozen = json.loads(frozen_path.read_text())
        if not isinstance(frozen.get("sha256"), dict) or not frozen["sha256"]:
            raise ValueError("Invalid empty freeze inventory: " + name)
        for relative, expected in sorted(frozen["sha256"].items()):
            source = (frozen_path.parent / relative).resolve()
            if source not in included or not source.is_relative_to(root):
                raise ValueError("Frozen dependency is absent from package: " + relative)
            if not isinstance(expected, str) or digest(source) != expected:
                raise ValueError("Frozen dependency changed: " + str(source.relative_to(root)))
            references.append({"freeze_path":str(frozen_path.relative_to(root)),
                               "reference":relative, "source_path":str(source.relative_to(root)), "sha256":expected})
    return references


def source_signature(path):
    status = path.stat()
    return status.st_dev, status.st_ino, status.st_size, status.st_mtime_ns, status.st_ctime_ns


def write_source(archive, path, relative, prefix):
    before = source_signature(path)
    info = zipfile.ZipInfo.from_file(path, prefix + "/" + relative)
    info.compress_type = zipfile.ZIP_DEFLATED
    h = hashlib.sha256()
    size = 0
    tail = b""
    with path.open("rb") as source, archive.open(info, "w") as target:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            if KEY_PATTERN.search(tail + chunk):
                raise ValueError("Credential-shaped literal detected; packaging refused for source: " + relative)
            tail = chunk[-128:]
            h.update(chunk)
            size += len(chunk)
            target.write(chunk)
    if source_signature(path) != before or size != before[2]:
        raise ValueError("Source changed while packaging: " + relative)
    return {"size":size, "sha256":h.hexdigest(), "mtime_ns":before[3]}, before


def git_head(root):
    result = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, text=True,
                            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    value = result.stdout.strip()
    return value if result.returncode == 0 and re.fullmatch(r"[a-f0-9]{40,64}", value) else None


def build(destination, root=ROOT, prefix=PREFIX):
    root = Path(root).resolve()
    destination = Path(destination).resolve()
    if not re.fullmatch(r"[A-Za-z0-9._-]+", prefix) or prefix in (".", ".."):
        raise ValueError("Archive prefix must be a single ordinary directory name")
    for relative in (*[Path("research/outputs")/name for name in STUDIES],*EXTRA_TREES):
        directory = root / relative
        if destination == directory or directory in destination.parents:
            raise ValueError("Write the archive outside all included study/release directories")
    if destination.exists():
        raise FileExistsError("Refusing to overwrite an existing evidence archive")
    files = collect(root)
    references = freeze_references(root, files)
    commit = git_head(root)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = tempfile.NamedTemporaryFile(prefix=destination.name + ".", suffix=".partial", dir=destination.parent, delete=False)
    temporary.close()
    temporary_path = Path(temporary.name)
    manifest_files, signatures = {}, {}
    generated_time = time.time_ns()
    generated = {"restore_and_verify.py":RESTORE, "verify_offline.py":VERIFY_OFFLINE,
                 "README_REPRODUCE.md":README, "requirements-offline.txt":"jsonschema==4.26.0\n"}
    try:
        with zipfile.ZipFile(temporary_path, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
            for path in files:
                relative = str(path.relative_to(root))
                manifest_files[relative], signatures[path] = write_source(archive, path, relative, prefix)
            generated_manifest = {}
            for name, content in generated.items():
                data = content.encode()
                archive.writestr(prefix + "/" + name, data)
                generated_manifest[name] = {"size":len(data), "sha256":hashlib.sha256(data).hexdigest(), "mtime_ns":generated_time}
            if freeze_references(root, files) != references:
                raise ValueError("Freeze inventory changed while packaging")
            for path, expected in signatures.items():
                if source_signature(path) != expected:
                    raise ValueError("Source changed before package completion: " + str(path.relative_to(root)))
            manifest = {"manifest_version":2, "git_head_at_packaging":commit, "files":manifest_files,
                        "generated_files":generated_manifest, "freeze_references":references,
                        "scope":"Three new study trees, release tree, presentation tree, and immutable borrowed transport; all present raw records retained. Historical-context links require the full repository.",
                        "excluded":"Environment/credential/key files, Python caches, lock/partial files, nested archives and Git metadata.",
                        "temporal_limit":"Recorded source mtimes and local hash freezes are not external attestation.",
                        "api_calls_during_packaging":0}
            archive.writestr(prefix + "/SOURCE_MANIFEST.json", json.dumps(manifest, indent=2, sort_keys=True) + "\n")
        # An exclusive hard link makes publication atomic without overwriting an
        # archive created concurrently. The temporary file is on this filesystem.
        os.link(temporary_path, destination)
    finally:
        temporary_path.unlink(missing_ok=True)
    return {"archive":str(destination), "prefix":prefix, "source_files":len(files),
            "generated_files":len(generated), "freeze_references":len(references),
            "bytes":destination.stat().st_size, "sha256":digest(destination), "git_head":commit,
            "api_calls":0}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--root", type=Path, default=ROOT, help="Repository root; useful for isolated synthetic fixture tests.")
    parser.add_argument("--prefix", default=PREFIX)
    args = parser.parse_args()
    print(json.dumps(build(args.out, args.root, args.prefix), indent=2, sort_keys=True))
