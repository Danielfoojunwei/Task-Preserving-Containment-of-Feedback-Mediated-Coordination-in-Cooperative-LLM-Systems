#!/usr/bin/env python3
"""Package only this extension and its verified freeze dependency closure.

Standard-library-only export and offline reproduction. No study runner is ever
called in live mode. Existing study artifacts and releases are never overwritten.
"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import zipfile

EXTENSION = Path("research/outputs/covert_extension_20261016")
MANIFEST = "EXPORT_MANIFEST.json"
LOCKS = {".call.lock", ".budget.lock", ".scheduler.lock"}
SCRIPT = EXTENSION / "release/package_extension.py"
CREDENTIAL_NAMES = {".env", ".aws", ".azure", ".config", ".git", ".codex", ".agents",
    "credentials", "credentials.json", "service-account.json", "id_rsa", "id_ed25519"}
SECRET_PATTERNS = (
    re.compile(rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(rb"\bsk-(?:or-v1-)?[A-Za-z0-9_-]{32,}\b"),
    re.compile(rb"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b"),
)


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load(path):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError("duplicate JSON key: " + key)
            result[key] = value
        return result
    return json.loads(Path(path).read_text(encoding="utf-8"), object_pairs_hook=pairs)


def write_new(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, sort_keys=True, indent=2, allow_nan=False)
        stream.write("\n")


def excluded(path):
    return ("__pycache__" in path.parts or path.suffix == ".pyc" or
            path.name in LOCKS or path.name.endswith(".lock"))


def check_export_content(relative, data):
    if any(part.lower() in CREDENTIAL_NAMES for part in Path(relative).parts):
        raise ValueError("credential or private metadata path cannot be exported: " + relative)
    if any(pattern.search(data) for pattern in SECRET_PATTERNS):
        raise ValueError("possible credential material cannot be exported: " + relative)


def checked_path(root, relative):
    """Allow freeze ../ references only when their normalized path stays in root."""
    root = Path(root).resolve()
    relative = Path(relative)
    if relative.is_absolute():
        raise ValueError("absolute source path")
    target = root / relative
    # Check each lexical component too: resolve() alone would hide symlinks.
    cursor = root
    for part in relative.parts:
        cursor = cursor / part
        if cursor.is_symlink():
            raise ValueError("source symlink: " + str(relative))
    target = target.resolve()
    if not target.is_relative_to(root) or not target.is_file():
        raise ValueError("source missing or escaped repository: " + str(relative))
    return target


def freeze_closure(repo):
    repo = Path(repo).resolve()
    queue = [repo / EXTENSION / name / "FREEZE.json" for name in ("formation", "clarification")]
    visited, pinned = set(), {}
    while queue:
        freeze = queue.pop()
        if freeze in visited:
            continue
        visited.add(freeze)
        frozen = load(checked_path(repo, freeze.relative_to(repo)))
        for name, wanted in frozen["sha256"].items():
            if not re.fullmatch(r"[0-9a-f]{64}", wanted):
                raise ValueError("invalid pinned SHA256")
            path = checked_path(repo, freeze.parent.relative_to(repo) / name)
            relative = path.relative_to(repo).as_posix()
            if relative in pinned and pinned[relative] != wanted:
                raise ValueError("conflicting freeze hashes: " + relative)
            if sha(path) != wanted:
                raise ValueError("frozen source changed: " + relative)
            pinned[relative] = wanted
            if path.name == "FREEZE.json":
                queue.append(path)
    return dict(sorted(pinned.items()))


def inventory(repo):
    repo = Path(repo).resolve()
    extension = repo / EXTENSION
    pinned = freeze_closure(repo)
    paths = set(pinned)
    for path in extension.rglob("*"):
        if path.is_symlink():
            raise ValueError("extension symlink: " + str(path))
        if path.is_file() and not excluded(path.relative_to(extension)):
            paths.add(path.relative_to(repo).as_posix())
    files = {}
    for relative in sorted(paths):
        path = checked_path(repo, relative)
        if excluded(Path(relative)):
            raise ValueError("excluded file was pinned: " + relative)
        check_export_content(relative, path.read_bytes())
        files[relative] = {"sha256": sha(path), "bytes": path.stat().st_size}
    return {"schema_version": 1, "extension": EXTENSION.as_posix(),
        "scope": "Whole extension, excluding bytecode and locks, plus transitive freeze SHA256 closure only.",
        "pinned": pinned, "files": files,
        "prior_audit_scope": "Pinned prior-liability inventory and completion certificate; prior raw-call cohorts are in the earlier bundle."}


def archive_name(name):
    relative = PurePosixPath(name)
    if (not name or "\\" in name or relative.is_absolute() or
            any(part in ("", ".", "..") for part in name.split("/")) or
            relative.as_posix() != name or ":" in relative.parts[0]):
        raise ValueError("unsafe ZIP member: " + name)
    return relative


def safe_extract(archive, target):
    target = Path(target)
    target.mkdir(parents=True, exist_ok=False)
    with zipfile.ZipFile(archive) as bundle:
        names = bundle.namelist()
        if len(names) != len(set(names)):
            raise ValueError("duplicate ZIP member")
        for entry in bundle.infolist():
            archive_name(entry.filename)
            mode = entry.external_attr >> 16
            if entry.is_dir() or stat.S_ISLNK(mode) or (mode and not stat.S_ISREG(mode)):
                raise ValueError("ZIP contains a non-regular file")
            path = target / entry.filename
            if not path.resolve().is_relative_to(target.resolve()):
                raise ValueError("ZIP path escaped extraction root")
            path.parent.mkdir(parents=True, exist_ok=True)
            with bundle.open(entry) as source, path.open("xb") as destination:
                shutil.copyfileobj(source, destination)
    manifest = load(target / MANIFEST)
    expected = set(manifest["files"]) | {MANIFEST}
    actual = {p.relative_to(target).as_posix() for p in target.rglob("*") if p.is_file()}
    if actual != expected:
        raise ValueError("ZIP member set differs from manifest")
    verify_manifest(target)


def verify_manifest(repo, require_exact=False):
    repo = Path(repo).resolve()
    manifest = load(repo / MANIFEST)
    if require_exact:
        actual = set()
        for path in repo.rglob("*"):
            if path.is_symlink():
                raise ValueError("unmanifested extraction symlink")
            if path.is_file():
                actual.add(path.relative_to(repo).as_posix())
        if actual != set(manifest["files"]) | {MANIFEST}:
            raise ValueError("fresh extraction contains missing or unmanifested files")
    for relative, wanted in manifest["files"].items():
        archive_name(relative)
        path = checked_path(repo, relative)
        if sha(path) != wanted["sha256"] or path.stat().st_size != wanted["bytes"]:
            raise ValueError("export source changed: " + relative)
    if freeze_closure(repo) != manifest["pinned"]:
        raise ValueError("freeze closure differs from export manifest")
    return manifest


GUARD = r'''import os, sys, socket
from pathlib import Path
root = Path(os.environ["COVERT_EXTRACTED_ROOT"]).resolve()
forbidden = os.environ.get("COVERT_FORBIDDEN_SOURCE_ROOT")
forbidden = Path(forbidden).resolve() if forbidden else None
def blocked(*args, **kwargs):
    raise RuntimeError("Network disabled for offline reproduction")
socket.socket.connect = blocked
socket.socket.connect_ex = blocked
socket.socket.sendto = blocked
socket.socketpair = blocked
socket.create_connection = blocked
socket.getaddrinfo = blocked
def audit(event, args):
    if event.startswith("socket."):
        raise RuntimeError("Network disabled for offline reproduction")
    if event == "open" and args and isinstance(args[0], (str, bytes)):
        path = Path(os.fsdecode(args[0])).resolve()
        if forbidden and path.is_relative_to(forbidden):
            raise RuntimeError("Original source filesystem is forbidden")
sys.addaudithook(audit)
assert all(not forbidden or not Path(p or os.getcwd()).resolve().is_relative_to(forbidden) for p in sys.path)
sys._covert_offline_guard = True
'''


def reproduce(repo, output, forbidden=None):
    """Launch a credential-free process with socket and original-source guards."""
    repo, output = Path(repo).resolve(), Path(output).resolve()
    if output.exists():
        raise FileExistsError("reproduction output must be new")
    if not output.is_relative_to(repo):
        raise ValueError("reproduction output must stay in the fresh extraction")
    verify_manifest(repo, require_exact=True)
    output.mkdir(parents=True)
    guard = output / "guard"
    guard.mkdir()
    (guard / "sitecustomize.py").write_text(GUARD, encoding="utf-8")
    empty_home = output / "empty_home"
    empty_home.mkdir()
    temporary = output / "tmp"
    temporary.mkdir()
    # An allowlist removes all provider keys, cloud credentials, identity and proxy
    # headers, inherited PYTHONPATH, and credential-file selectors without reading them.
    env = {key: os.environ[key] for key in ("PATH", "LANG", "LC_ALL", "TZ") if key in os.environ}
    env.update(HOME=str(empty_home), TMPDIR=str(temporary), PYTHONPATH=str(guard),
        PYTHONNOUSERSITE="1", PYTHONDONTWRITEBYTECODE="1", COVERT_EXTRACTED_ROOT=str(repo))
    if forbidden:
        forbidden = Path(forbidden).resolve()
        if repo.is_relative_to(forbidden) or forbidden.is_relative_to(repo):
            raise ValueError("original and extracted roots overlap")
        env["COVERT_FORBIDDEN_SOURCE_ROOT"] = str(forbidden)
    command = [sys.executable, str(repo / SCRIPT), "_worker", "--repo-root", str(repo), "--output-dir", str(output)]
    result = subprocess.run(command, cwd=repo, env=env, text=True, capture_output=True)
    (output / "worker.stdout.log").write_text(result.stdout, encoding="utf-8")
    (output / "worker.stderr.log").write_text(result.stderr, encoding="utf-8")
    if result.returncode:
        raise RuntimeError("offline reproduction failed; see " + str(output / "worker.stderr.log"))
    return load(output / "OFFLINE_VERIFICATION.json")


def module(repo, relative, name):
    path = checked_path(repo, relative)
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    if not Path(result.__file__).resolve().is_relative_to(repo):
        raise ValueError("module escaped extracted repository")
    return result


def worker(repo, output):
    repo, output = Path(repo).resolve(), Path(output).resolve()
    if getattr(sys, "_covert_offline_guard", False) is not True:
        raise RuntimeError("credential/network isolation guard was not loaded")
    if Path(__file__).resolve() != repo / SCRIPT:
        raise ValueError("reproduction script must come from extraction")
    before = verify_manifest(repo)
    extension = repo / EXTENSION
    formation, clarification = extension / "formation", extension / "clarification"
    checks = {}
    def run(name, arguments, count=None):
        command = [sys.executable] + [str(x) for x in arguments]
        result = subprocess.run(command, cwd=repo, text=True, capture_output=True)
        (output / (name + ".stdout.log")).write_text(result.stdout, encoding="utf-8")
        (output / (name + ".stderr.log")).write_text(result.stderr, encoding="utf-8")
        if result.returncode:
            raise RuntimeError(name + " failed: " + result.stderr[-4000:])
        checks[name] = {"passed": True}
        if count is not None:
            match = re.search(r"Ran (\d+) tests?", result.stderr)
            if not match or int(match[1]) != count:
                raise ValueError(name + " test count differs")
            checks[name]["tests"] = count
    run("formation_tests", ["-m", "unittest", "discover", "-s", formation, "-p", "test_*.py"], 149)
    run("clarification_tests", ["-m", "unittest", "discover", "-s", clarification, "-p", "test_*.py"], 25)
    run("secondary_v2_tests", ["-m", "unittest", "discover", "-s", extension / "release", "-p", "test_secondary_v2.py"])
    run("clarification_review_checks", [clarification / "merge_clarification_reviews.py", "--check", "--self-test"])
    f = module(repo, EXTENSION / "formation/run_study.py", "offline_formation")
    c = module(repo, EXTENSION / "clarification/run_clarification.py", "offline_clarification")
    for imported in (f, f.parent, c, c.parent, c.formation):
        if not Path(imported.__file__).resolve().is_relative_to(repo):
            raise ValueError("inherited source escaped extracted repository")
    for dependency in (f.PARENT_DIR, c.ORIGINAL, c.FORMATION):
        if not Path(dependency).resolve().is_relative_to(repo):
            raise ValueError("dependency root escaped extracted repository")
    f.verify_freeze(formation)
    c.verify_freeze(clarification)
    checks["source_freezes"] = {"passed": True, "pinned_paths": len(before["pinned"])}
    fresh_audit = formation / "independent/offline_reproduction_all"
    run("independent_raw_all", [formation / "independent_verify.py", "--root", formation,
        "--phase", "all", "--output-dir", fresh_audit, "--release"])
    audit = load(fresh_audit / "INDEPENDENT_VERIFICATION_ALL.json")
    if not audit["passed"] or not audit["before_after_equal"] or audit["inventory"]["verified_calls"] != 1430:
        raise ValueError("fresh independent raw audit failed")
    checks["independent_raw_all"]["verified_calls"] = 1430
    raw = c.self_check(clarification)
    if raw != load(clarification / "RAW_SELF_CHECK.json") or not raw["pass"] or raw["calls_checked"] != 64:
        raise ValueError("clarification raw self-check differs")
    write_new(output / "CLARIFICATION_RAW_SELF_CHECK.json", raw)
    checks["clarification_raw"] = {"passed": True, "verified_calls": 64, "full_record_equal": True}
    # The existing audit is itself source-bound and verified above. Reusing its
    # immutable provenance links permits exact comparison with no ignored leaves.
    analysis = output / "ANALYSIS.json"
    primary = formation / "manual_reviews/SEALED_PRIMARY_REVIEWS.json"
    original_audit = formation / "independent/all/INDEPENDENT_VERIFICATION_ALL.json"
    run("primary_analysis", [formation / "analyze.py", "--root", formation,
        "--sealed-reviews", primary, "--verification", original_audit,
        "--output", analysis, "--release"])
    if load(analysis) != load(formation / "ANALYSIS.json"):
        raise ValueError("primary analysis differs, including statistics, summaries or sessions")
    checks["primary_analysis"].update(full_record_equal=True, ignored_fields=[])
    secondary = output / "SECONDARY_EXECUTION.json"
    run("secondary_merge", [extension / "release/secondary_execution_v2.py", "--merge",
        "--root", formation, "--primary-reviews", primary, "--verification", original_audit,
        "--analysis", formation / "ANALYSIS.json", "--output", secondary, "--release"])
    if load(secondary) != load(formation / "SECONDARY_EXECUTION.json"):
        raise ValueError("secondary data differ")
    checks["secondary_merge"].update(full_record_equal=True, ignored_fields=[])
    run("independent_results_self_test", [extension / "release/independent_results_check.py", "--self-test"])
    checker_out = output / "independent_results"
    run("independent_results", [extension / "release/independent_results_check.py", "--root", formation,
        "--output-dir", checker_out, "--release"])
    independent = load(checker_out / "INDEPENDENT_RESULTS_CHECK.json")
    original = load(extension / "release/INDEPENDENT_RESULTS_CHECK.json")
    for record in (independent, original):
        record.pop("created_at_utc")
    if independent != original or not independent["passed"]:
        raise ValueError("independent scientific reconstruction differs")
    checks["independent_results"].update(full_record_equal_except_timestamp=True)
    verify_manifest(repo)
    result = {"schema_version": 1, "passed": True, "network_blocked": True,
        "provider_environment_removed": True, "original_source_root_forbidden": bool(os.environ.get("COVERT_FORBIDDEN_SOURCE_ROOT")),
        "all_manifest_sources_unchanged": True, "source_files": len(before["files"]), "checks": checks,
        "scope": "New extension reproduced from extracted files only. Prior aggregate closure uses the pinned inventory, not old raw-call cost reconstruction."}
    write_new(output / "OFFLINE_VERIFICATION.json", result)
    return result


def build(repo, archive):
    repo, archive = Path(repo).resolve(), Path(archive).resolve()
    receipt_path = archive.with_suffix(archive.suffix + ".receipt.json")
    checksum_path = archive.with_suffix(archive.suffix + ".sha256")
    evidence = archive.with_suffix(archive.suffix + ".offline-verification")
    if any(path.exists() or path.is_symlink() for path in (archive, receipt_path, checksum_path, evidence)):
        raise FileExistsError("archive, receipt, checksum and evidence paths must all be new")
    manifest = inventory(repo)
    archive.parent.mkdir(parents=True, exist_ok=True)
    try:
        with zipfile.ZipFile(archive, "x", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as bundle:
            for relative, wanted in manifest["files"].items():
                path = checked_path(repo, relative)
                data = path.read_bytes()
                if hashlib.sha256(data).hexdigest() != wanted["sha256"]:
                    raise ValueError("source changed during packaging: " + relative)
                entry = zipfile.ZipInfo(relative, date_time=(2026, 10, 16, 0, 0, 0))
                entry.external_attr = (stat.S_IFREG | 0o644) << 16
                entry.compress_type = zipfile.ZIP_DEFLATED
                bundle.writestr(entry, data, compresslevel=9)
            entry = zipfile.ZipInfo(MANIFEST, date_time=(2026, 10, 16, 0, 0, 0))
            entry.external_attr = (stat.S_IFREG | 0o644) << 16
            entry.compress_type = zipfile.ZIP_DEFLATED
            bundle.writestr(entry, json.dumps(manifest, sort_keys=True, indent=2) + "\n", compresslevel=9)
        if inventory(repo) != manifest:
            raise ValueError("source inventory changed during packaging")
        with tempfile.TemporaryDirectory(prefix="covert-extension-offline-") as temporary:
            extracted = Path(temporary) / "repository"
            safe_extract(archive, extracted)
            verification = reproduce(extracted, extracted / ".offline-reproduction", forbidden=repo)
            # Keep all fresh audit outputs and logs alongside the archive for review.
            if evidence.exists():
                raise FileExistsError("offline evidence directory must be new")
            shutil.copytree(extracted / ".offline-reproduction", evidence)
            shutil.copytree(extracted / EXTENSION / "formation/independent/offline_reproduction_all", evidence / "fresh_raw_audit")
        receipt = {"archive": archive.name, "bytes": archive.stat().st_size, "sha256": sha(archive),
            "members": len(manifest["files"]) + 1, "source_files": len(manifest["files"]),
            "pinned_paths": len(manifest["pinned"]), "uncompressed_source_bytes": sum(x["bytes"] for x in manifest["files"].values()),
            "fresh_extraction_offline_verification": verification, "evidence_directory": evidence.name}
        with checksum_path.open("x", encoding="ascii") as stream:
            stream.write(receipt["sha256"] + "  " + archive.name + "\n")
        write_new(receipt_path, receipt)
        return receipt
    except BaseException:
        # Failed packages are retained for diagnosis, with no success receipt.
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("inventory", "build", "reproduce", "_worker"))
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[4])
    parser.add_argument("--output", type=Path)
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args()
    if args.command == "inventory":
        value = inventory(args.repo_root)
        print(json.dumps({"source_files": len(value["files"]), "pinned_paths": len(value["pinned"]),
            "source_bytes": sum(x["bytes"] for x in value["files"].values())}, sort_keys=True))
    elif args.command == "build":
        if args.output is None:
            parser.error("build requires --output")
        print(json.dumps(build(args.repo_root, args.output), sort_keys=True))
    else:
        if args.output_dir is None:
            parser.error("reproduce requires --output-dir")
        result = worker(args.repo_root, args.output_dir) if args.command == "_worker" else reproduce(args.repo_root, args.output_dir)
        print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
