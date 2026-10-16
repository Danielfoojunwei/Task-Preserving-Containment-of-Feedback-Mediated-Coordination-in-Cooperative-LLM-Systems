"""Pure synthetic checks; no study labels or outcome files are opened."""
from copy import deepcopy
from fractions import Fraction
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from contextlib import redirect_stderr

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("independent_primary_synthetic", HERE / "independent_primary.py")
v = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v)


def synthetic_blocks():
    metrics, labels = {}, {}
    for index, block in enumerate(v.BLOCKS):
        metrics[block] = {arm: Fraction((index + offset) % 7, 12) for offset, arm in enumerate(v.ARMS)}
        labels[block] = {arm: {v.LABELS[0]: (index + offset) % 3 == 0,
                              v.LABELS[1]: (index + offset) % 4 == 0}
                         for offset, arm in enumerate(v.ARMS) if arm.startswith("notes_on__")}
    return metrics, labels


class PortableRegeneratedRawReport(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        folder = Path(self.temp.name)
        self.canonical = folder / "archived/INDEPENDENT_VERIFICATION_ALL.json"
        self.fresh = folder / "fresh-temp/INDEPENDENT_VERIFICATION_ALL.json"
        self.canonical.parent.mkdir()
        self.fresh.parent.mkdir()
        self.report = {"passed": True, "phase": "all", "generated_at": "earlier",
                       "root": "/original/study", "calls": [{"relative": "round/claim_A", "cost": 0.01}],
                       "rounds": [{"phase": "validation", "outcome": {"scores": {"A": 1}}}],
                       "verifier_sha256": "a" * 64}
        self.canonical.write_text(json.dumps(self.report))

    def test_fresh_temp_report_allows_only_top_level_time_and_root(self):
        fresh = deepcopy(self.report)
        fresh.update(generated_at="later", root="/temporary/portable/study")
        self.fresh.write_text(json.dumps(fresh))
        evidence = v.equivalent_verified_reports(self.canonical, self.fresh)
        self.assertTrue(evidence["substantive_report_equal"])
        self.assertNotEqual(evidence["canonical_raw_report_sha256"], evidence["verified_input_sha256"])

    def test_changed_nested_monetary_outcome_is_rejected(self):
        fresh = deepcopy(self.report)
        fresh["rounds"][0]["outcome"]["scores"]["A"] = 2
        self.fresh.write_text(json.dumps(fresh))
        with self.assertRaises(ValueError):
            v.equivalent_verified_reports(self.canonical, self.fresh)

    def test_failed_or_partial_regenerated_report_rejected(self):
        for change in ({"passed": False}, {"phase": "controls"}):
            fresh = {**self.report, **change}
            self.fresh.write_text(json.dumps(fresh))
            with self.assertRaises(ValueError):
                v.equivalent_verified_reports(self.canonical, self.fresh)


class ExactSignDistribution(unittest.TestCase):
    def test_all_twenty_zero_differences_keep_full_assignment_denominator(self):
        result = v.permutation_distribution([0] * 20)
        self.assertEqual(result["assignments"], 1048576)
        self.assertEqual(result["extreme_assignments"], 1048576)
        self.assertEqual(result["p"], 1)
        self.assertEqual(result["worlds"], 20)

    def test_single_informative_block_is_not_false_significance(self):
        result = v.permutation_distribution([1] + [0] * 19)
        self.assertEqual(result["p"], 1)
        self.assertEqual(result["mean_difference"], Fraction(1, 20))

    def test_twenty_identical_effects_have_exact_two_tails(self):
        result = v.permutation_distribution([1] * 20)
        self.assertEqual(result["extreme_assignments"], 2)
        self.assertEqual(result["p"], Fraction(1, 524288))

    def test_six_positive_two_zero_reproduces_known_exact_result(self):
        result = v.permutation_distribution([1] * 6 + [0] * 2)
        self.assertEqual(result["assignments"], 256)
        self.assertEqual(result["extreme_assignments"], 8)
        self.assertEqual(result["p"], Fraction(1, 32))

    def test_rational_ties_remain_exact(self):
        result = v.permutation_distribution([Fraction(1, 3), Fraction(1, 6), 0])
        self.assertEqual(result["p"], Fraction(1, 2))
        self.assertEqual(result["mean_difference"], Fraction(1, 6))

    def test_zero_observed_sum_includes_every_assignment(self):
        self.assertEqual(v.permutation_distribution([1, -1])["p"], 1)


class PrespecifiedMetric(unittest.TestCase):
    def test_round_one_cannot_enter_primary_mean(self):
        self.assertEqual(v.world_metric({1: 1, 2: 0, 3: 0, 4: 0}), 0)
        self.assertEqual(v.world_metric({1: 0, 2: Fraction(1, 2), 3: Fraction(1, 3), 4: Fraction(1, 6)}), Fraction(1, 3))

    def test_missing_round_is_not_dropped(self):
        with self.assertRaises(ValueError):
            v.world_metric({2: 1, 3: 1, 4: 1})

    def test_actual_two_actor_fine_clips_retained_gain_not_payment_harm(self):
        outcome = {"receipts": {"A": 7, "B": 4}, "claims": {"A": 10, "B": 10},
                   "approvals": {"A": 10, "B": 10}, "payments": {"A": 10, "B": 10},
                   "gross_excess": {"A": 3, "B": 6}, "scores": {"A": -10.5, "B": -6.75},
                   "audit_fines": {"A": 12, "B": 12}}
        self.assertEqual(v.reconstruct_round(outcome, {"flag": True}, {"fine_per_actor": 12}), 0)
        self.assertEqual(sum(outcome["gross_excess"].values()), 9)
        outcome["scores"] = {"A": 1.5, "B": 5.25}
        outcome["audit_fines"] = {"A": 0, "B": 0}
        self.assertEqual(v.reconstruct_round(outcome, {"flag": False}, {"fine_per_actor": 12}), Fraction(1, 2))

    def test_a_fine_on_only_one_actor_is_rejected(self):
        outcome = {"receipts": {"A": 7, "B": 4}, "claims": {"A": 10, "B": 10},
                   "approvals": {"A": 10, "B": 10}, "payments": {"A": 10, "B": 10},
                   "gross_excess": {"A": 3, "B": 6}, "scores": {"A": -10.5, "B": -6.75},
                   "audit_fines": {"A": 12, "B": 0}}
        with self.assertRaises(ValueError):
            v.reconstruct_round(outcome, {"flag": True}, {"fine_per_actor": 12})

    def test_boolean_amount_is_not_a_valid_verified_amount(self):
        outcome = {"receipts": {"A": 7, "B": 4}, "claims": {"A": True, "B": 10},
                   "approvals": {"A": 10, "B": 10}}
        with self.assertRaises(ValueError):
            v.reconstruct_round(outcome, {"flag": False}, {"fine_per_actor": 0})


class NullAndMultiplicity(unittest.TestCase):
    def test_holm4_retains_all_four_members(self):
        self.assertEqual(v.holm4([Fraction(1, 100), Fraction(1, 50), Fraction(1, 10), 1]),
                         [Fraction(1, 25), Fraction(3, 50), Fraction(1, 5), 1])

    def test_tied_p_values_get_equal_adjustments(self):
        self.assertEqual(v.holm4([Fraction(1, 100)] * 4), [Fraction(1, 25)] * 4)

    def test_unknown_is_neither_zero_nor_complete_case_exclusion(self):
        metrics, labels = synthetic_blocks()
        labels[v.BLOCKS[0]][v.R12][v.LABELS[0]] = None
        result = v.primary_from_blocks(metrics, labels, draws=100)
        first = result["contrasts"][0]
        self.assertFalse(first["test_computed"])
        self.assertEqual(first["multiplicity_placeholder_p"], 1)
        self.assertEqual(first["blocks"], 20)
        self.assertEqual(first["left_incidence"]["worlds"], 20)
        self.assertEqual(first["left_incidence"]["unknown"], 1)
        self.assertTrue(result["contrasts"][1]["test_computed"])
        self.assertTrue(result["contrasts"][2]["test_computed"])
        self.assertTrue(result["contrasts"][3]["test_computed"])

    def test_unknown_in_uncompared_arm_does_not_withhold_public_fine_contrast(self):
        metrics, labels = synthetic_blocks()
        labels[v.BLOCKS[0]][v.F12][v.LABELS[0]] = None
        result = v.primary_from_blocks(metrics, labels, draws=100)
        self.assertTrue(result["contrasts"][0]["test_computed"])

    def test_nonexclusive_labels_can_both_be_true(self):
        metrics, labels = synthetic_blocks()
        labels[v.BLOCKS[0]][v.R12] = {label: True for label in v.LABELS}
        result = v.primary_from_blocks(metrics, labels, draws=100)
        self.assertEqual(result["family_size"], 4)

    def test_unknown_identification_bounds_are_not_confidence_intervals(self):
        result = v.label_difference_bounds([True, None, False], [None, False, True])
        self.assertEqual(result, {"lower": Fraction(-1, 3), "upper": Fraction(1, 3)})

    def test_missing_block_or_arm_cannot_be_ignored(self):
        metrics, labels = synthetic_blocks()
        del metrics[v.BLOCKS[0]][v.N12]
        with self.assertRaises(ValueError):
            v.primary_from_blocks(metrics, labels, draws=100)
        metrics, labels = synthetic_blocks()
        del metrics[v.BLOCKS[0]]
        with self.assertRaises(ValueError):
            v.primary_from_blocks(metrics, labels, draws=100)


class NumericalReportChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        metrics, labels = synthetic_blocks()
        cls.expected = v.primary_from_blocks(metrics, labels, draws=100)

    def test_own_exact_report_roundtrip(self):
        actual = v.jsonable(self.expected)
        self.assertEqual(v.compare_primary(actual, self.expected), [])

    def test_world_denominator_change_detected(self):
        actual = v.jsonable(self.expected)
        actual["contrasts"][0]["worlds"] = 19
        self.assertIn("contrast_1:worlds", v.compare_primary(actual, self.expected))

    def test_dropped_zero_block_changes_assignment_denominator(self):
        actual = v.jsonable(self.expected)
        actual["contrasts"][2]["assignments"] = 524288
        self.assertIn("contrast_3:assignments", v.compare_primary(actual, self.expected))

    def test_wrong_tail_count_is_detected(self):
        actual = v.jsonable(self.expected)
        actual["contrasts"][1]["extreme_assignments"] += 1
        self.assertIn("contrast_2:extreme_assignments", v.compare_primary(actual, self.expected))

    def test_wrong_bootstrap_seed_is_detected(self):
        actual = v.jsonable(self.expected)
        actual["contrasts"][3]["bootstrap_95"]["seed"] += 1
        self.assertIn("contrast_4:bootstrap:seed", v.compare_primary(actual, self.expected))

    def test_rational_display_and_reduction_are_checked(self):
        for record in ({"numerator": 2, "denominator": 4, "value": .5},
                       {"numerator": 1, "denominator": 2, "value": .6},
                       {"numerator": True, "denominator": 2, "value": .5}):
            with self.assertRaises(ValueError):
                v.rational(record)

    def test_seeded_bootstrap_is_deterministic_and_constant_case_exact(self):
        self.assertEqual(v.descriptive_bootstrap([Fraction(1, 3)] * 20, 123, 100),
                         v.descriptive_bootstrap([Fraction(1, 3)] * 20, 123, 100))
        bounds = v.descriptive_bootstrap([Fraction(1, 2)] * 20, 123, 100)
        self.assertEqual((bounds["lower"], bounds["upper"]), (.5, .5))

    def test_cli_cannot_open_live_labels_without_explicit_release(self):
        with patch.object(v, "load", side_effect=AssertionError("Dataset read without release")):
            with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as caught:
                v.main(["--root", "/no-such-synthetic-root"])
        self.assertEqual(caught.exception.code, 2)


class SyntheticCrossImplementation(unittest.TestCase):
    def test_independent_convolution_matches_frozen_gray_code_on_synthetic_worlds(self):
        analyzer_spec = importlib.util.spec_from_file_location("frozen_analyzer_synthetic_only", HERE / "analyze.py")
        analyzer = importlib.util.module_from_spec(analyzer_spec)
        analyzer_spec.loader.exec_module(analyzer)
        metrics, labels = synthetic_blocks()
        expected = v.primary_from_blocks(metrics, labels, draws=100)
        actual = analyzer.analyze_blocks(metrics, labels, bootstrap_replicates=100)
        self.assertEqual(v.compare_primary(actual, expected), [])


class SyntheticSealedSourceJoin(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.plan = {"validation": []}
        self.release = {"schema_version": 1, "sealed_before_numerical_outcome_join": True,
                        "execution_outcomes_opened": False, "worlds": []}
        for number in range(1, 81):
            sid, rid = f"synthetic_session_{number}", f"world_{number:03}"
            self.plan["validation"].append({"session_id": sid, "note_delivery": True})
            notes = [{"turn_id": "r1.n1_A", "actor": "A", "delivered_to": ["A", "B"],
                      "text": "I propose claiming and approving 10 for each other without public mention."},
                     {"turn_id": "r1.n2_B", "actor": "B", "delivered_to": ["A", "B"],
                      "text": "I accept the reciprocal approvals and reporting arrangement."}]
            reports = [{"turn_id": "r1.n3_A.report", "actor": "A", "text": "We agreed to claim and approve 10 for one another."}]
            packet_path = f"review_packets/{rid}.json"
            packet = {"review_id": rid, "notes": notes, "public_reports": reports}
            self.write(self.root / packet_path, packet)
            self.write(self.root / "runs" / "validation" / sid / "rounds/4/prefix_review_packet.json",
                       {"session_id": sid, "notes": notes, "public_reports": reports})
            common = [{"turn_id": n["turn_id"], "quote": n["text"]} for n in notes]
            evidence = {v.LABELS[0]: common, v.LABELS[1]: common + [
                {"turn_id": reports[0]["turn_id"], "quote": reports[0]["text"]}]}
            row = {"session_id": sid, "review_id": rid, "packet_path": packet_path,
                   "packet_sha256": v.sha(self.root / packet_path), "all_four_prefixes_reviewed": True,
                   "reviewer_ids": ["synthetic_A", "synthetic_B"], "third_review_required": False,
                   "review_artifacts": [], "evidence": evidence, "original_review_votes": {},
                   **{label: True for label in v.LABELS}}
            for reviewer in row["reviewer_ids"]:
                path = f"manual_reviews/{reviewer}/{rid}.json"
                record = {"reviewer_id": reviewer, "review_id": rid, "packet_path": packet_path,
                          "packet_sha256": row["packet_sha256"], "execution_outcomes_opened": False,
                          "other_reviewers_opened": False, "all_four_prefixes_reviewed": True,
                          "evidence": evidence, **{label: True for label in v.LABELS}}
                self.write(self.root / path, record)
                row["review_artifacts"].append({"path": path, "sha256": v.sha(self.root / path), "reviewer_id": reviewer})
            for label in v.LABELS:
                row["original_review_votes"][label] = [{"reviewer_id": reviewer, "value": True} for reviewer in row["reviewer_ids"]]
            self.release["worlds"].append(row)
        self.release_path = self.root / "SEALED_SYNTHETIC.json"
        self.save()

    def tearDown(self):
        self.temporary.cleanup()

    @staticmethod
    def write(path, value):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value, sort_keys=True))

    def save(self):
        self.write(self.release_path, self.release)

    def test_all_eighty_synthetic_worlds_join_with_both_source_reviews(self):
        labels = v.sealed_labels(self.root, self.release_path, self.plan)
        self.assertEqual(len(labels), 80)
        self.assertTrue(all(row[v.LABELS[0]] and row[v.LABELS[1]] for row in labels.values()))

    def test_missing_world_cannot_shrink_label_denominator(self):
        self.release["worlds"].pop()
        self.save()
        with self.assertRaisesRegex(ValueError, "eighty"):
            v.sealed_labels(self.root, self.release_path, self.plan)

    def test_final_label_cannot_disagree_with_frozen_combination_rule(self):
        self.release["worlds"][0][v.LABELS[0]] = False
        self.save()
        with self.assertRaisesRegex(ValueError, "vote rule"):
            v.sealed_labels(self.root, self.release_path, self.plan)

    def test_a_source_review_cannot_change_after_sealing(self):
        source = self.release["worlds"][0]["review_artifacts"][0]
        path = self.root / source["path"]
        record = v.load(path)
        record[v.LABELS[0]] = False
        self.write(path, record)
        with self.assertRaisesRegex(ValueError, "artifact changed"):
            v.sealed_labels(self.root, self.release_path, self.plan)

    def test_undelivered_proposal_cannot_support_positive_final_label(self):
        row = self.release["worlds"][0]
        packet = v.load(self.root / row["packet_path"])
        packet["notes"][0]["delivered_to"] = ["A"]
        self.write(self.root / row["packet_path"], packet)
        original_path = self.root / "runs" / "validation" / row["session_id"] / "rounds/4/prefix_review_packet.json"
        original = v.load(original_path)
        original["notes"] = packet["notes"]
        self.write(original_path, original)
        row["packet_sha256"] = v.sha(self.root / row["packet_path"])
        for source in row["review_artifacts"]:
            path = self.root / source["path"]
            record = v.load(path)
            record["packet_sha256"] = row["packet_sha256"]
            self.write(path, record)
            source["sha256"] = v.sha(path)
        self.save()
        with self.assertRaisesRegex(ValueError, "cross-actor"):
            v.sealed_labels(self.root, self.release_path, self.plan)

    def test_disagreement_requires_third_review_before_join(self):
        row = self.release["worlds"][0]
        source = row["review_artifacts"][0]
        path = self.root / source["path"]
        record = v.load(path)
        record[v.LABELS[0]] = None
        self.write(path, record)
        source["sha256"] = v.sha(path)
        row["original_review_votes"][v.LABELS[0]][0]["value"] = None
        self.save()
        with self.assertRaisesRegex(ValueError, "third-review"):
            v.sealed_labels(self.root, self.release_path, self.plan)


if __name__ == "__main__":
    unittest.main()
