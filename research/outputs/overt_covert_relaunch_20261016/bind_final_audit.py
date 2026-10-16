#!/usr/bin/env python3
"""Post-freeze supplement: bind a completed raw audit to its exact source bytes.

No model/network imports, semantic labels, or statistical analysis. This wrapper
does not alter either frozen verifier. The before snapshot and successful final
manifest are exclusive, read-only artifacts; rerunning cannot replace them.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
import sys


class BindingError(RuntimeError):
    pass


RUNTIME_LOCK_FILENAMES = (".call.lock", ".budget.lock", ".scheduler.lock")


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def digest(path):
    with path.open("rb") as stream:
        value = hashlib.file_digest(stream, "sha256").hexdigest()
    return value


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      allow_nan=False).encode("utf-8")


def read_json(path):
    def unique_pairs(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise BindingError(f"Duplicate JSON key in {path.name}: {key}")
            result[key] = value
        return result
    def invalid_number(value):
        raise BindingError(f"Non-finite JSON number in {path.name}: {value}")
    return json.loads(path.read_text(encoding="utf-8"),
                      object_pairs_hook=unique_pairs, parse_constant=invalid_number)


def inventory(root):
    """All calls/runs files except three declared, nonsemantic runtime locks."""
    result = {}
    for directory in ("calls", "runs"):
        start = root / directory
        if start.is_symlink() or not start.is_dir():
            raise BindingError(f"Missing or symlinked inventory root: {directory}")
        for parent, directories, names in os.walk(start, followlinks=False):
            for name in directories:
                if (Path(parent) / name).is_symlink():
                    raise BindingError("Symlinked source directory is not auditable")
            for name in names:
                if name in RUNTIME_LOCK_FILENAMES:
                    continue
                path = Path(parent) / name
                before = path.lstat()
                if not stat.S_ISREG(before.st_mode):
                    raise BindingError("Nonregular source artifact is not auditable")
                value = digest(path)
                after = path.lstat()
                if (before.st_ino, before.st_size, before.st_mtime_ns) != (
                        after.st_ino, after.st_size, after.st_mtime_ns):
                    raise BindingError("Source artifact changed while being captured")
                result[path.relative_to(root).as_posix()] = {
                    "sha256": value, "bytes": after.st_size}
    return dict(sorted(result.items()))


def write_exclusive(path, value):
    payload = (json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()
    with path.open("xb") as stream:
        stream.write(payload)
        stream.flush()
        os.fsync(stream.fileno())
    path.chmod(0o444)


def bound_audit(root, output_dir, *, report_name="INDEPENDENT_VERIFICATION_ALL.json",
                verifier_args=("--phase", "all", "--release"), phase="all"):
    root = Path(root).resolve()
    output_dir = Path(output_dir).resolve()
    try:
        output_dir.relative_to(root)
    except ValueError as error:
        raise BindingError("Audit output must be within the study root") from error
    output_dir.mkdir(parents=True, exist_ok=True)
    report_path = output_dir / report_name
    manifest_path = output_dir / "SOURCE_BINDINGS.json"
    before_path = output_dir / "SOURCE_SNAPSHOT_BEFORE_AUDIT.json"
    log_path = output_dir / "RAW_AUDIT.log"
    for path in (report_path, manifest_path, before_path, log_path):
        if path.exists() or path.is_symlink():
            raise BindingError(f"Refusing to overwrite prior audit artifact: {path.name}")
    freeze_path = root / "FREEZE.json"
    verifier_path = root / "independent_verify.py"
    if freeze_path.is_symlink() or verifier_path.is_symlink():
        raise BindingError("Freeze and verifier must be regular, nonsymlinked files")
    freeze_sha = digest(freeze_path)
    freeze = read_json(freeze_path)
    expected = freeze.get("sha256", {}).get("independent_verify.py")
    verifier_sha = digest(verifier_path)
    if not expected or verifier_sha != expected:
        raise BindingError("Verifier does not match the frozen source hash")
    capture_started = utc_now()
    before = inventory(root)
    capture_finished = utc_now()
    inventory_sha = hashlib.sha256(canonical(before)).hexdigest()
    snapshot = {"schema_version": 1, "inventory_roots": ["calls", "runs"],
                "inventory_excluded_filenames": list(RUNTIME_LOCK_FILENAMES),
                "capture_started_at": capture_started,
                "capture_finished_at": capture_finished,
                "artifacts": before, "inventory_sha256": inventory_sha,
                "source_freeze_sha256": freeze_sha,
                "verifier_sha256": verifier_sha}
    write_exclusive(before_path, snapshot)
    audit_started = utc_now()
    with log_path.open("xb") as log:
        run = subprocess.run([sys.executable, str(verifier_path), "--root", str(root),
                              *verifier_args, "--output-dir", str(output_dir)],
                             cwd=root, stdout=log, stderr=subprocess.STDOUT,
                             check=False)
    audit_finished = utc_now()
    if run.returncode:
        raise BindingError(f"Frozen raw audit failed with exit code {run.returncode}; see RAW_AUDIT.log")
    report = read_json(report_path)
    if report.get("passed") is not True:
        raise BindingError("Raw audit report did not pass")
    if report.get("phase", phase) != phase:
        raise BindingError("Raw audit report has the wrong phase")
    if report.get("verifier_sha256") != verifier_sha:
        raise BindingError("Raw audit report does not bind the frozen verifier")
    if digest(freeze_path) != freeze_sha or digest(verifier_path) != verifier_sha:
        raise BindingError("Freeze or verifier changed during raw audit")
    after = inventory(root)
    if before != after:
        raise BindingError("Source byte inventory changed during raw audit; no binding released")
    if digest(before_path) != hashlib.sha256((json.dumps(snapshot, indent=2, sort_keys=True,
            allow_nan=False) + "\n").encode()).hexdigest():
        raise BindingError("Persisted pre-audit snapshot changed during audit")
    manifest = {
        "schema_version": 1, "passed": True, "phase": phase,
        "inventory_roots": ["calls", "runs"],
        "inventory_excluded_filenames": list(RUNTIME_LOCK_FILENAMES),
        "capture_started_at": capture_started,
        "capture_finished_at": capture_finished,
        "audit_started_at": audit_started, "audit_finished_at": audit_finished,
        "confirmed_at": utc_now(), "captured_before_audit": True,
        "checked_unchanged_after_audit": True, "artifact_inventory_unchanged": True,
        "artifacts": before, "inventory_sha256": inventory_sha,
        "raw_report": {"path": report_path.relative_to(root).as_posix(),
                       "sha256": digest(report_path), "passed": True},
        "verifier": {"path": "independent_verify.py", "sha256": verifier_sha,
                     "frozen_sha256": expected},
        "source_freeze_sha256": freeze_sha,
        "before_snapshot": {"path": before_path.relative_to(root).as_posix(),
                            "sha256": digest(before_path)},
        "binding_wrapper_sha256": digest(Path(__file__)),
        "scope": "Exact completed calls/runs bytes audited, excluding only three declared nonsemantic runtime lock filenames; no semantic or statistical conclusion."}
    write_exclusive(manifest_path, manifest)
    return {"passed": True, "phase": phase, "source_artifact_count": len(before),
            "source_total_bytes": sum(row["bytes"] for row in before.values()),
            "inventory": report.get("inventory"),
            "report": str(report_path), "source_bindings": str(manifest_path)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--continuation", action="store_true",
                        help="Use the continuation verifier's unsuffixed report and CLI")
    parser.add_argument("--release", action="store_true",
                        help="Authorize raw forensic outcome reconstruction, not statistical release")
    args = parser.parse_args()
    if not args.release:
        parser.error("--release is required before any source reads")
    keywords = ({"report_name": "INDEPENDENT_VERIFICATION.json",
                 "verifier_args": ("--release",), "phase": "all"}
                if args.continuation else {})
    try:
        result = bound_audit(args.root, args.output_dir or args.root / "independent/final",
                             **keywords)
    except (BindingError, OSError, ValueError) as error:
        print(json.dumps({"passed": False, "error": str(error)}))
        raise SystemExit(1)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
