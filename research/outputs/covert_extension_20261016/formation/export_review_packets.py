#!/usr/bin/env python3
"""Export anonymous pure-prefix packets, never outcomes or actual ledgers.

The coordinator index is not for reviewers. Authored text and previous public
certifications can reveal treatments or prior results: anonymity is metadata
redaction, not a claim of perfect treatment or outcome blinding.
"""
import argparse
import hashlib
import json
from pathlib import Path
import random

HERE = Path(__file__).resolve().parent
SEED = 0xC037B11D
SOURCE_KEYS = ("round", "organization_policy", "notes", "public_reports", "public_certification_history")


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")


def load(path):
    def pairs(items):
        obj = {}
        for key, value in items:
            if key in obj: raise ValueError("duplicate JSON key")
            obj[key] = value
        return obj
    def reject(v): raise ValueError("nonfinite JSON")
    return json.loads(Path(path).read_text(encoding="utf-8"), object_pairs_hook=pairs, parse_constant=reject)


def save_new(path, value):
    blob = canonical(value)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_bytes() != blob: raise ValueError("immutable export changed")
    else:
        with path.open("xb") as handle: handle.write(blob)


def export(root=HERE):
    root = Path(root).resolve()
    plan = load(root/"plan.json")
    specs = list(plan["heldout"])
    if len(specs) != 36 or len({s["session_id"] for s in specs}) != 36:
        raise ValueError("exactly 36 unique heldout worlds required")
    random.Random(SEED).shuffle(specs)
    mapping, available = [], 0
    for number, spec in enumerate(specs, 1):
        review_id = f"world_{number:03}"
        source = Path("runs")/"heldout"/spec["session_id"]/"rounds"/"3"/"prefix_review_packet.json"
        target = Path("review_packets")/(review_id+".json")
        mapping.append({"review_id": review_id, "session_id": spec["session_id"],
            "source_packet": source.as_posix(), "packet_path": target.as_posix()})
        if not (root/source).is_file(): continue
        original = load(root/source)
        packet = {k: original[k] for k in SOURCE_KEYS if k in original}
        if original.get("round") != 3 or original.get("host_supplied_pact") is not False:
            raise ValueError("heldout source must be round-three nonassigned prefix")
        packet.update(review_id=review_id, all_three_prefixes_available=True,
            no_private_memory_or_actual_numeric_ledger=True, no_operational_audit_results=True,
            scope="Three chronological pre-action prefixes; current final claim, review and certification outputs excluded.",
            redaction_limit="Authored text and prior routine public certification facts can reveal treatment or prior outcomes.")
        save_new(root/target, packet)
        available += 1
    save_new(root/"review_packets"/"INDEX_COORDINATOR_ONLY.json", {
        "seed": SEED, "reviewers_must_not_open": True, "worlds": mapping})
    return {"expected": 36, "exported": available,
        "exporter_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=HERE)
    args = parser.parse_args(argv)
    print(json.dumps(export(args.root)))
    return 0


if __name__ == "__main__": raise SystemExit(main())
