#!/usr/bin/env python3
"""Independent offline check of all-eight-source adaptive defense branches.

Imports only the frozen pure parent/supplement checkers, never a runner,
transport, analyzer, environment credential, or network module. Live reads
require the root's explicit --release flag.
"""
import argparse
from collections import Counter
from copy import deepcopy
from datetime import datetime, timezone
from decimal import Decimal
from fractions import Fraction
import importlib.util
import json
from pathlib import Path
import random

HERE = Path(__file__).resolve().parent
SUPPLEMENT = HERE.parent / "negotiation_causal_20261016"
PARENT = HERE.parent / "reciprocity_causal_20261016"
_spec = importlib.util.spec_from_file_location("defense_supplement_independent", SUPPLEMENT / "independent_verify.py")
supplement = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(supplement)
base = supplement.base
BRANCHES = ("unchanged", "no_future_notes", "live_receipt_gate_disclosed")
BLOCKS = tuple(range(9301, 9309))


def fresh_cases(block):
    rng = random.Random((block + 100) ^ 0xCA05A116)
    return [{"round": n, "receipts": {a: rng.randint(2, 7) for a in "AB"},
        "public_tasks": [{"id": "T" + str(i), "priority": rng.randint(1, 7)}
                         for i in range(1, 5)]} for n in (3, 4)]


def bounded_source_state(state):
    """Reject future state even if an archive labels it as a round-2 snapshot."""
    return (type(state) is dict and [r.get("round") for r in state.get("round_ledgers", [])] == [1, 2]
            and all(type(n.get("round")) is int and n["round"] <= 2 for n in state.get("notes", []))
            and all(type(r.get("round")) is int and r["round"] <= 2
                    for actor in "AB" for r in state.get("own_action_outputs", {}).get(actor, []))
            and all(type(r.get("round")) is int and r["round"] <= 2
                    for actor in "AB" for r in state.get("own_observed_cases", {}).get(actor, [])))


class Audit(base.Audit):
    def __init__(self, root):
        super().__init__(root, phase="all")
        self.source_reports = []

    def actor_messages(self, actor, condition, state, stage, round_number,
                       case=None, claims=None, live_gate=False):
        self.same(condition, "full", "defense_keeps_full_physics_except_future_delivery_or_gate")
        messages = super().actor_messages(actor, condition, state, stage, round_number,
                                          case=case, claims=claims, live_gate=live_gate)
        if stage == "negotiation":
            obj = base.strict_json(messages[1]["content"])
            obj["instruction"] += " " + supplement.PARAGRAPH
            messages[1]["content"] = base.canonical(obj).decode()
        return messages

    def hashes_and_plan(self):
        for name, expected in self.freeze["sha256"].items():
            path = self.root / name
            self.check(path.is_file(), "defense_frozen_source_exists", name)
            if path.is_file():
                self.same(base.file_hash(path), expected, "defense_frozen_source_or_snapshot_hash", name)
        for directory in (PARENT, SUPPLEMENT):
            frozen = base.load(directory / "FREEZE.json")
            for name, expected in frozen["sha256"].items():
                self.same(base.file_hash(directory / name), expected, "imported_study_freeze_unchanged", str(directory / name))
        sources = self.plan["sources"]
        self.same(len(sources), 8, "all_eight_directed_source_worlds")
        self.same({s["block_id"] for s in sources}, set(BLOCKS), "all_eight_source_blocks")
        self.check(all(s["condition"] == "directed" for s in sources), "source_arm_directed_only")
        source_plan = base.load(SUPPLEMENT / "plan.json")
        expected = {s["session_id"]: s for s in source_plan["validation"] if s["condition"] == "directed"}
        self.same({s["session_id"] for s in sources}, set(expected), "no_selection_by_label_or_profit")
        for source in sources:
            for key, value in expected[source["session_id"]].items():
                self.same(source.get(key), value, "source_specification_matches_frozen_supplement", key)
        expected_jobs = {(s["session_id"], b) for s in sources for b in BRANCHES}
        jobs = [(j["session_id"], j["branch"]) for j in self.plan["jobs"]]
        self.same(len(jobs), 24, "exactly_24_branch_jobs")
        self.same(set(jobs), expected_jobs, "all_three_branches_for_every_source")
        self.same(len(set(jobs)), len(jobs), "no_duplicate_branch_jobs")
        expected_dispatch = [{"session_id": s["session_id"], "branch": b}
                             for s in sorted(sources, key=lambda s: s["block_id"]) for b in BRANCHES]
        random.Random(0xDEF8432).shuffle(expected_dispatch)
        self.same(self.plan["jobs"], expected_dispatch, "frozen_randomized_branch_dispatch_order")
        self.same(set(self.plan["continuation_cases"]), set(map(str, BLOCKS)), "fresh_case_eight_blocks")
        for block in BLOCKS:
            self.same(self.plan["continuation_cases"][str(block)], fresh_cases(block),
                      "fresh_alternative_cases_reconstructed_seed_plus100", block)
        material = deepcopy(self.material)
        defense = material.pop("defense", {})
        self.same(material, base.load(SUPPLEMENT / "prompt_material.json"), "directed_prompt_material_preserved")
        self.same(defense.get("gate_notice"), self.material["gate_notice"], "live_gate_notice_exact_parent_rule")
        self.same(defense.get("branches"), list(BRANCHES), "only_declared_defense_branches")
        self.same(defense.get("source_round"), 2, "source_round_two")
        self.same(defense.get("new_rounds"), [3, 4], "two_fresh_alternative_rounds")
        self.same(defense.get("future_note_cut_retains_past_delivered_notes"), True, "retained_history_declared")
        self.same(defense.get("directed_scaffolding_retained"), True, "scaffold_retained_declared")
        settings = self.plan["settings"]
        for key, value in {"actor_model": base.ACTOR_MODEL, "judge_model": base.JUDGE_MODEL,
                "temperature": .7, "actor_max_tokens": 1000, "judge_max_tokens": 1500,
                "cap_usd": 5., "workers": 3, "max_attempts": 1,
                "parent_separate_cap_usd": 25., "supplement_separate_cap_usd": 10.,
                "aggregate_authorization_usd": 40., "unused_other_study_budget_may_not_be_borrowed": True,
                "branches": list(BRANCHES), "rounds_per_branch": 2,
                "actor_calls_max": 384, "judge_calls_max": 48, "logical_calls_max": 432, "new_pilot": False}.items():
            self.same(settings.get(key), value, "defense_runtime_setting", key)
        self.same(self.freeze.get("defense_cap_usd"), 5., "frozen_defense_separate_cap")
        self.same(self.freeze.get("aggregate_authorization_usd"), 40., "frozen_aggregate_authorization")

    def reconstruct_source(self, source):
        sid = source["session_id"]
        source_path = self.root / source["source_state_path"]
        expected_path = SUPPLEMENT / "runs" / "validation" / sid / "rounds" / "2" / "end_state.json"
        self.same(source_path.resolve(), expected_path.resolve(), "source_path_exact_round2_end_state", sid)
        self.same(base.file_hash(source_path), source["source_state_sha256"], "source_original_round2_hash", sid)
        snapshot = self.root / source["snapshot_path"]
        self.same(snapshot.read_bytes(), source_path.read_bytes(), "snapshot_byte_identical_to_actual_round2_state", sid)
        checker = supplement.Audit(SUPPLEMENT)
        checker.active_arm = "directed"
        spec = {k: source[k] for k in ("session_id", "condition", "seed", "block_id", "slot")}
        normalized = dict(spec, condition="full", study_arm="directed")
        state = base.initial_state()
        for case in checker.plan["cases"][str(source["seed"])][:2]:
            state = base.Audit.round(checker, "validation", normalized, case, state)
            if state is None:
                self.check(False, "source_first_two_rounds_incomplete", sid)
                return None
        self.same(checker.failures, [], "source_first_two_rounds_reconstructed_from_raw_wire", sid)
        self.check(all(c["finished_at"] < self.freeze["frozen_at"] for c in checker.calls),
                   "source_round_two_completed_before_defense_freeze", sid)
        self.check(bounded_source_state(state), "source_has_no_original_round3_or4_state", sid)
        self.same(base.load(snapshot), state, "source_snapshot_matches_independent_raw_reconstruction", sid)
        self.source_reports.append({"session_id": sid, "raw_calls_verified": len(checker.calls),
            "source_state_sha256": source["source_state_sha256"], "passed": not checker.failures,
            "response_ids": [c["response_id"] for c in checker.calls if c["response_id"]],
            "failures": checker.failures})
        return state

    def run(self):
        self.hashes_and_plan()
        preflight = base.Audit(PARENT, phase="pilot").run()
        self.same(preflight.get("passed"), True, "parent_preflight_independent_integrity")
        self.same(preflight.get("pilot_gate", {}).get("pass"), True, "parent_preflight_independent_gate_pass")
        sources = {}
        for source in self.plan["sources"]:
            try:
                sources[source["session_id"]] = self.reconstruct_source(source)
            except (ValueError, KeyError, TypeError, IndexError, OSError) as exc:
                self.check(False, "source_reconstruction_exception", source["session_id"] + ":" + repr(exc))
        by_id = {s["session_id"]: s for s in self.plan["sources"]}
        for job in self.plan["jobs"]:
            sid, branch = job["session_id"], job["branch"]
            if sources.get(sid) is None:
                self.check(False, "branch_source_unavailable", sid)
                continue
            spec = {k: by_id[sid][k] for k in ("session_id", "condition", "seed", "block_id", "slot")}
            spec.update(condition="full", study_arm="directed")
            state = deepcopy(sources[sid])
            count = 0
            try:
                for case in self.plan["continuation_cases"][str(spec["seed"])]:
                    state = super().round("continuations", spec, case, state, branch=branch)
                    if state is None:
                        break
                    self.rounds[-1]["condition"] = "directed"
                    count += 1
            except (ValueError, KeyError, TypeError, IndexError, OSError) as exc:
                self.check(False, "defense_branch_audit_exception", sid + "/" + branch + ":" + repr(exc))
            self.same(count, 2, "both_fresh_rounds_complete", sid + "/" + branch)
            if count == 2:
                self.sessions.append({"phase": "continuations", "specification": spec,
                    "branch": branch, "rounds": 2, "M_world": None})
        inventory = super().inventory_and_budget()
        for key, count in (("actor_calls", 384), ("judge_calls", 48), ("retained_requests", 432), ("retained_attempts", 432)):
            self.same(inventory[key], count, "exact_defense_call_count", key)
        self.check(inventory["peak_accounted_usd"] <= Decimal("5.00000000001"), "separate_defense_5_dollar_cap_at_every_event")
        self.check(inventory["accounted_including_unknown_cost_usd"] <= Decimal("5.00000000001"), "separate_final_defense_cap")
        self.same(len(self.sessions), 24, "all_24_branches_complete")
        completion_path = self.root / "continuation_completion.json"
        self.check(completion_path.is_file(), "defense_completion_record_present")
        if completion_path.exists():
            completion = base.load(completion_path)
            self.same(completion.get("complete"), len(self.sessions) == 24, "defense_completion_matches_all_branches")
            self.same(completion.get("failures"), [], "no_omitted_defense_failure_records")
            self.same(completion.get("defense_cap_usd"), 5., "completion_defense_own_cap")
            self.same(completion.get("aggregate_authorization_usd"), 40., "completion_aggregate_authorization")
            self.check(Decimal(str(completion.get("parent_accounted_at_launch_usd", 1e9))) <= Decimal("25.00000000001"),
                       "parent_launch_accounted_within_own_cap")
            self.check(Decimal(str(completion.get("supplement_accounted_at_launch_usd", 1e9))) <= Decimal("10.00000000001"),
                       "supplement_launch_accounted_within_own_cap")
        source_ids = [rid for source in self.source_reports for rid in source["response_ids"]]
        fresh_ids = [c["response_id"] for c in self.calls if c["response_id"]]
        self.same(len(source_ids + fresh_ids), len(set(source_ids + fresh_ids)), "fresh_branch_responses_not_reused_from_sources")
        return {"audit_version": 1, "generated_at": datetime.now(timezone.utc).isoformat(),
            "root": str(self.root), "passed": not self.failures,
            "verifier_sha256": base.file_hash(__file__), "checks_executed": dict(self.checks),
            "failures": self.failures, "inventory": inventory, "source_reconstructions": self.source_reports,
            "parent_preflight_passed": preflight.get("passed") and preflight.get("pilot_gate", {}).get("pass"),
            "finite_certificate": base.finite_certificate(), "sessions": self.sessions,
            "rounds": self.rounds, "calls": self.calls,
            "method": "Independent raw-wire reconstruction of source rounds1/2 and every fresh branch call via frozen pure checkers; no original round3/4 source actions/outcomes read; no runner/analyzer/client imports or API calls.",
            "scope": "All8 directed source contexts, regardless of labels/payoffs. Descriptive matched continuations; no rounds-as-independent significance tests. Disclosed gate changes knowledge and enforcement together."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=HERE)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--release", action="store_true")
    args = parser.parse_args()
    if not args.release:
        parser.error("--release is required before any live outcome reads")
    report = base.jsonable(Audit(args.root).run())
    output = args.output_dir or args.root
    output.mkdir(parents=True, exist_ok=True)
    destination = output / "INDEPENDENT_VERIFICATION.json"
    destination.write_text(json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False) + "\n")
    print(json.dumps({"passed": report["passed"], "inventory": report["inventory"],
                      "failures": report["failures"], "report": str(destination)}, indent=2))
    raise SystemExit(0 if report["passed"] else 1)


if __name__ == "__main__":
    main()
