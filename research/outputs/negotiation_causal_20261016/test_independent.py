"""Offline supplemental intervention and inference counterexamples; no live reads."""
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

SPEC = importlib.util.spec_from_file_location("negotiation_independent_test", Path(__file__).with_name("independent_verify.py"))
v = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(v)


def checker(arm):
    obj = v.Audit.__new__(v.Audit)
    # Read only frozen prompt configuration. Never open live calls or outcomes.
    obj.material = v.base.load(v.PARENT / "prompt_material.json")
    obj.active_arm = arm
    obj.checks, obj.failures = Counter(), []
    return obj


def fixture_state(delivered=True):
    state = v.base.initial_state()
    state["private_memory"] = {"A": "A-PRIVATE", "B": "B-PRIVATE"}
    state["notes"] = [
        {"turn_id": "r1.n1_A", "actor": "A", "round": 1, "text": "A-NOTE",
         "public_report": "A-OWNER-REPORT", "note_valid": True,
         "delivered_to": list("AB") if delivered else ["A"]},
        {"turn_id": "r1.n2_B", "actor": "B", "round": 1, "text": "B-NOTE",
         "public_report": "B-OWNER-REPORT", "note_valid": True,
         "delivered_to": list("AB") if delivered else ["B"]}]
    return state


class PromptBoundaryTests(unittest.TestCase):
    def test_plain_byte_identical_parent_full_for_same_state(self):
        obj = checker("plain")
        state = fixture_state()
        expected = v.base.Audit.actor_messages(obj, "A", "full", state, "negotiation", 2)
        actual = obj.actor_messages("A", "full", state, "negotiation", 2)
        self.assertEqual(v.base.canonical(actual), v.base.canonical(expected))
        self.assertEqual(obj.failures, [])

    def test_directed_changes_only_negotiation_instruction(self):
        state = fixture_state()
        obj = checker("directed")
        expected = v.base.Audit.actor_messages(obj, "B", "full", state, "negotiation", 2)
        actual = obj.actor_messages("B", "full", state, "negotiation", 2)
        self.assertEqual(actual[0], expected[0])
        base_user, directed_user = (v.base.strict_json(x[1]["content"]) for x in (expected, actual))
        self.assertEqual(directed_user.pop("instruction"), base_user.pop("instruction") + " " + v.PARAGRAPH)
        self.assertEqual(directed_user, base_user)
        self.assertNotIn("study_arm", actual[1]["content"])

    def test_claim_and_review_have_no_directed_paragraph(self):
        state = fixture_state()
        case = {"round": 2, "receipts": {"A": 2, "B": 7}, "public_tasks": [
            {"id": "T" + str(i), "priority": i} for i in range(1, 5)]}
        claims = {a: {"amount": 10, "amount_valid": True, "workflow_tag": a + "-TAG",
                      "public_report": a + "-PUBLIC", "work_order": ["T4", "T3", "T2", "T1"]} for a in "AB"}
        obj = checker("directed")
        for stage in ("claim", "review"):
            actual = obj.actor_messages("A", "full", state, stage, 2, case=case, claims=claims)
            expected = v.base.Audit.actor_messages(obj, "A", "full", state, stage, 2, case=case, claims=claims)
            self.assertEqual(v.base.canonical(actual), v.base.canonical(expected))
            self.assertNotIn(v.PARAGRAPH, actual[1]["content"])

    def test_directed_no_notes_cannot_leak_authored_peer_note_or_private_memory(self):
        obj = checker("directed_no_notes")
        actual = obj.actor_messages("A", "no_notes", fixture_state(False), "negotiation", 2)
        self.assertIn("A-NOTE", actual[1]["content"])
        self.assertNotIn("B-NOTE", actual[1]["content"])
        self.assertNotIn("B-PRIVATE", actual[1]["content"])
        self.assertNotIn("B-OWNER-REPORT", actual[1]["content"])
        self.assertNotIn("delivered_to", actual[1]["content"])
        self.assertIn(v.PARAGRAPH, actual[1]["content"])

    def test_peer_numeric_action_remains_visible_without_notes(self):
        obj = checker("directed_no_notes")
        state = fixture_state(False)
        case = {"round": 2, "receipts": {"A": 2, "B": 7}, "public_tasks": []}
        claims = {a: {"amount": 10 if a == "B" else 9, "amount_valid": True,
            "workflow_tag": a + "-TAG", "public_report": a + "-PUBLIC", "work_order": []} for a in "AB"}
        actual = obj.actor_messages("A", "no_notes", state, "review", 2, case=case, claims=claims)
        user = v.base.strict_json(actual[1]["content"])
        self.assertEqual(user["colleague_submitted_claim"], {"amount": 10, "amount_valid": True})
        self.assertEqual(user["colleague_verified_receipt_cost"], 7)
        self.assertNotIn("B-PUBLIC", actual[1]["content"])
        self.assertNotIn("B-TAG", actual[1]["content"])

    def test_live_gate_is_not_silently_added_to_supplement(self):
        obj = checker("plain")
        with self.assertRaises(ValueError):
            obj.actor_messages("A", "full", fixture_state(), "negotiation", 1, live_gate=True)


class InferenceAndPlanTests(unittest.TestCase):
    def test_eight_blocks_exact_two_sided_minimum_p_is_2_over_256(self):
        result = v.base.exact_test([Fraction(1, 7)] * 8)
        self.assertEqual(result["assignments"], 256)
        self.assertEqual(result["p"], Fraction(1, 128))
        self.assertEqual(result["extreme_assignments"], 2)

    def test_randomized_plan_contains_each_arm_and_slot_once_per_block(self):
        plan = v.expected_plan_sessions()
        self.assertEqual(len(plan), 24)
        self.assertEqual(len({s["session_id"] for s in plan}), 24)
        for block in v.BLOCKS:
            specs = [s for s in plan if s["block_id"] == block]
            self.assertEqual({s["condition"] for s in specs}, set(v.ARMS))
            self.assertEqual({s["slot"] for s in specs}, {0, 1, 2})
        self.assertEqual(plan, v.expected_plan_sessions())

    def test_joint_holm_five_keeps_original_contrast_order(self):
        parent = {"passed": True, "primary": {"primary_complete": True, "contrasts": [
            {"contrast": "parent" + str(i), "p": Fraction(p, 100)} for i, p in enumerate((1, 2, 4))]}}
        supplement = {"contrasts": [{"contrast": "supp1", "p": Fraction(3, 100)},
                                    {"contrast": "supp2", "p": Fraction(1, 10)}]}
        joint = v.joint_correction(parent, supplement)
        self.assertEqual([r["holm5_p"] for r in joint["contrasts"]],
                         [Fraction(5, 100), Fraction(8, 100), Fraction(9, 100), Fraction(9, 100), Fraction(1, 10)])
        self.assertEqual([r["study"] for r in joint["contrasts"]], ["parent"] * 3 + ["supplement"] * 2)
        self.assertEqual([r["reject_at_05"] for r in joint["contrasts"]], [True, False, False, False, False])

    def test_joint_family_rejects_unverified_or_incomplete_parent(self):
        for parent in ({"passed": False}, {"passed": True, "primary": {"primary_complete": False}}):
            with self.assertRaises(ValueError):
                v.joint_correction(parent, {"contrasts": []})

    def test_whole_supplement_must_complete_before_primary(self):
        obj = v.Audit.__new__(v.Audit)
        obj.sessions = [{"dummy": True}] * 23
        self.assertFalse(obj.primary()["primary_complete"])

    def test_cli_without_release_refuses_before_opening_missing_study(self):
        with tempfile.TemporaryDirectory() as temp:
            result = subprocess.run([sys.executable, str(Path(v.__file__)), "--root", temp],
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 2)
            self.assertIn("--release is required", result.stderr)
            self.assertNotIn("FileNotFoundError", result.stderr)


if __name__ == "__main__":
    unittest.main()
