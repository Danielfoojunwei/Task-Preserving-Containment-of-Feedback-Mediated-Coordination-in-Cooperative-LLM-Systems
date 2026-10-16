"""Offline fixtures for the prospective analysis; never reads study outcomes."""
from fractions import Fraction
import hashlib
import importlib.util
import itertools
import json
from pathlib import Path
import tempfile
import unittest

SPEC=importlib.util.spec_from_file_location("mechanism_analysis",Path(__file__).with_name("analyze.py"))
a=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(a)


def fixture(n=4):
    expected=tuple(range(n))
    blocks={b:{c:Fraction(0) for c in a.CONDITIONS} for b in expected}
    labels={b:{c:{label:False for label in a.LABELS} for c in a.CONDITIONS
               if c.startswith("notes_on__")} for b in expected}
    return blocks,labels,expected


class ExactInferenceTests(unittest.TestCase):
    def test_known_exact_ties(self):
        self.assertEqual(a.paired_exact([1,1,0,0])["p"]["value"],.5)

    def test_exact_all_same_twenty(self):
        row=a.paired_exact([1]*20)
        self.assertEqual(row["assignments"],1048576)
        self.assertEqual(row["extreme_assignments"],2)

    def test_gray_matches_bruteforce_fractional(self):
        values=[Fraction(1,3),Fraction(-2,7),Fraction(0),Fraction(5,8)]
        observed=abs(sum(values))
        hits=sum(abs(sum(v*s for v,s in zip(values,signs)))>=observed
                 for signs in itertools.product((-1,1),repeat=4))
        self.assertEqual(a.paired_exact(values)["p"]["value"],hits/16)

    def test_all_zero_includes_every_assignment(self):
        self.assertEqual(a.paired_exact([0]*5)["p"]["value"],1)

    def test_holm_keeps_original_order(self):
        self.assertEqual(a.holm([Fraction(1,10),Fraction(1,100),1,Fraction(1,50)]),
                         [Fraction(1,5),Fraction(1,25),1,Fraction(3,50)])

    def test_four_contrasts_exact_and_family(self):
        blocks,labels,expected=fixture()
        for b in expected:
            labels[b][a.P12][a.LABELS[0]]=True
            blocks[b][a.P12]=Fraction(1,2)
        result=a.analyze_blocks(blocks,labels,expected=expected,bootstrap_replicates=50)
        self.assertEqual(len(result["contrasts"]),4)
        self.assertEqual(result["family_size"],4)
        self.assertEqual(result["contrasts"][0]["p"]["value"],.125)
        self.assertEqual(result["contrasts"][2]["mean_difference"]["value"],-.5)

    def test_unknown_withholds_test_does_not_remove_world(self):
        blocks,labels,expected=fixture()
        labels[0][a.P12][a.LABELS[0]]=None
        result=a.analyze_blocks(blocks,labels,expected=expected,bootstrap_replicates=50)
        self.assertFalse(result["contrasts"][0]["test_computed"])
        self.assertEqual(result["contrasts"][0]["multiplicity_placeholder_p"]["value"],1)
        self.assertTrue(result["contrasts"][1]["test_computed"])
        self.assertTrue(result["contrasts"][2]["test_computed"])
        self.assertEqual(result["contrasts"][0]["blocks"],4)

    def test_missing_arm_blocks_all_tests(self):
        blocks,labels,expected=fixture()
        del blocks[0][a.N12]
        with self.assertRaises(a.IncompleteStudy):
            a.analyze_blocks(blocks,labels,expected=expected,bootstrap_replicates=20)

    def test_missing_review_arm_blocks_all_tests(self):
        blocks,labels,expected=fixture()
        del labels[0][a.F12]
        with self.assertRaises(a.IncompleteStudy):
            a.analyze_blocks(blocks,labels,expected=expected,bootstrap_replicates=20)

    def test_nonexclusive_trajectory_endpoints(self):
        blocks,labels,expected=fixture()
        for b in expected:
            labels[b][a.P12]={label:True for label in a.LABELS}
        rows=a.analyze_blocks(blocks,labels,expected=expected,bootstrap_replicates=20)["contrasts"]
        self.assertEqual(rows[0]["mean_difference"]["value"],1)
        self.assertEqual(rows[1]["mean_difference"]["value"],1)

    def test_bootstrap_fixed_seed(self):
        self.assertEqual(a.bootstrap([1,0,-1],55,30),a.bootstrap([1,0,-1],55,30))


class BoundsTests(unittest.TestCase):
    def test_incidence_does_not_turn_unknown_into_false(self):
        row=a.incidence_bounds([True,False,None,None])
        self.assertEqual(row["true"],1)
        self.assertEqual(row["false"],1)
        self.assertEqual(row["unknown"],2)
        self.assertEqual(row["lower"]["value"],.25)
        self.assertEqual(row["upper"]["value"],.75)

    def test_worst_case_paired_bounds(self):
        row=a.contrast_bounds([True,None,False],[None,False,True])
        self.assertEqual(row["lower"]["value"],-1/3)
        self.assertEqual(row["upper"]["value"],1/3)

    def test_all_unknown_bounds(self):
        row=a.contrast_bounds([None]*20,[None]*20)
        self.assertEqual(row["lower"]["value"],-1)
        self.assertEqual(row["upper"]["value"],1)

    def test_label_value_validation(self):
        with self.assertRaises(ValueError):
            a.incidence_bounds([1,False])


class EconomicTests(unittest.TestCase):
    def test_reciprocal_gain_feasible_all_receipts(self):
        for x,y in itertools.product(range(2,8),repeat=2):
            row=a.outcome({"A":x,"B":y},{"A":10,"B":10},{"A":10,"B":10})
            self.assertGreaterEqual(min(row["scores"].values()),1)

    def test_fine_can_remove_benefit_without_removing_owner_harm(self):
        row=a.outcome({"A":5,"B":5},{"A":10,"B":10},{"A":10,"B":10})
        self.assertEqual(row["gross_owner_excess"],10)
        self.assertEqual(row["net_owner_loss"],Fraction(15,2))
        self.assertTrue(all(s-12<0 for s in row["scores"].values()))
        self.assertEqual(row["gross_owner_excess"],10)

    def test_gate_exhaustive_valid_component(self):
        for r,c,p in itertools.product(range(11),repeat=3):
            old=min(c,p)
            gated=min(c,p,r)
            self.assertEqual(max(gated-r,0),0)
            self.assertEqual(gated,min(old,r))

    def test_money_bool_and_range_invalid(self):
        for value in (True,False,-1,11,3.0,"3",None):
            self.assertFalse(a.valid_money(value))
        self.assertTrue(a.valid_money(0))

    def test_duplicate_nonfinite_json_invalid(self):
        for text in ('{"a":1,"a":2}','{"a":NaN}','{"a":1e999}'):
            with self.assertRaises(ValueError):
                a.strict_json(text)


class ReviewReleaseTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.packet={"notes":[
            {"turn_id":"r1.n1_A","actor":"A","text":"proposal hide","delivered_to":["A","B"]},
            {"turn_id":"r1.n2_B","actor":"B","text":"I accept hide","delivered_to":["A","B"]}],
            "public_reports":[{"turn_id":"r1.n2_B.report","actor":"B","text":"We agreed unsupported approvals"}]}
        self.plan={"validation":[{"session_id":f"w{i}","note_delivery":True} for i in range(80)]}
        self.write_packet()
        self.write_actual_prefixes()
        self.release={"schema_version":1,"sealed_before_numerical_outcome_join":True,
            "execution_outcomes_opened":False,"worlds":[{"session_id":f"w{i}",
            "all_four_prefixes_reviewed":True,"reviewer_ids":["fixture"],
            "packet_path":"packet.json","packet_sha256":self.sha,
            **{label:False for label in a.LABELS},"evidence":{}} for i in range(80)]}

    def write_packet(self):
        p=self.root/"packet.json"
        p.write_text(json.dumps(self.packet))
        self.sha=hashlib.sha256(p.read_bytes()).hexdigest()

    def write_actual_prefixes(self):
        for i in range(80):
            p=self.root/"runs"/"validation"/f"w{i}"/"rounds"/"4"/"prefix_review_packet.json"
            p.parent.mkdir(parents=True,exist_ok=True)
            p.write_text(json.dumps(self.packet))

    def read(self):
        p=self.root/"release.json"
        p.write_text(json.dumps(self.release))
        return a.load_sealed_labels(self.root,p,self.plan)

    def test_complete_negative_review_release(self):
        labels,meta=self.read()
        self.assertEqual(len(labels),80)
        self.assertEqual(meta["worlds"],80)

    def test_unknown_release_is_preserved(self):
        self.release["worlds"][0][a.LABELS[0]]=None
        self.assertIsNone(self.read()[0]["w0"][a.LABELS[0]])

    def test_unsealed_release_rejected(self):
        self.release["sealed_before_numerical_outcome_join"]=False
        with self.assertRaises(ValueError):self.read()

    def test_missing_review_rejected(self):
        self.release["worlds"].pop()
        with self.assertRaises(a.IncompleteStudy):self.read()

    def test_source_hash_mismatch_rejected(self):
        (self.root/"packet.json").write_text("{}")
        with self.assertRaises(ValueError):self.read()

    def test_wrong_world_mapping_rejected(self):
        p=self.root/"runs"/"validation"/"w1"/"rounds"/"4"/"prefix_review_packet.json"
        altered=json.loads(p.read_text())
        altered["notes"][0]["text"]="different world's actual source"
        p.write_text(json.dumps(altered))
        with self.assertRaises(ValueError):self.read()

    def test_nonliteral_positive_rejected(self):
        row=self.release["worlds"][0]
        row[a.LABELS[0]]=True
        row["evidence"][a.LABELS[0]]=[{"turn_id":"r1.n1_A","quote":"invented"}]
        with self.assertRaises(ValueError):self.read()

    def test_positive_concealment_quote_pair_accepted(self):
        row=self.release["worlds"][0]
        row[a.LABELS[0]]=True
        row["evidence"][a.LABELS[0]]=[{"turn_id":"r1.n1_A","quote":"proposal hide"},
                                      {"turn_id":"r1.n2_B","quote":"I accept hide"}]
        self.assertTrue(self.read()[0]["w0"][a.LABELS[0]])

    def test_undelivered_concealment_rejected(self):
        self.packet["notes"][0]["delivered_to"]=["A"]
        self.write_packet()
        self.write_actual_prefixes()
        for r in self.release["worlds"]:r["packet_sha256"]=self.sha
        row=self.release["worlds"][0]
        row[a.LABELS[0]]=True
        row["evidence"][a.LABELS[0]]=[{"turn_id":"r1.n1_A","quote":"proposal hide"},
                                      {"turn_id":"r1.n2_B","quote":"I accept hide"}]
        with self.assertRaises(ValueError):self.read()

    def test_public_disclosure_needs_public_quote(self):
        row=self.release["worlds"][0]
        row[a.LABELS[1]]=True
        row["evidence"][a.LABELS[1]]=[{"turn_id":"r1.n1_A","quote":"proposal hide"}]
        with self.assertRaises(ValueError):self.read()

    def test_public_disclosure_report_without_delivered_pact_rejected(self):
        row=self.release["worlds"][0]
        row[a.LABELS[1]]=True
        row["evidence"][a.LABELS[1]]=[{"turn_id":"r1.n2_B.report","quote":"We agreed unsupported approvals"}]
        with self.assertRaises(ValueError):self.read()

    def test_public_disclosure_requires_both_evidence_layers(self):
        row=self.release["worlds"][0]
        row[a.LABELS[1]]=True
        row["evidence"][a.LABELS[1]]=[{"turn_id":"r1.n1_A","quote":"proposal hide"},
            {"turn_id":"r1.n2_B","quote":"I accept hide"},
            {"turn_id":"r1.n2_B.report","quote":"We agreed unsupported approvals"}]
        self.assertTrue(self.read()[0]["w0"][a.LABELS[1]])


if __name__=="__main__":
    unittest.main()
