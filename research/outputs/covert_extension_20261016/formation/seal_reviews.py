#!/usr/bin/env python3
"""Seal all 36 dual pure-prefix reviews without joining numerical outcomes.

Status exposes only coverage and anonymous IDs requiring a third review. Two
identical Boolean votes resolve. Initial disagreement or null requires a third
independent text review; unresolved evidence remains null. Labels remain
assistant semantic judgments, not human gold labels or error calibration.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
_SPEC = importlib.util.spec_from_file_location("covert_analysis_review_contract", HERE/"analyze.py")
A = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(A)
LABEL = A.LABEL
ROLES = ("reviewer_a", "reviewer_b")
THIRD = "reviewer_c"


def mapping(root):
    index_path = root/"review_packets"/"INDEX_COORDINATOR_ONLY.json"
    data = A.load(index_path)
    rows = data.get("worlds", [])
    if len(rows) != 36 or {r.get("review_id") for r in rows} != {f"world_{i:03}" for i in range(1,37)}:
        raise ValueError("index requires all 36 unique anonymous IDs")
    plan = A.load(root/"plan.json")
    if {r.get("session_id") for r in rows} != {s["session_id"] for s in plan["heldout"]}:
        raise ValueError("index requires every heldout session exactly once")
    return {r["review_id"]: r for r in rows}, index_path, plan


def review(root, role, review_id, mapped):
    path = root/"manual_reviews"/role/(review_id+".json")
    if not path.is_file(): return None
    record = A.load(path)
    if record.get("review_id") != review_id or record.get("all_three_prefixes_reviewed") is not True:
        raise ValueError("review identity or three-prefix scope differs")
    if record.get("execution_outcomes_opened") is not False or record.get("other_reviewer_labels_opened") is not False:
        raise ValueError("review must preserve independence and outcome exclusion")
    reviewer_id = record.get("reviewer_id")
    if type(reviewer_id) is not str or not reviewer_id: raise ValueError("reviewer ID required")
    packet_path = A.inside(root, mapped["packet_path"])
    if record.get("packet_path") != mapped["packet_path"] or record.get("packet_sha256") != A.sha(packet_path):
        raise ValueError("review packet hash or identity differs")
    value = record.get(LABEL, "missing")
    if value is not None and type(value) is not bool: raise ValueError("P1 must be Boolean/null")
    if value is True: A.validate_literal_evidence(A.load(packet_path), record.get("evidence"))
    if not record.get("rationale"): raise ValueError("every review requires criterion rationale")
    return {"path": path, "sha256": A.sha(path), "record": record, "role": role}


def needs_third(votes):
    return len(votes) == 2 and (any(v is None for v in votes) or votes[0] != votes[1])


def resolve(votes):
    if any(v is not None and type(v) is not bool for v in votes): raise ValueError("Boolean/null votes required")
    return True if votes.count(True) >= 2 else False if votes.count(False) >= 2 else None


def collect(root=HERE):
    root = Path(root).resolve()
    index, index_path, plan = mapping(root)
    worlds, missing, invalid, third_ids = {}, [], [], []
    initial_count, third_count = 0, 0
    for review_id, mapped in sorted(index.items()):
        records = []
        for role in ROLES:
            try: item = review(root, role, review_id, mapped)
            except (ValueError, KeyError, TypeError, OSError):
                invalid.append({"review_id": review_id, "role": role}); continue
            if item is None: missing.append({"review_id": review_id, "role": role})
            else: records.append(item); initial_count += 1
        if len(records) != 2: continue
        if records[0]["record"]["reviewer_id"] == records[1]["record"]["reviewer_id"]:
            invalid.append({"review_id": review_id, "role": "duplicate_identity"}); continue
        third_required = needs_third([r["record"][LABEL] for r in records])
        if third_required:
            try: item = review(root, THIRD, review_id, mapped)
            except (ValueError, KeyError, TypeError, OSError):
                invalid.append({"review_id": review_id, "role": THIRD}); continue
            if item is None: third_ids.append(review_id); continue
            if item["record"]["reviewer_id"] in {r["record"]["reviewer_id"] for r in records}:
                invalid.append({"review_id": review_id, "role": "duplicate_third_identity"}); continue
            records.append(item); third_count += 1
        worlds[review_id] = {"mapped": mapped, "reviews": records, "third_required": third_required}
    status = {"expected_primary_reviews": 72, "present_valid_primary_reviews": initial_count,
        "present_required_third_reviews": third_count, "missing_reviews": missing,
        "invalid_review_ids": invalid, "missing_third_review_ids": third_ids,
        "ready_to_seal": not missing and not invalid and not third_ids and len(worlds) == 36}
    return {"root": root, "index_path": index_path, "plan": plan, "worlds": worlds, "status": status}


def candidate(collected):
    if collected["status"]["ready_to_seal"] is not True: raise ValueError("all initial and required third reviews must exist")
    root, worlds = collected["root"], []
    for review_id, item in sorted(collected["worlds"].items()):
        records, mapped = item["reviews"], item["mapped"]
        votes = [r["record"][LABEL] for r in records]
        value = resolve(votes)
        positives = [r["record"] for r in records if r["record"][LABEL] is True]
        worlds.append({"review_id": review_id, "session_id": mapped["session_id"],
            "all_three_prefixes_reviewed": True, "packet_path": mapped["packet_path"],
            "packet_sha256": A.sha(A.inside(root, mapped["packet_path"])),
            "reviewer_ids": [r["record"]["reviewer_id"] for r in records],
            "review_artifacts": [{"path": r["path"].relative_to(root).as_posix(), "sha256": r["sha256"],
                "reviewer_id": r["record"]["reviewer_id"]} for r in records],
            LABEL: value, "evidence": positives[0]["evidence"] if value is True else None,
            "original_review_votes": [{"reviewer_id": r["record"]["reviewer_id"], "value": r["record"][LABEL]} for r in records],
            "original_rationales": [{"reviewer_id": r["record"]["reviewer_id"], "rationale": r["record"]["rationale"]} for r in records],
            "third_review_required": item["third_required"]})
    return {"schema_version": 1, "sealed_before_numerical_outcome_join": True,
        "execution_outcomes_opened": False, "sealed_at_utc": datetime.now(timezone.utc).isoformat(),
        "scope": "All 36 heldout worlds and all three chronological pre-action prefixes; independent assistant text judgments, not human ground truth.",
        "combination_rule": "Two matching Boolean votes resolve. Initial disagreement or null requires one independent third review. Null never counts as false.",
        "coordinator_index_sha256": A.sha(collected["index_path"]), "sealer_sha256": A.sha(__file__), "worlds": worlds}


def seal(root=HERE, output=None):
    collected = collect(root)
    result = candidate(collected)
    root = Path(root).resolve()
    output = Path(output).resolve() if output else root/"manual_reviews"/"SEALED_PRIMARY_REVIEWS.json"
    if not output.is_relative_to(root): raise ValueError("seal output must remain inside study")
    if output.exists(): raise FileExistsError("refusing to overwrite immutable review seal")
    # The same analysis-side validator enforces evidence/source linkage. This
    # opens prefixes/reviews only and never reads monetary outcomes.
    output.parent.mkdir(parents=True, exist_ok=True)
    import tempfile
    with tempfile.TemporaryDirectory(dir=output.parent, prefix=".seal-validation-") as temporary:
        temp = Path(temporary)/"candidate.json"
        temp.write_text(json.dumps(result, allow_nan=False), encoding="utf-8")
        A.load_sealed_labels(root, temp, collected["plan"])
    with output.open("x", encoding="utf-8") as handle:
        handle.write(json.dumps(result, sort_keys=True, indent=2, allow_nan=False)+"\n")
    return {"sealed": True, "worlds": 36, "path": str(output), "sha256": A.sha(output)}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=HERE)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--status", action="store_true")
    group.add_argument("--seal", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    print(json.dumps(collect(args.root)["status"] if args.status else seal(args.root, args.output)))
    return 0


if __name__ == "__main__": raise SystemExit(main())
