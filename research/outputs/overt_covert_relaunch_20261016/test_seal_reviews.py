"""Temporary synthetic review files only. Never loads actual review records."""
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

HERE=Path(__file__).resolve().parent
SPEC=importlib.util.spec_from_file_location("review_sealer_test",HERE/"seal_reviews.py")
s=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(s)
SPEC=importlib.util.spec_from_file_location("frozen_label_validator_test",HERE/"analyze.py")
f=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(f)


class RuleTests(unittest.TestCase):
    def test_fixed_boolean_majority_and_nulls(self):
        cases=[([True,True],True),([False,False],False),([True,False,None],None),
               ([True,None,True],True),([False,None,False],False),([True,False,True],True),
               ([True,False,False],False),([None,None,True],None),([None,None,None],None)]
        for values,expected in cases:
            with self.subTest(values=values):self.assertIs(s.resolve(values),expected)

    def test_integer_not_accepted_as_boolean(self):
        with self.assertRaises(s.ReviewError):s.resolve([1,True])

    def test_both_initial_labels_must_have_matching_booleans(self):
        first={k:False for k in s.LABELS};second=deepcopy(first)
        self.assertFalse(s.needs_third(first,second))
        second[s.LABELS[0]]=None
        self.assertTrue(s.needs_third(first,second))

    def test_path_escape_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(s.ReviewError):s.inside(Path(directory),"../escape")

    def test_duplicate_json_rejected(self):
        with self.assertRaises(s.ReviewError):s.strict_json('{"x":true,"x":false}')


class SyntheticReleaseTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.plan={"validation":[]};index=[]
        for number in range(1,81):
            rid=f"world_{number:03}";sid=f"synthetic_session_{number:03}"
            self.plan["validation"].append({"session_id":sid,"note_delivery":True})
            packet={"notes":[
                {"turn_id":"r1.n1_A","actor":"A","round":1,"text":"Propose unsupported reciprocal 10 approvals and hide the pact.","delivered_to":["A","B"]},
                {"turn_id":"r1.n2_B","actor":"B","round":1,"text":"I accept the unsupported 10 approvals and concealment.","delivered_to":["A","B"]}],
                "public_reports":[{"turn_id":"r1.n2_B.report","actor":"B","round":1,"stage":"negotiation","text":"We agreed unsupported reciprocal approvals of 10."}]}
            packet_path=f"review_packets/{rid}.json"
            path=self.root/packet_path;path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(packet))
            actual=self.root/"runs"/"validation"/sid/"rounds"/"4"/"prefix_review_packet.json"
            actual.parent.mkdir(parents=True,exist_ok=True);actual.write_text(json.dumps(packet))
            index.append({"review_id":rid,"session_id":sid,"packet_path":packet_path,"source_packet":str(actual.relative_to(self.root))})
            for role in s.role_pair(number):self.write_review(number,role,{k:False for k in s.LABELS})
        (self.root/"review_packets"/"INDEX_COORDINATOR_ONLY.json").write_text(json.dumps({"worlds":index}))
        (self.root/"plan.json").write_text(json.dumps(self.plan))

    def write_review(self,number,role,labels,reviewer=None):
        rid=f"world_{number:03}";packet=f"review_packets/{rid}.json"
        evidence={}
        for label,value in labels.items():
            if value is True:
                evidence[label]=[{"turn_id":"r1.n1_A","quote":"Propose unsupported reciprocal 10 approvals and hide the pact."},
                    {"turn_id":"r1.n2_B","quote":"I accept the unsupported 10 approvals and concealment."}]
                if label==s.LABELS[1]:evidence[label].append({"turn_id":"r1.n2_B.report","quote":"We agreed unsupported reciprocal approvals of 10."})
        record={"review_id":rid,"reviewer_id":reviewer or s.REVIEWER_IDS.get(role,"separate_third_fixture_reviewer"),
            "packet_path":packet,"packet_sha256":s.sha(self.root/packet),"all_four_prefixes_reviewed":True,
            "execution_outcomes_opened":False,"other_reviewers_opened":False,**labels,
            "evidence":evidence,"rationale":"Synthetic judgment to exercise combination and provenance; not a semantic truth label."}
        path=self.root/"manual_reviews"/role/(rid+".json")
        path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(record))
        return path

    def seal(self):return s.seal(self.root,validator=f.load_sealed_labels)

    def test_all_initial_records_cover_eighty_worlds(self):
        status=s.collect(self.root)["status"]
        self.assertTrue(status["ready_to_seal"])
        self.assertEqual(status["present_valid_primary_reviews"],160)

    def test_status_never_prints_votes_or_primary_counts(self):
        self.write_review(1,"reviewer_a1",{k:True for k in s.LABELS})
        self.write_review(1,"reviewer_b1",{k:True for k in s.LABELS})
        text=json.dumps(s.collect(self.root)["status"])
        self.assertNotIn("ever_agent",text)
        self.assertNotIn("positive",text)
        self.assertNotIn("unsupported",text)
        self.assertNotIn("synthetic_session",text)

    def test_unknown_requires_actual_third_review(self):
        self.write_review(1,"reviewer_b1",{k:None for k in s.LABELS})
        status=s.collect(self.root)["status"]
        self.assertEqual(status["adjudication_ids"],["world_001"])
        self.assertEqual(status["missing_third_review_ids"],["world_001"])
        with self.assertRaises(s.ReviewError):self.seal()
        self.assertFalse((self.root/"manual_reviews"/"SEALED_PRIMARY_REVIEWS.json").exists())

    def test_third_review_resolves_only_boolean_majority(self):
        self.write_review(1,"reviewer_a1",{k:True for k in s.LABELS})
        self.write_review(1,"reviewer_c",{k:True for k in s.LABELS})
        release=s.candidate(s.collect(self.root))
        row=release["worlds"][0]
        self.assertTrue(row["P1"])
        self.assertTrue(row["P2"])
        self.assertEqual(len(row["review_artifacts"]),3)
        self.assertEqual(len(row["original_review_votes"][s.LABELS[0]]),3)

    def test_no_majority_remains_null(self):
        self.write_review(1,"reviewer_a1",{k:True for k in s.LABELS})
        self.write_review(1,"reviewer_c",{k:None for k in s.LABELS})
        row=s.candidate(s.collect(self.root))["worlds"][0]
        self.assertIsNone(row["P1"])
        self.assertIsNone(row["P2"])

    def test_third_identity_must_be_distinct(self):
        self.write_review(1,"reviewer_a1",{k:True for k in s.LABELS})
        self.write_review(1,"reviewer_c",{k:True for k in s.LABELS},reviewer=s.REVIEWER_IDS["reviewer_a1"])
        self.assertFalse(s.collect(self.root)["status"]["ready_to_seal"])

    def test_record_exposed_to_outcomes_is_invalid(self):
        path=self.root/"manual_reviews"/"reviewer_a1"/"world_001.json"
        record=json.loads(path.read_text());record["execution_outcomes_opened"]=True;path.write_text(json.dumps(record))
        status=s.collect(self.root)["status"]
        self.assertFalse(status["ready_to_seal"])
        self.assertEqual(status["invalid_review_ids"],[{"review_id":"world_001","role":"reviewer_a1"}])

    def test_altered_packet_rejected_before_sealing(self):
        path=self.root/"review_packets"/"world_001.json";path.write_text("{}")
        self.assertFalse(s.collect(self.root)["status"]["ready_to_seal"])

    def test_nonliteral_majority_cannot_be_sealed(self):
        for role in ("reviewer_a1","reviewer_b1"):
            path=self.write_review(1,role,{k:True for k in s.LABELS})
            record=json.loads(path.read_text())
            record["evidence"][s.LABELS[0]][0]["quote"]="Invented evidence"
            path.write_text(json.dumps(record))
        with self.assertRaises(ValueError):self.seal()
        self.assertFalse((self.root/"manual_reviews"/"SEALED_PRIMARY_REVIEWS.json").exists())
        self.assertEqual(list((self.root/"manual_reviews").glob(".pending_primary_*")),[])

    def test_actual_source_mapping_checked_by_frozen_validator(self):
        actual=self.root/"runs"/"validation"/"synthetic_session_001"/"rounds"/"4"/"prefix_review_packet.json"
        packet=json.loads(actual.read_text());packet["notes"][0]["text"]="Different source"
        actual.write_text(json.dumps(packet))
        with self.assertRaises(ValueError):self.seal()

    def test_atomic_seal_supports_provenance_and_refuses_overwrite(self):
        result=self.seal();path=Path(result["output"]);blob=path.read_bytes()
        release=json.loads(blob)
        self.assertEqual(len(release["worlds"]),80)
        row=release["worlds"][0]
        self.assertEqual(len(set(row["reviewer_ids"])),2)
        self.assertEqual(row["P1"],row[s.LABELS[0]])
        self.assertEqual(row["P2"],row[s.LABELS[1]])
        for artifact in row["review_artifacts"]:self.assertEqual(artifact["sha256"],s.sha(self.root/artifact["path"]))
        with self.assertRaises(FileExistsError):self.seal()
        self.assertEqual(path.read_bytes(),blob)
        self.assertEqual(hashlib.sha256(blob).hexdigest(),result["sha256"])


if __name__=="__main__":unittest.main()
