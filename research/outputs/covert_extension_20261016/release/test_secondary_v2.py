"""Regression tests for the post-freeze reporting-only guard correction."""
from contextlib import ExitStack
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

HERE=Path(__file__).resolve().parent

def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    value=importlib.util.module_from_spec(spec); spec.loader.exec_module(value)
    return value

V=module("covert_secondary_v2_tests",HERE/"secondary_execution_v2.py")
F=module("covert_secondary_frozen_bug_tests",HERE.parent/"formation"/"secondary_execution.py")


def fixture(root):
    specs=[]; sessions=[]
    for b in range(10051,10063):
        for slot,arm in enumerate(V.A.ARMS):
            spec={"session_id":f"{b}_{arm}","seed":b,"block_id":b,"slot":slot,"condition":arm,
                "rounds":3,"control_type":None,"canonical_reports":arm==V.A.ARMS[2],"fine_per_actor":0 if arm==V.A.ARMS[0] else 8}
            specs.append(spec)
            # Exactly the released analysis shape: this field intentionally
            # replaces the plan's integer round count with three actual rows.
            sessions.append({**spec,"phase":"heldout","rounds":[{"round":n} for n in (1,2,3)]})
    plan={"heldout":specs}; raw={"sha256":"raw-sha"}; seal={"sha256":"seal-sha"}
    labels={s["session_id"]:{"session_id":s["session_id"],"review_id":f"world_{i:03}",V.A.LABEL:False} for i,s in enumerate(specs,1)}
    data={"inference_eligible":True,"planned_total_calls":1430,"heldout_worlds":36,"heldout_rounds":108,
        "review_release":{"sha256":seal["sha256"]},"raw_verification":{"sha256":raw["sha256"]},
        "source_hashes":{"analyzer_sha256":"sha::analyze.py"},"sessions":sessions}
    root.mkdir(exist_ok=True); (root/"plan.json").write_text(json.dumps(plan)); (root/"ANALYSIS.json").write_text(json.dumps(data))
    verification=root/"independent"/"all"/"INDEPENDENT_VERIFICATION_ALL.json"; verification.parent.mkdir(parents=True)
    (verification.parent/"SOURCE_BINDINGS.json").write_text('{"files":{}}')
    return plan,data,labels,raw,seal,verification


class GuardRegressionTests(unittest.TestCase):
    def exercise(self,subject,root,labels,raw,seal,verification):
        with ExitStack() as stack:
            stack.enter_context(patch.object(subject.A,"validate_plan"))
            stack.enter_context(patch.object(subject.A,"verify_release_prerequisites",return_value=raw))
            stack.enter_context(patch.object(subject.A,"load_sealed_labels",return_value=(labels,seal)))
            stack.enter_context(patch.object(subject.A,"sha",side_effect=lambda p:"sha::"+Path(p).name))
            return subject.guard(root,root/"seal.json",verification,root/"ANALYSIS.json")

    def test_actual_released_schema_reproduces_old_bug_and_passes_new_guard(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); plan,data,labels,raw,seal,verification=fixture(root)
            with self.assertRaisesRegex(ValueError,"session factors"):
                self.exercise(F,root,labels,raw,seal,verification)
            result=self.exercise(V,root,labels,raw,seal,verification)
            self.assertEqual(len(result[2]),36)
            self.assertEqual(result[4]["secondary_guard_fix"]["version"],2)

    def test_fixed_factor_mismatches_still_rejected(self):
        for key,value in (("condition","wrong"),("fine_per_actor",99),("canonical_reports",True),("seed",99),("block_id",99),("slot",99)):
            with self.subTest(key=key),tempfile.TemporaryDirectory() as td:
                root=Path(td); _,data,labels,raw,seal,verification=fixture(root)
                data["sessions"][0][key]=value; (root/"ANALYSIS.json").write_text(json.dumps(data))
                with self.assertRaisesRegex(ValueError,"session factors"):
                    self.exercise(V,root,labels,raw,seal,verification)

    def test_round_count_order_and_types_remain_required(self):
        for value in (3,[],[{"round":1},{"round":2}], [{"round":1},{"round":2},{"round":2}], [{"round":2},{"round":1},{"round":3}], [{"round":1},{"round":2},{"round":3},{"round":4}], [1,2,3]):
            with self.subTest(value=value),tempfile.TemporaryDirectory() as td:
                root=Path(td); _,data,labels,raw,seal,verification=fixture(root)
                data["sessions"][0]["rounds"]=value; (root/"ANALYSIS.json").write_text(json.dumps(data))
                with self.assertRaisesRegex(ValueError,"three ordered"):
                    self.exercise(V,root,labels,raw,seal,verification)

    def test_broken_primary_source_link_remains_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); _,data,labels,raw,seal,verification=fixture(root)
            data["review_release"]["sha256"]="changed"; (root/"ANALYSIS.json").write_text(json.dumps(data))
            with self.assertRaisesRegex(ValueError,"source linkage"):
                self.exercise(V,root,labels,raw,seal,verification)

    def test_incomplete_heldout_coverage_remains_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); _,data,labels,raw,seal,verification=fixture(root)
            data["sessions"].pop(); (root/"ANALYSIS.json").write_text(json.dumps(data))
            with self.assertRaisesRegex(ValueError,"all 36"):
                self.exercise(V,root,labels,raw,seal,verification)

    def test_guard_does_not_open_financial_outcomes(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); _,_,labels,raw,seal,verification=fixture(root)
            original=V.A.load
            def guarded(path):
                self.assertNotIn("runs",Path(path).parts)
                self.assertNotIn("calls",Path(path).parts)
                return original(path)
            with patch.object(V.A,"load",side_effect=guarded):
                self.exercise(V,root,labels,raw,seal,verification)

    def test_default_verification_path_matches_archived_all_report(self):
        self.assertEqual(V.default_paths(Path("study"))[1],Path("study/independent/all/INDEPENDENT_VERIFICATION_ALL.json"))

    def test_tier_and_annotation_logic_byte_identical_to_frozen_helper(self):
        import inspect
        for name in ("tri","conjunction","disjunction","negate","evaluate_tiers","validate_pair","validate_annotation","observed_predicates"):
            with self.subTest(name=name): self.assertEqual(inspect.getsource(getattr(V,name)),inspect.getsource(getattr(F,name)))


if __name__=="__main__": unittest.main()
