#!/usr/bin/env python3
"""Post-freeze, read-only evidence projection; never changes study execution.

Exports only prefix notes and the owner's report text through that prefix.
Current/later claims, reviews and outcomes, numeric ledgers and private memory
are never exported. Earlier report text may itself mention prior actions.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def read(path):
    return json.loads(path.read_text())


def hashed(path, root):
    return {"path": str(path.relative_to(root)),
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def export(root, phase):
    destination = root / "review_packets" / phase
    destination.mkdir(parents=True, exist_ok=True)
    count = 0
    for source in sorted((root / "runs" / phase).glob("*/rounds/*/prefix_review_packet.json")):
        packet = read(source)
        state_path = source.parent / "start_state.json"
        state = read(state_path)
        reports = []
        for actor in ("A", "B"):
            for item in state["own_action_outputs"][actor]:
                reports.append({"actor": actor, "round": item["round"],
                                "stage": item["stage"],
                                "public_report": item["public_report"]})
        reports.extend({"actor": note["actor"], "round": note["round"],
                        "stage": "negotiation", "turn_id": note["turn_id"],
                        "public_report": note["public_report"]}
                       for note in packet["notes"])
        result = {**packet, "owner_public_report_projection": reports,
                  "sources": [hashed(source, root), hashed(state_path, root)],
                  "projection_scope": "Notes and owner public-report strings only; no private memory, numeric ledger, or current/later actions/outcomes.",
                  "exporter_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
        target = destination / (packet["session_id"] + "_r" + str(packet["round"]) + ".json")
        data = json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
        if target.exists() and target.read_text() != data:
            raise RuntimeError("Previously exported review packet changed: " + target.name)
        if not target.exists():
            target.write_text(data)
        count += 1
    return {"phase": phase, "packets_exported": count, "api_calls": 0,
            "runtime_or_frozen_sources_changed": False}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument("--phase", choices=("pilot", "validation"), required=True)
    args = parser.parse_args()
    print(json.dumps(export(args.root, args.phase)))
