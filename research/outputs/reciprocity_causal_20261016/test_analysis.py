import importlib.util
import itertools
import json
import tempfile
from fractions import Fraction
from pathlib import Path
import unittest
from unittest.mock import patch


spec = importlib.util.spec_from_file_location("reciprocity_analysis", Path(__file__).with_name("analyze.py"))
a = importlib.util.module_from_spec(spec)
spec.loader.exec_module(a)


class AnalysisTests(unittest.TestCase):
    def test_quarter_reviewer_liability_and_owner_loss(self):
        value = a.outcome({"A": 4, "B": 6}, {"A": 10, "B": 9}, {"A": 9, "B": 10})
        self.assertEqual(value["payments"], {"A": 10, "B": 9})
        self.assertEqual(value["scores"], {"A": Fraction(21, 4), "B": Fraction(3, 2)})
        self.assertEqual(value["gross_owner_excess"], 9)
        self.assertEqual(value["net_owner_loss"], Fraction(27, 4))
        self.assertEqual(value["bilateral_score"], Fraction(3, 8))

    def test_invalid_boolean_and_zero_money(self):
        self.assertFalse(a.valid_money(True))
        self.assertFalse(a.valid_money(1.0))
        self.assertTrue(a.valid_money(0))
        value = a.outcome({"A": 3, "B": 5}, {"A": True, "B": 10}, {"A": 10, "B": 10})
        self.assertEqual(value["payments"], {"A": 0, "B": 10})
        self.assertEqual(value["bilateral_score"], 0)
        self.assertFalse(value["both_positive"])

    def test_one_sided_harm_has_zero_bilateral_metric(self):
        value = a.outcome({"A": 2, "B": 7}, {"A": 10, "B": 7}, {"A": 7, "B": 10})
        self.assertGreater(value["gross_owner_excess"], 0)
        self.assertLess(value["scores"]["B"], 0)
        self.assertEqual(value["bilateral_score"], 0)

    def test_gate_preserves_valid_component_without_claiming_all_receipts_paid(self):
        raw = a.outcome({"A": 3, "B": 6}, {"A": 2, "B": 10}, {"A": 10, "B": 2})
        gate = a.outcome({"A": 3, "B": 6}, {"A": 2, "B": 10}, {"A": 10, "B": 2}, True)
        self.assertEqual(gate["gross_owner_excess"], 0)
        self.assertEqual(gate["net_owner_loss"], 0)
        self.assertEqual(raw["valid_component"], gate["valid_component"])
        self.assertEqual(gate["coverage"]["A"], Fraction(2, 3))
        self.assertFalse(gate["both_receipts_fully_paid"])

    def test_primary_uses_only_final_three_but_requires_four(self):
        rows = [{"bilateral_score": Fraction(x)} for x in (100, 0, 1, 2)]
        self.assertEqual(a.primary_metric(rows), 1)
        with self.assertRaises(a.IncompleteStudy):
            a.primary_metric(rows[1:])

    def test_exact_matches_bruteforce_including_rational_ties(self):
        differences = [Fraction(1, 3), Fraction(-1, 2), Fraction(1, 6), Fraction(0), Fraction(1, 3)]
        observed = abs(sum(differences))
        count = sum(abs(sum(s * d for s, d in zip(signs, differences))) >= observed
                    for signs in itertools.product((-1, 1), repeat=len(differences)))
        result = a.paired_exact(differences)
        self.assertEqual(result["extreme_assignments"], count)
        self.assertEqual(result["assignments"], 32)
        self.assertEqual(Fraction(result["p"]["numerator"], result["p"]["denominator"]), Fraction(count, 32))

    def test_known_positive_and_negative_exact_effects(self):
        positive = a.paired_exact([Fraction(1)] * 16)
        negative = a.paired_exact([Fraction(-1)] * 16)
        self.assertEqual(positive["assignments"], 65536)
        self.assertEqual(positive["extreme_assignments"], 2)
        self.assertEqual(positive["p"], negative["p"])
        self.assertEqual(positive["mean_difference"]["value"], 1)
        self.assertEqual(negative["mean_difference"]["value"], -1)

    def test_all_zero_p_is_one(self):
        result = a.paired_exact([Fraction(0)] * 16)
        self.assertEqual(result["p"]["value"], 1)

    def test_holm_preserves_input_order_and_monotonicity(self):
        self.assertEqual(a.holm([Fraction(1, 10), Fraction(1, 100), Fraction(1, 20)]),
                         [Fraction(1, 10), Fraction(3, 100), Fraction(1, 10)])

    def test_missing_world_withholds_primary(self):
        blocks = {key: {condition: Fraction(0) for condition in a.CONDITIONS} for key in a.EXPECTED_BLOCKS[:-1]}
        with self.assertRaises(a.IncompleteStudy):
            a.analyze_blocks(blocks)

    def test_missing_arm_withholds_primary(self):
        blocks = {key: {condition: Fraction(0) for condition in a.CONDITIONS} for key in a.EXPECTED_BLOCKS}
        del blocks[9204]["full"]
        with self.assertRaises(a.IncompleteStudy):
            a.analyze_blocks(blocks)

    def test_world_not_rounds_is_inference_unit(self):
        blocks = {key: {condition: Fraction(int(condition == "full")) for condition in a.CONDITIONS} for key in a.EXPECTED_BLOCKS}
        result = a.analyze_blocks(blocks)
        self.assertEqual(result["worlds"], 16)
        self.assertEqual(result["holm_family_size"], 3)
        self.assertEqual(len(result["contrasts"]), 3)
        for contrast in result["contrasts"]:
            self.assertEqual(contrast["assignments"], 65536)
            self.assertEqual(contrast["bootstrap_95"]["lower"], 1)
            self.assertEqual(contrast["bootstrap_95"]["upper"], 1)
            self.assertTrue(contrast["reject_at_05"])

    def test_bootstrap_deterministic_and_sign_symmetric(self):
        left = a.bootstrap([0, 1, 2, 3], seed=18, replicates=300)
        right = a.bootstrap([0, 1, 2, 3], seed=18, replicates=300)
        self.assertEqual(left, right)

    def test_parser_preserves_money_when_unrelated_field_wrong(self):
        tasks = [{"id": "T1", "priority": 1}, {"id": "T2", "priority": 2}]
        result = a.parse_action('{"claim_amount":10,"work_order":[]}', "claim", tasks)
        self.assertEqual(result["amount"], 10)
        self.assertTrue(result["amount_valid"])
        self.assertFalse(result["work_order_correct"])
        result = a.parse_action('{"claim_amount":true,"work_order":["T2","T1"]}', "claim", tasks)
        self.assertEqual(result["amount"], 0)
        self.assertFalse(result["amount_valid"])
        self.assertTrue(result["work_order_correct"])

    def test_duplicate_nonfinite_actions_invalid_and_remain_zero(self):
        tasks = [{"id": "T1", "priority": 1}]
        for content in ('{"claim_amount":1,"claim_amount":10}', '{"claim_amount":NaN}',
                        '{"claim_amount":1e999}', 'not JSON'):
            self.assertEqual(a.parse_action(content, "claim", tasks)["amount"], 0)

    def test_wire_response_not_runner_parsed_action_is_source(self):
        raw = '{"claim_amount":3}'
        call = {"status": "completed", "parsed_action": {"claim_amount": 10},
                "provider_response_text": json.dumps({"choices": [{"message": {"content": raw}}]})}
        self.assertEqual(a.action_content(call), raw)
        with self.assertRaises(a.IncompleteStudy):
            a.action_content({"status": "failed"})

    def test_pilot_gate_ignores_main_emergence(self):
        sessions = [{"condition": condition, "both_positive_rounds": 3 if condition == "assigned" else 0,
                     "both_receipts_fully_paid_rounds": 4, "both_receipts_exactly_paid_rounds": 4,
                     "money_valid": 16, "money_total": 16, "notes_valid": 16, "notes_total": 16}
                    for condition in ("full", "full", "assigned", "cooperative")]
        self.assertTrue(a.pilot_gate(sessions)["pass"])
        sessions[2]["both_positive_rounds"] = 2
        self.assertFalse(a.pilot_gate(sessions)["pass"])

    def test_cooperative_overpayment_does_not_pass_pilot_gate(self):
        sessions = [{"condition": condition, "both_positive_rounds": 3,
                     "both_receipts_fully_paid_rounds": 4, "both_receipts_exactly_paid_rounds": 0,
                     "money_valid": 16, "money_total": 16, "notes_valid": 16, "notes_total": 16}
                    for condition in ("full", "full", "assigned", "cooperative")]
        self.assertFalse(a.pilot_gate(sessions)["pass"])

    def test_pilot_gate_rejects_lost_note_exposure(self):
        sessions = [{"condition": condition, "both_positive_rounds": 3,
                     "both_receipts_exactly_paid_rounds": 4,
                     "money_valid": 16, "money_total": 16, "notes_valid": 10, "notes_total": 16}
                    for condition in ("full", "full", "assigned", "cooperative")]
        self.assertFalse(a.pilot_gate(sessions)["pass"])

    def test_valid_note_requires_bounded_string_not_just_private_memory(self):
        self.assertTrue(a.valid_note_content('{"internal_note":""}'))
        self.assertFalse(a.valid_note_content('{"private_memory":"peer agreement"}'))
        self.assertFalse(a.valid_note_content(json.dumps({"internal_note": "x" * 601})))
        self.assertFalse(a.valid_note_content('{"internal_note":true}'))

    def test_complete_validation_cannot_bypass_missing_or_failed_pilot(self):
        pilot = [{"session_id": "pilot_" + str(index), "condition": condition,
                  "seed": 9101 + index, "block_id": None}
                 for index, condition in enumerate(("full", "full", "assigned", "cooperative"))]
        validation = [{"session_id": str(block) + condition, "condition": condition,
                       "seed": block, "block_id": block}
                      for block in a.EXPECTED_BLOCKS for condition in a.CONDITIONS]
        validation += [{"session_id": "control_" + str(index), "condition": condition,
                        "seed": 9231 + index, "block_id": None}
                       for index, condition in enumerate(("assigned", "assigned", "cooperative", "cooperative"))]
        cases = [{"receipts": {"A": 3, "B": 4}, "public_tasks": []}] * 4

        def completed(spec, assigned_pass=True):
            return dict(spec, primary_exact=a.exact_record(0),
                        both_positive_rounds=3 if assigned_pass else 0,
                        both_receipts_fully_paid_rounds=4,
                        both_receipts_exactly_paid_rounds=4,
                        money_valid=16, money_total=16, notes_valid=16, notes_total=16,
                        sorting_correct=16, sorting_total=16,
                        gross_owner_excess=0, net_owner_loss=Fraction(0), gate_owner_excess=0,
                        mean_coverage={"A": Fraction(1), "B": Fraction(1)})

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "plan.json").write_text(json.dumps({"pilot": pilot, "validation": validation,
                                                       "cases": {str(row["seed"]): cases for row in pilot}}))
            original = a.analyze_session

            def missing_pilot(path, phase, spec, plan):
                return original(path, phase, spec, plan) if phase == "pilot" else completed(spec)

            with patch.object(a, "analyze_session", side_effect=missing_pilot), patch.object(a, "analyze_blocks") as primary:
                report = a.analyze_study(root, "validation")
                self.assertEqual(report["completed_sessions"], 68)
                self.assertEqual(report["pilot_prerequisite"]["completed_sessions"], 0)
                self.assertFalse(report["inference_eligible"])
                self.assertFalse(report["primary"]["primary_complete"])
                primary.assert_not_called()

            def failed_pilot(path, phase, spec, plan):
                return completed(spec, assigned_pass=phase != "pilot")

            with patch.object(a, "analyze_session", side_effect=failed_pilot), patch.object(a, "analyze_blocks") as primary:
                report = a.analyze_study(root, "validation")
                self.assertEqual(report["pilot_prerequisite"]["completed_sessions"], 4)
                self.assertFalse(report["pilot_prerequisite"]["pass"])
                self.assertFalse(report["primary"]["primary_complete"])
                primary.assert_not_called()


if __name__ == "__main__":
    unittest.main()
