#!/usr/bin/env python3
"""Export prefix text only; never open payments, audit results or labels."""
import hashlib
import json
from pathlib import Path
import random

HERE = Path(__file__).resolve().parent


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode()


def save_new(path, value):
    data = canonical(value)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_bytes() != data:
            raise ValueError("Export changed: " + str(path))
    else:
        with path.open("xb") as stream:
            stream.write(data)


def export(root=HERE):
    root = Path(root)
    plan = json.loads((root / "plan.json").read_text())
    specs = [row for row in plan["validation"] if row["note_delivery"]]
    random.Random(0xB11D80).shuffle(specs)
    if len(specs) != 80:
        raise ValueError("Expected all 80 notes-on main worlds")
    mapping = []
    available = 0
    for index, spec in enumerate(specs, 1):
        review_id = f"world_{index:03}"
        source = Path("runs") / "validation" / spec["session_id"] / "rounds" / "4" / "prefix_review_packet.json"
        output = Path("review_packets") / (review_id + ".json")
        mapping.append({"review_id": review_id, "session_id": spec["session_id"],
                        "source_packet": str(source), "packet_path": str(output)})
        if not (root / source).is_file():
            continue
        original = json.loads((root / source).read_text())
        packet = {key: original[key] for key in
                  ("round", "organization_policy", "notes", "public_reports",
                   "public_concealment_projection")}
        packet.update(review_id=review_id,
                      no_private_memory_or_numeric_ledger=True,
                      no_operational_audit_results=True,
                      scope="Four chronological pre-action prefixes; final current claim/review reports excluded.",
                      redaction_limit="Actor-authored text may reveal treatment or prior results.")
        save_new(root / output, packet)
        available += 1
    save_new(root / "review_packets" / "INDEX_COORDINATOR_ONLY.json",
             {"seed": 0xB11D80, "reviewers_must_not_open": True, "worlds": mapping})
    return {"expected": 80, "exported": available,
            "exporter_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}


if __name__ == "__main__":
    print(json.dumps(export()))
