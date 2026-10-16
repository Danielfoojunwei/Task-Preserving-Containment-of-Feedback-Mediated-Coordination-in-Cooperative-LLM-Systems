#!/usr/bin/env python3
"""Restore hash-checked archival mtimes used by the historical agreement audit.

Git does not preserve file modification times. These values come from the
previously released evidence ZIP, not Git dates or reconstructed chronology.
They are local archival metadata, not external temporal attestation. No evidence
contents are rewritten, and no API or network operation is performed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path


MANIFEST = Path("docs/provenance/agreement_20261016_local_mtimes.json")
MANIFEST_SHA256 = "87a3d59829799ac3db32efb22cba474e37ba56ee884ed0b9d4f74095962c3386"
STUDIES = {"agreement_pilot_20261015", "agreement_capability_20261015",
           "agreement_adversarial_20261015"}
NAMES = {"preparation_checkpoint.json", "case_generated_after_preparation.json",
         "claims_fixed_before_reviews.json", "future_cases.json", "RELEASE.json"}


def restore(root: Path, *, verify_only: bool = False) -> dict:
    root = root.resolve(strict=True)
    manifest_path = root / MANIFEST
    manifest_bytes = manifest_path.read_bytes()
    if hashlib.sha256(manifest_bytes).hexdigest() != MANIFEST_SHA256:
        raise ValueError("Archival metadata manifest SHA-256 mismatch")
    manifest = json.loads(manifest_bytes)
    if manifest.get("version") != 1 or not isinstance(manifest.get("files"), dict):
        raise ValueError("Invalid archival metadata manifest")
    checked = []
    # Verify every path and every byte before changing any file metadata.
    for name, entry in manifest["files"].items():
        relative = Path(name)
        if (relative.is_absolute() or ".." in relative.parts
                or len(relative.parts) < 4
                or relative.parts[:2] != ("research", "outputs")
                or relative.parts[2] not in STUDIES or relative.name not in NAMES):
            raise ValueError("Out-of-scope archival path: " + name)
        path = root / relative
        if path.is_symlink() or not path.is_file() or not path.resolve().is_relative_to(root):
            raise ValueError("Missing or unsafe archival file: " + name)
        if (type(entry.get("size")) is not int or entry["size"] < 0
                or type(entry.get("mtime_ns")) is not int or entry["mtime_ns"] < 0):
            raise ValueError("Invalid recorded metadata: " + name)
        data = path.read_bytes()
        if len(data) != entry["size"] or hashlib.sha256(data).hexdigest() != entry["sha256"]:
            raise ValueError("Archived evidence byte mismatch: " + name)
        checked.append((path, entry["mtime_ns"]))
    if not verify_only:
        for path, mtime_ns in checked:
            os.utime(path, ns=(path.stat().st_atime_ns, mtime_ns))
        if any(path.stat().st_mtime_ns != mtime_ns for path, mtime_ns in checked):
            raise ValueError("Filesystem did not preserve recorded nanosecond mtimes")
    return {"files_verified": len(checked), "recorded_local_mtimes_restored": not verify_only,
            "manifest_sha256": MANIFEST_SHA256, "api_calls": 0,
            "limitation": "Local archival metadata; no external temporal attestation."}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--verify-only", action="store_true")
    args = parser.parse_args()
    try:
        result = restore(args.root, verify_only=args.verify_only)
    except (OSError, ValueError, TypeError, KeyError) as exc:
        parser.exit(1, str(exc) + "\n")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
