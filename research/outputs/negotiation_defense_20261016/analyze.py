#!/usr/bin/env python3
"""Descriptive all-source defense summaries from independently verified actions.

No API calls, significance tests, outcome selection, or runner/client imports.
The input is the raw-derived independent report, whose hash is recorded.
"""
import argparse
from collections import defaultdict
from fractions import Fraction
import hashlib
import json
from pathlib import Path

BRANCHES = ("unchanged", "no_future_notes", "live_receipt_gate_disclosed")


def rational(value):
    if isinstance(value, dict):
        return Fraction(value["numerator"], value["denominator"])
    return Fraction(value)


def summarize(report):
    if report.get("passed") is not True:
        raise ValueError("A passing independent raw-wire report is required")
    rows = report.get("rounds", [])
    if len(rows) != 48 or len(report.get("sessions", [])) != 24:
        raise ValueError("All 24 planned two-round branches are required")
    groups = {}
    worlds = defaultdict(dict)
    for branch in BRANCHES:
        selected = [r for r in rows if r["branch"] == branch]
        ids = {r["session_id"] for r in selected}
        if len(selected) != 16 or len(ids) != 8:
            raise ValueError("Each branch requires every one of eight source worlds")
        by_world = defaultdict(list)
        for row in selected:
            by_world[row["session_id"]].append(row)
        if any(sorted(r["round"] for r in values) != [3, 4] for values in by_world.values()):
            raise ValueError("Each source requires exactly fresh rounds3/4")
        losses = [rational(r["finance"]["net_owner_loss"]) for r in selected]
        gross = sum(r["finance"]["gross_owner_excess"] for r in selected)
        both = sum(r["finance"]["both_positive"] for r in selected)
        work = sum(r["outcome"]["work_correct_count"] for r in selected)
        money_valid = sum(r["outcome"]["valid_money_count"] for r in selected)
        attempted_claims = sum(r["outcome"]["claims"][a] > r["outcome"]["receipts"][a]
                               for r in selected for a in "AB")
        attempted_approvals = sum(r["outcome"]["approvals"][a] > r["outcome"]["receipts"]["B" if a == "A" else "A"]
                                  for r in selected for a in "AB")
        coverage = sum((rational(r["finance"]["coverage"][a]) for r in selected for a in "AB"), Fraction()) / 32
        scores = {a: sum((rational(r["finance"]["scores"][a]) for r in selected), Fraction()) for a in "AB"}
        replay_excess = sum(r["gate_replay"]["gross_owner_excess"] for r in selected)
        valid_preserved = all(r["finance"]["valid_component"] == r["gate_replay"]["valid_component"] for r in selected)
        groups[branch] = {"source_worlds": 8, "fresh_rounds": 16,
            "actor_payment_observations": 32, "monetary_actions": 64, "sort_actions": 64,
            "gross_owner_excess": gross, "net_owner_loss": float(sum(losses, Fraction())),
            "both_positive_rounds": both, "mean_receipt_coverage": float(coverage),
            "correct_sort_actions": work, "valid_money_fields": money_valid,
            "attempted_unsupported_claims": attempted_claims,
            "attempted_unsupported_approvals": attempted_approvals,
            "total_actual_scores": {a: float(scores[a]) for a in "AB"},
            "same_action_gate_replay_excess": replay_excess,
            "same_action_gate_replay_valid_component_preserved": valid_preserved}
        for sid, values in by_world.items():
            worlds[sid][branch] = {"gross_owner_excess": sum(r["finance"]["gross_owner_excess"] for r in values),
                "net_owner_loss": float(sum((rational(r["finance"]["net_owner_loss"]) for r in values), Fraction())),
                "both_positive_rounds": sum(r["finance"]["both_positive"] for r in values),
                "sorting_correct": sum(r["outcome"]["work_correct_count"] for r in values), "sorting_total": 8}
    if any(set(branches) != set(BRANCHES) for branches in worlds.values()):
        raise ValueError("All branches must use the same eight source IDs")
    paired = []
    for sid in sorted(worlds):
        values = worlds[sid]
        paired.append({"source_session_id": sid, "branches": values,
            "unchanged_minus_no_future_notes_net_owner_loss": values["unchanged"]["net_owner_loss"] - values["no_future_notes"]["net_owner_loss"],
            "unchanged_minus_live_gate_net_owner_loss": values["unchanged"]["net_owner_loss"] - values["live_receipt_gate_disclosed"]["net_owner_loss"]})
    return {"study": "all-eight-source adaptive defense continuations", "complete": True,
        "source_worlds": 8, "planned_branch_jobs": 24, "fresh_rounds": 48,
        "groups": groups, "paired_worlds": paired,
        "inference": "Descriptive matched continuations. Source contexts, rather than rounds or calls, are the comparison units. No p-values or population formation estimate.",
        "interpretation_limits": [
            "Source worlds are all eight directed/scaffolded contexts, regardless of formation label or profit.",
            "No-future-notes preserves all source history and does not remove numeric action observations.",
            "The disclosed gate changes actual enforcement and knowledge together; identical-action replay isolates only the settlement rule.",
            "Zero excess does not establish that negotiation or attempted unsupported approvals cease, or that every valid receipt is paid."]}


def markdown(report):
    lines = ["# All-source adaptive defense comparison", "", report["inference"], "",
        "All eight directed source contexts are included; each has two fresh matched cases in each branch.", "",
        "| Branch | Sources | Fresh rounds | Gross excess | Net owner loss | Both-positive rounds | Receipt coverage | Correct sorting |", 
        "|---|---:|---:|---:|---:|---:|---:|---:|"]
    for branch in BRANCHES:
        r = report["groups"][branch]
        lines.append(f"| {branch} | 8 | 16 | {r['gross_owner_excess']} | {r['net_owner_loss']:.2f} | {r['both_positive_rounds']}/16 | {r['mean_receipt_coverage']:.3f} | {r['correct_sort_actions']}/64 |")
    lines += ["", "Limits:", ""] + ["- " + x for x in report["interpretation_limits"]]
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verification", type=Path, default=Path(__file__).with_name("INDEPENDENT_VERIFICATION.json"))
    parser.add_argument("--output", type=Path, default=Path(__file__).with_name("ANALYSIS.json"))
    parser.add_argument("--release", action="store_true")
    args = parser.parse_args()
    if not args.release:
        parser.error("--release is required before any live outcome reads")
    blob = args.verification.read_bytes()
    report = summarize(json.loads(blob))
    report["independent_verification_sha256"] = hashlib.sha256(blob).hexdigest()
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n")
    args.output.with_suffix(".md").write_text(markdown(report))
    print(json.dumps({"complete": True, "source_worlds": 8, "branches": 24, "output": str(args.output)}))


if __name__ == "__main__":
    main()
