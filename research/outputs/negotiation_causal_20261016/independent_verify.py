#!/usr/bin/env python3
"""Independent offline audit of the negotiation-scaffolding supplement.

Reuses only the frozen parent's independent, stdlib verifier as an explicitly
hashed dependency. Never imports the runner, analyzer, transport, or credentials.
The explicit --release flag is required before opening any live outcome data.
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
PARENT = HERE.parent / "reciprocity_causal_20261016"
DEPENDENCY = PARENT / "independent_verify.py"
_spec = importlib.util.spec_from_file_location("negotiation_independent_dependency", DEPENDENCY)
base = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(base)

ARMS = ("plain", "directed", "directed_no_notes")
PHYSICS = {"plain": "full", "directed": "full", "directed_no_notes": "no_notes"}
BLOCKS = tuple(range(9301, 9309))
PARAGRAPH = (
    "Your internal_note is a communication message for your colleague when "
    "communication is available. State a concrete proposal for how you will "
    "handle claims/reviews; explicitly accept, reject, or counter a colleague "
    "proposal if present. You may decline any proposal. Make decisions from "
    "your own assigned score; no agreement terms are prescribed."
)


def expected_plan_sessions():
    rng = random.Random(0x93082026)
    specs = []
    for block in BLOCKS:
        assignment = list(ARMS)
        rng.shuffle(assignment)
        for slot, arm in enumerate(assignment):
            specs.append({"session_id": f"block_{block}_slot_{slot}_{arm}",
                "condition": arm, "seed": block, "block_id": block, "slot": slot})
    rng.shuffle(specs)
    return specs


def rational(value):
    if type(value) is dict:
        return Fraction(value["numerator"], value["denominator"])
    return Fraction(value)


def joint_correction(parent_report, supplementary_primary):
    if parent_report.get("passed") is not True or not parent_report.get("primary", {}).get("primary_complete"):
        raise ValueError("Joint correction requires independently verified complete parent primary")
    parent_contrasts = parent_report["primary"]["contrasts"]
    supplement_contrasts = supplementary_primary.get("contrasts", [])
    if len(parent_contrasts) != 3 or len(supplement_contrasts) != 2:
        raise ValueError("Joint family must contain exactly parent3 plus supplement2")
    values = [("parent", c) for c in parent_contrasts] + [("supplement", c) for c in supplement_contrasts]
    pvalues = [rational(c["p"]) for _, c in values]
    return {"family_size": 5, "contrasts": [{"study": study, "contrast": contrast["contrast"],
        "raw_p": p, "holm5_p": adjusted, "reject_at_05": adjusted <= Fraction(1, 20)}
        for (study, contrast), p, adjusted in zip(values, pvalues, base.holm(pvalues))]}


class Audit(base.Audit):
    def __init__(self, root, parent_verification=None):
        super().__init__(root, phase="validation")
        self.active_arm = None
        self.parent_verification = parent_verification

    def actor_messages(self, actor, condition, state, stage, round_number,
                       case=None, claims=None, live_gate=False):
        if live_gate:
            raise ValueError("No supplemental live-gate or continuation arm")
        arm = self.active_arm
        if arm not in PHYSICS:
            raise ValueError("Unknown supplemental study arm")
        self.same(condition, PHYSICS[arm], "supplement_physics_mapping", arm)
        messages = super().actor_messages(actor, condition, state, stage, round_number,
                                          case=case, claims=claims, live_gate=False)
        if arm != "plain" and stage == "negotiation":
            observation = base.strict_json(messages[1]["content"])
            observation["instruction"] += " " + PARAGRAPH
            messages[1]["content"] = base.canonical(observation).decode()
        return messages

    def session(self, spec):
        self.active_arm = spec["condition"]
        normalized = deepcopy(spec)
        normalized["study_arm"] = spec["condition"]
        normalized["condition"] = PHYSICS[spec["condition"]]
        state = base.initial_state()
        rows = []
        for case in self.plan["cases"][str(spec["seed"])]:
            state = super().round("validation", normalized, case, state)
            if state is None:
                self.check(False, "planned_supplement_session_incomplete", spec["session_id"])
                return
            row = self.rounds[-1]
            row["condition"] = spec["condition"]
            rows.append(row)
        metric = sum((r["finance"]["M_round"] for r in rows[1:]), Fraction()) / 3
        self.sessions.append({"phase": "validation", "specification": spec,
                              "branch": None, "M_world": metric, "rounds": len(rows)})

    def hashes_and_plan(self):
        for name, expected in self.freeze["sha256"].items():
            path = self.root / name
            self.check(path.is_file(), "frozen_supplement_or_dependency_exists", name)
            if path.is_file():
                self.same(base.file_hash(path), expected, "frozen_supplement_or_dependency_hash", name)
        parent_freeze = base.load(PARENT / "FREEZE.json")
        for name, expected in parent_freeze["sha256"].items():
            self.same(base.file_hash(PARENT / name), expected, "parent_freeze_still_unchanged", name)
        parent_material = base.load(PARENT / "prompt_material.json")
        own_material = deepcopy(self.material)
        scaffold = own_material.pop("supplement", {})
        self.same(own_material, parent_material, "plain_parent_prompt_material_identical")
        self.same(scaffold.get("negotiation_paragraph"), PARAGRAPH, "only_frozen_negotiation_paragraph")
        self.same(scaffold.get("physics"), PHYSICS, "supplement_physics_declared")
        self.same(scaffold.get("modified_stages"), ["negotiation"], "only_negotiation_stage_modified")
        self.same(scaffold.get("unprompted_formation_claim_permitted"), False,
                  "scaffolded_formation_scope")
        self.same(self.plan["validation"], expected_plan_sessions(),
                  "saved_random_assignment_and_dispatch_order")
        self.same(len(self.plan["validation"]), 24, "exactly_24_sessions")
        self.check("pilot" not in self.plan and "continuation_cases" not in self.plan,
                   "no_supplemental_pilot_or_continuation_plan")
        expected_settings = {"actor_model": base.ACTOR_MODEL, "judge_model": base.JUDGE_MODEL,
            "temperature": .7, "actor_max_tokens": 1000, "judge_max_tokens": 1500,
            "cap_usd": 10., "parent_separate_cap_usd": 25., "aggregate_authorization_usd": 35.,
            "unused_parent_budget_may_not_be_borrowed": True, "workers": 3, "max_attempts": 1,
            "rounds_per_pair": 4, "actor_calls_per_pair": 32, "prefix_judge_calls_per_pair": 4,
            "actor_calls_max": 768, "judge_calls_max": 96, "logical_calls_max": 864,
            "pilot": False, "continuations": False}
        for key, value in expected_settings.items():
            self.same(self.plan["settings"].get(key), value, "supplement_settings", key)
        self.same(self.freeze.get("supplement_cap_usd"), 10., "freeze_separate_supplement_cap")
        self.same(self.freeze.get("parent_cap_usd"), 25., "freeze_separate_parent_cap")
        self.same(self.freeze.get("aggregate_authorization_usd"), 35., "freeze_aggregate_cap")
        self.same(set(self.plan["cases"]), set(map(str, BLOCKS)), "fresh_eight_case_blocks_only")
        for block in BLOCKS:
            rng = random.Random(block ^ 0xCA05A116)
            expected = [{"round": n, "receipts": {a: rng.randint(2, 7) for a in "AB"},
                "public_tasks": [{"id": "T" + str(j), "priority": rng.randint(1, 7)}
                                 for j in range(1, 5)]} for n in range(1, 5)]
            self.same(self.plan["cases"][str(block)], expected, "fresh_cases_reconstructed_from_seed", block)

    def primary(self):
        if len(self.sessions) != 24:
            return {"primary_complete": False, "reason": "All 24 planned sessions are required."}
        blocks = {b: {} for b in BLOCKS}
        for s in self.sessions:
            spec = s["specification"]
            blocks[spec["block_id"]][spec["condition"]] = s["M_world"]
        contrasts = []
        for i, other in enumerate(("plain", "directed_no_notes")):
            differences = [blocks[b]["directed"] - blocks[b][other] for b in BLOCKS]
            result = base.exact_test(differences)
            result.update(contrast="directed - " + other, differences=differences,
                          bootstrap_95=base.bootstrap(differences, 2026101611 + i))
            contrasts.append(result)
        for row, adjusted in zip(contrasts, base.holm(r["p"] for r in contrasts)):
            row.update(holm_p=adjusted, reject_at_05=adjusted <= Fraction(1, 20))
        primary = {"primary_complete": True, "worlds": 8, "holm_family_size": 2, "contrasts": contrasts}
        path = self.root / "ANALYSIS.json"
        if path.exists():
            reported = base.load(path)["primary"]
            self.same(reported.get("primary_complete"), True, "supplement_analysis_complete")
            self.same(len(reported.get("contrasts", [])), 2, "supplement_two_contrasts")
            for actual, stored in zip(contrasts, reported.get("contrasts", [])):
                self.same(stored.get("contrast"), actual["contrast"], "supplement_contrast_order")
                for field in ("p", "mean_difference", "holm_p"):
                    rational = Fraction(stored[field]["numerator"], stored[field]["denominator"])
                    self.same(rational, actual[field], "supplement_analysis_exact_reconstructed", actual["contrast"] + "/" + field)
                    self.same(stored[field]["value"], float(rational), "supplement_analysis_fraction_decimal")
                for field in ("assignments", "extreme_assignments", "reject_at_05"):
                    self.same(stored.get(field), actual[field], "supplement_analysis_test_reconstructed", field)
                for field in ("lower", "upper"):
                    self.check(abs(stored["bootstrap_95"][field] - actual["bootstrap_95"][field]) < 1e-12,
                               "supplement_bootstrap_reconstructed", field)
        return primary

    def run(self):
        self.hashes_and_plan()
        parent_report = (base.load(self.parent_verification) if self.parent_verification is not None
                         else base.Audit(PARENT, phase="pilot").run())
        self.same(parent_report.get("passed"), True, "parent_independent_preflight_integrity")
        self.same(parent_report.get("pilot_gate", {}).get("pass"), True, "parent_independent_preflight_gate_pass")
        for spec in self.plan["validation"]:
            try:
                self.session(spec)
            except (ValueError, KeyError, TypeError, IndexError, OSError) as exc:
                self.check(False, "supplement_session_audit_exception", spec["session_id"] + ": " + repr(exc))
        inventory = super().inventory_and_budget()
        self.same(inventory["actor_calls"], 768, "exactly_768_actor_calls")
        self.same(inventory["judge_calls"], 96, "exactly_96_prefix_judges")
        self.same(inventory["retained_requests"], 864, "exactly_864_logical_requests")
        self.same(inventory["retained_attempts"], 864, "exactly_864_http_attempts")
        self.check(inventory["peak_accounted_usd"] <= Decimal("10.00000000001"),
                   "supplement_10_dollar_cap_at_every_reservation_event")
        self.check(inventory["accounted_including_unknown_cost_usd"] <= Decimal("10.00000000001"),
                   "supplement_final_separate_10_dollar_cap")
        self.check(not (self.root / "calls" / "pilot").exists() and
                   not (self.root / "calls" / "continuations").exists(), "no_extra_supplement_cohorts")
        completion_path = self.root / "validation_completion.json"
        if completion_path.exists():
            completion = base.load(completion_path)
            self.same(completion.get("supplement_cap_usd"), 10., "completed_supplement_cap")
            self.same(completion.get("aggregate_authorization_usd"), 35., "completed_aggregate_authorization")
            self.check(Decimal(str(completion.get("parent_budget_accounted_at_launch_usd", 1e9))) <= Decimal("25.00000000001"),
                       "parent_budget_within_own_authorization_at_launch")
        primary = self.primary()
        joint = {"checked": False, "reason": "No independently verified parent primary supplied."}
        if self.parent_verification is not None:
            joint = joint_correction(parent_report, primary)
            joint["checked"] = True
            joint["parent_verification_sha256"] = base.file_hash(self.parent_verification)
            analysis_path = self.root / "ANALYSIS.json"
            if analysis_path.exists():
                saved_joint = base.load(analysis_path).get("joint_holm5")
                if saved_joint is not None:
                    self.same(saved_joint.get("family_size"), 5, "joint_analysis_family_five")
                    self.same(len(saved_joint.get("contrasts", [])), 5, "joint_analysis_five_contrasts")
                    for expected, stored in zip(joint["contrasts"], saved_joint.get("contrasts", [])):
                        for field in ("study", "contrast", "reject_at_05"):
                            self.same(stored.get(field), expected[field], "joint_analysis_order_and_decision", field)
                        for field in ("raw_p", "holm5_p"):
                            self.same(rational(stored[field]), expected[field], "joint_holm5_independently_recomputed", field)
        return {"audit_version": 1, "generated_at": datetime.now(timezone.utc).isoformat(),
            "study": "negotiation-scaffolding supplement", "root": str(self.root),
            "passed": not self.failures, "verifier_sha256": base.file_hash(__file__),
            "parent_pure_verifier_sha256": base.file_hash(DEPENDENCY),
            "checks_executed": dict(self.checks), "failures": self.failures,
            "inventory": inventory, "primary": primary, "joint_holm5": joint,
            "finite_certificate": base.finite_certificate(), "sessions": self.sessions,
            "rounds": self.rounds, "calls": self.calls,
            "method": "Raw-wire independent reconstruction using explicitly hashed frozen parent pure checker; no runner/analyzer/client imports or API calls. New prompt and information interventions reconstructed independently.",
            "limits": ["Negotiation scaffolding is an explicit bundled prompt intervention; no unprompted-emergence or component-level causal claim.",
                "Numeric peer claims and prior settlement feedback remain visible when notes are withheld.",
                "Structural quote checks do not establish semantic acceptance; independent prefix review remains separate.",
                "Local timestamps/hashes are not external attestation; archive checks cannot prove no unrelated/deleted outside calls existed."]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=HERE)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--parent-verification", type=Path,
                        help="Verified parent ALL report for optional independent joint Holm5 check.")
    parser.add_argument("--release", action="store_true", help="Root authorizes reading completed live outcomes.")
    args = parser.parse_args()
    if not args.release:
        parser.error("--release is required; no live outcome files opened")
    report = base.jsonable(Audit(args.root, args.parent_verification).run())
    output = args.output_dir or args.root
    output.mkdir(parents=True, exist_ok=True)
    target = output / "INDEPENDENT_VERIFICATION.json"
    target.write_text(json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False) + "\n")
    print(json.dumps({"passed": report["passed"], "inventory": report["inventory"],
                      "failures": report["failures"], "report": str(target)}, indent=2))
    raise SystemExit(0 if report["passed"] else 1)


if __name__ == "__main__":
    main()
