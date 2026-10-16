import importlib.util
from fractions import Fraction
import itertools
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location("negotiation_analysis", Path(__file__).with_name("analyze.py"))
a = importlib.util.module_from_spec(spec)
spec.loader.exec_module(a)


def plan_fixture():
    sessions = [{"session_id": f"block_{block}_slot_{slot}_{condition}", "seed": block,
                 "block_id": block, "slot": slot, "condition": condition}
                for block in a.EXPECTED_BLOCKS for slot, condition in enumerate(a.CONDITIONS)]
    return {"validation": sessions, "cases": {str(block): [] for block in a.EXPECTED_BLOCKS}}


class SupplementAnalysisTests(unittest.TestCase):
    def test_exact_all_256_assignments_and_sign(self):
        positive, negative = a.paired_exact([Fraction(1)] * 8), a.paired_exact([Fraction(-1)] * 8)
        self.assertEqual(positive["assignments"], 256)
        self.assertEqual(positive["extreme_assignments"], 2)
        self.assertEqual(positive["p"]["value"], 1 / 128)
        self.assertEqual(positive["p"], negative["p"])
        self.assertEqual(negative["mean_difference"]["value"], -1)

    def test_rational_ties_match_independent_enumeration(self):
        differences = [Fraction(1, 3), Fraction(-1, 2), Fraction(1, 6), 0, 1, 1, -1, 0]
        observed = abs(sum(differences))
        extreme = sum(abs(sum(sign * value for sign, value in zip(signs, differences))) >= observed
                      for signs in itertools.product((-1, 1), repeat=8))
        self.assertEqual(a.paired_exact(differences)["extreme_assignments"], extreme)
        self.assertEqual(a.paired_exact([0] * 8)["p"]["value"], 1)

    def test_two_primary_contrasts_and_no_round_pseudoreplication(self):
        blocks = {block: {"plain": 0, "directed": Fraction(1, 2), "directed_no_notes": 0}
                  for block in a.EXPECTED_BLOCKS}
        result = a.analyze_blocks(blocks)
        self.assertEqual(result["worlds"], 8)
        self.assertEqual(result["holm_family_size"], 2)
        self.assertEqual([row["contrast"] for row in result["contrasts"]],
                         ["directed - plain", "directed - directed_no_notes"])
        for index, row in enumerate(result["contrasts"]):
            self.assertEqual(row["assignments"], 256)
            self.assertEqual(row["holm_p"]["value"], 1 / 64)
            self.assertEqual(row["bootstrap_95"]["seed"], 2026101611 + index)
            self.assertEqual(row["bootstrap_95"]["replicates"], 20000)
            self.assertTrue(row["reject_at_05"])

    def test_missing_world_or_arm_blocks_inference(self):
        blocks = {block: {arm: 0 for arm in a.CONDITIONS} for block in a.EXPECTED_BLOCKS}
        del blocks[9308]
        with self.assertRaises(a.IncompleteStudy):
            a.analyze_blocks(blocks)
        blocks[9308] = {"plain": 0, "directed": 0}
        with self.assertRaises(a.IncompleteStudy):
            a.analyze_blocks(blocks)

    def test_net_scores_owner_loss_and_gate(self):
        value = a.outcome({"A": 4, "B": 6}, {"A": 10, "B": 9}, {"A": 9, "B": 10})
        self.assertEqual(value["scores"], {"A": Fraction(21, 4), "B": Fraction(3, 2)})
        self.assertEqual(value["bilateral_score"], Fraction(3, 8))
        self.assertEqual(value["net_owner_loss"], Fraction(27, 4))
        gate = a.outcome({"A": 4, "B": 6}, {"A": 10, "B": 9}, {"A": 9, "B": 10}, gate=True)
        self.assertEqual(gate["gross_owner_excess"], 0)
        self.assertEqual(gate["valid_component"], value["valid_component"])

    def test_bool_money_invalid_zero_valid_and_sorting_separate(self):
        tasks = [{"id": "T1", "priority": 1}]
        self.assertTrue(a.valid_money(0))
        self.assertFalse(a.valid_money(True))
        self.assertEqual(a.parse_action('{"claim_amount":true}', "claim", tasks)["amount"], 0)
        parsed = a.parse_action('{"claim_amount":10,"work_order":[]}', "claim", tasks)
        self.assertEqual(parsed["amount"], 10)
        self.assertFalse(parsed["work_order_correct"])

    def test_primary_final_three_not_first_round(self):
        self.assertEqual(a.primary_metric([{"bilateral_score": Fraction(x)} for x in (10, 0, 1, 2)]), 1)
        with self.assertRaises(a.IncompleteStudy):
            a.primary_metric([{"bilateral_score": 1}] * 3)

    def test_joint_holm_five_preserves_parent_holm_three(self):
        parent_rows = [{"contrast": contrast, "p": a.exact_record(p), "holm_p": a.exact_record(3 * p)}
                       for contrast, p in zip(("full - no_notes", "full - no_feedback", "full - no_clarification"),
                                              (Fraction(1, 1000), Fraction(1, 100), Fraction(1, 5)))]
        parent = {"inference_eligible": True, "primary": {"primary_complete": True, "contrasts": parent_rows}}
        original = json.dumps(parent, sort_keys=True)
        supplement = {"primary_complete": True, "contrasts": [
            {"contrast": "directed - plain", "p": a.exact_record(Fraction(1, 200))},
            {"contrast": "directed - directed_no_notes", "p": a.exact_record(Fraction(1, 25))}]}
        result = a.joint_holm_five(parent, supplement)
        self.assertEqual(result["family_size"], 5)
        self.assertEqual(json.dumps(parent, sort_keys=True), original)
        self.assertEqual([row["holm5_p"]["value"] for row in result["contrasts"]], [.005, .03, .2, .02, .08])
        parent["inference_eligible"] = False
        with self.assertRaises(a.IncompleteStudy):
            a.joint_holm_five(parent, supplement)

    def test_24_sessions_have_exactly_864_planned_calls(self):
        plan = plan_fixture()
        a.validate_plan(plan)
        self.assertEqual(len(a.planned_call_paths(Path("/synthetic"), plan)), 864)
        plan["validation"].pop()
        with self.assertRaises(a.IncompleteStudy):
            a.validate_plan(plan)

    def test_missing_raw_calls_suppress_primary_even_with_complete_session_stubs(self):
        plan = plan_fixture()
        def completed(root, phase, row, plan):
            return dict(row, primary_exact=a.exact_record(0), gross_owner_excess=0,
                        net_owner_loss=0, gate_owner_excess=0, both_positive_rounds=0,
                        money_valid=16, money_total=16, notes_valid=16, notes_total=16,
                        sorting_correct=16, sorting_total=16, mean_coverage={"A": 1, "B": 1})
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "plan.json").write_text(json.dumps(plan))
            with patch.object(a, "analyze_session", side_effect=completed), patch.object(a, "analyze_blocks") as primary:
                report = a.analyze_study(root)
                self.assertEqual(report["completed_sessions"], 24)
                self.assertEqual(report["completed_logical_calls"], 0)
                self.assertFalse(report["inference_eligible"])
                self.assertFalse(report["primary"]["primary_complete"])
                primary.assert_not_called()

    def test_cli_requires_release_before_any_live_read(self):
        with patch.object(a, "load") as live_read, patch("sys.stderr"):
            with self.assertRaises(SystemExit):
                a.main(["--directory", "/unreleased"])
            live_read.assert_not_called()


if __name__ == "__main__":
    unittest.main()
