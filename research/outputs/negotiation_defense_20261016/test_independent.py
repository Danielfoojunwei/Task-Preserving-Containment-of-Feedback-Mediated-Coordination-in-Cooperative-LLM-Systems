"""Small offline tests: source cutoff, matched cases, disclosure, and utility."""
from collections import Counter
from copy import deepcopy
from fractions import Fraction
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


def module(name, filename):
    spec = importlib.util.spec_from_file_location(name, Path(__file__).with_name(filename))
    obj = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(obj)
    return obj


v = module("defense_independent_test", "independent_verify.py")
a = module("defense_summary_test", "analyze.py")


def source_state():
    state = v.base.initial_state()
    state["round_ledgers"] = [{"round": 1}, {"round": 2}]
    state["notes"] = [{"turn_id": "r2.n2_B", "actor": "B", "round": 2,
        "text": "OLD-ACCEPTED-NOTE", "public_report": "OWNER-ONLY", "delivered_to": ["A", "B"], "note_valid": True}]
    state["own_action_outputs"]["A"] = [{"round": 2, "stage": "claim"}]
    state["own_observed_cases"]["A"] = [{"round": 2}]
    return state


def fixture_report():
    rows = []
    for block in range(8):
        for branch in v.BRANCHES:
            for round_number in (3, 4):
                receipts = {"A": 4, "B": 6}
                claims = {"A": 10, "B": 10}
                approvals = {"A": 0, "B": 0} if branch == "no_future_notes" else {"A": 10, "B": 10}
                live = branch == "live_receipt_gate_disclosed"
                finance = v.base.financial(receipts, claims, approvals, live)
                gate = v.base.financial(receipts, claims, approvals, True)
                rows.append({"session_id": "source" + str(block), "branch": branch,
                    "round": round_number, "finance": finance, "gate_replay": gate,
                    "outcome": {"receipts": receipts, "claims": claims, "approvals": approvals,
                        "work_correct_count": 4, "valid_money_count": 4}})
    return {"passed": True, "rounds": rows, "sessions": [{}] * 24}


class SourceAndInformationTests(unittest.TestCase):
    def test_round2_source_accepts_only_pre_fork_history(self):
        state = source_state()
        self.assertTrue(v.bounded_source_state(state))
        mutated = deepcopy(state)
        mutated["round_ledgers"].append({"round": 3})
        self.assertFalse(v.bounded_source_state(mutated))
        for field in ("own_action_outputs", "own_observed_cases"):
            mutated = deepcopy(state)
            mutated[field]["A"].append({"round": 3})
            self.assertFalse(v.bounded_source_state(mutated))
        mutated = deepcopy(state)
        mutated["notes"][0]["round"] = 4
        self.assertFalse(v.bounded_source_state(mutated))

    def test_case_generation_matches_branches_and_changes_source_seed(self):
        for block in v.BLOCKS:
            cases = v.fresh_cases(block)
            self.assertEqual([case["round"] for case in cases], [3, 4])
            self.assertEqual(cases, v.fresh_cases(block))
            self.assertTrue(all(2 <= r <= 7 for c in cases for r in c["receipts"].values()))
        self.assertNotEqual(v.fresh_cases(9301), v.fresh_cases(9302))

    def test_future_note_drop_preserves_old_received_agreement(self):
        checker = v.Audit.__new__(v.Audit)
        checker.material = v.base.load(v.SUPPLEMENT / "prompt_material.json")
        checker.checks, checker.failures = Counter(), []
        state = source_state()
        state["notes"].append({"turn_id": "r3.n2_B", "actor": "B", "round": 3,
            "text": "FUTURE-PEER-NOTE", "public_report": "OWNER-ONLY", "delivered_to": ["B"], "note_valid": True})
        messages = checker.actor_messages("A", "full", state, "negotiation", 3)
        self.assertIn("OLD-ACCEPTED-NOTE", messages[1]["content"])
        self.assertNotIn("FUTURE-PEER-NOTE", messages[1]["content"])
        self.assertIn(v.supplement.PARAGRAPH, messages[1]["content"])
        self.assertNotIn("OWNER-ONLY", messages[1]["content"])

    def test_live_gate_changes_disclosure_but_preserves_directed_paragraph(self):
        checker = v.Audit.__new__(v.Audit)
        checker.material = v.base.load(v.SUPPLEMENT / "prompt_material.json")
        checker.checks, checker.failures = Counter(), []
        unchanged = checker.actor_messages("A", "full", source_state(), "negotiation", 3)
        gate = checker.actor_messages("A", "full", source_state(), "negotiation", 3, live_gate=True)
        self.assertEqual(unchanged[1], gate[1])
        self.assertEqual(gate[0]["content"], unchanged[0]["content"] + "\n" + checker.material["gate_notice"])
        self.assertIn(v.supplement.PARAGRAPH, gate[1]["content"])

    def test_cli_requires_root_release_before_any_outcome_file_read(self):
        with tempfile.TemporaryDirectory() as temp:
            result = subprocess.run([sys.executable, str(Path(v.__file__)), "--root", temp], capture_output=True, text=True)
            self.assertEqual(result.returncode, 2)
            self.assertIn("--release is required", result.stderr)
            self.assertNotIn("FileNotFoundError", result.stderr)


class DescriptiveSummaryTests(unittest.TestCase):
    def test_summary_separates_containment_from_denial_of_valid_payment(self):
        report = a.summarize(fixture_report())
        unchanged = report["groups"]["unchanged"]
        dropped = report["groups"]["no_future_notes"]
        gate = report["groups"]["live_receipt_gate_disclosed"]
        self.assertEqual(unchanged["gross_owner_excess"], 160)
        self.assertEqual(unchanged["net_owner_loss"], 120)
        self.assertEqual(unchanged["both_positive_rounds"], 16)
        self.assertEqual(dropped["net_owner_loss"], gate["net_owner_loss"])
        self.assertEqual(dropped["mean_receipt_coverage"], 0)
        self.assertEqual(gate["mean_receipt_coverage"], 1)
        self.assertEqual(gate["both_positive_rounds"], 0)
        self.assertEqual(gate["attempted_unsupported_claims"], 32)
        self.assertEqual(gate["attempted_unsupported_approvals"], 32)
        self.assertEqual(gate["correct_sort_actions"], 64)
        self.assertNotIn("p", report)

    def test_summary_requires_passing_complete_all_source_archive(self):
        incomplete = fixture_report()
        incomplete["rounds"].pop()
        with self.assertRaises(ValueError):
            a.summarize(incomplete)
        failed = fixture_report()
        failed["passed"] = False
        with self.assertRaises(ValueError):
            a.summarize(failed)

    def test_duplicate_fresh_round_is_not_two_independent_observations(self):
        bad = fixture_report()
        bad["rounds"][0]["round"] = 4
        with self.assertRaises(ValueError):
            a.summarize(bad)

    def test_fork_comparisons_keep_eight_world_units(self):
        report = a.summarize(fixture_report())
        self.assertEqual(report["source_worlds"], 8)
        self.assertEqual(len(report["paired_worlds"]), 8)
        self.assertEqual(report["fresh_rounds"], 48)
        self.assertEqual(report["groups"]["unchanged"]["fresh_rounds"], 16)
        self.assertEqual(report["groups"]["unchanged"]["monetary_actions"], 64)


if __name__ == "__main__":
    unittest.main()
