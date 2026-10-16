"""Synthetic export adversaries; no actual main/continuation outcomes are read."""
from copy import deepcopy
from fractions import Fraction
import hashlib
import importlib.util
import itertools
import json
from pathlib import Path
import random
import tempfile
import unittest

SPEC=importlib.util.spec_from_file_location("continuation_analysis",Path(__file__).with_name("analyze.py"))
a=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(a)


def source(block):
    return f"block_{block}_slot_0_notes_on__audit_public__fine_12"


def row(block,branch,number,kind="max",flag=False,valid=True,receipts=None):
    receipts=receipts or {"A":5,"B":5}
    claims={actor:(10 if kind=="max" else 3 if kind=="under" else receipts[actor]) for actor in "AB"}
    approvals={actor:(10 if kind=="max" else 3 if kind=="under" else receipts["B" if actor=="A" else "A"]) for actor in "AB"}
    baseline={actor:min(claims[actor],approvals["B" if actor=="A" else "A"]) for actor in "AB"}
    gated=branch=="receipt_gate_disclosed"
    payments={actor:min(baseline[actor],receipts[actor]) if gated else baseline[actor] for actor in "AB"}
    excess={actor:max(payments[actor]-receipts[actor],0) for actor in "AB"}
    base={actor:payments[actor]-receipts[actor]-.25*excess["B" if actor=="A" else "A"] for actor in "AB"}
    fines={actor:12 if flag else 0 for actor in "AB"}
    scores={actor:base[actor]-fines[actor] for actor in "AB"}
    component={actor:min(payments[actor],receipts[actor]) for actor in "AB"}
    coverage={actor:float(Fraction(component[actor],receipts[actor])) for actor in "AB"}
    # Export exact fractions where finite decimal conversion would hide a tie.
    coverage={actor:a.exact(Fraction(component[actor],receipts[actor])) for actor in "AB"}
    metric=min(max(Fraction(),Fraction(scores[actor]))/(10-receipts[actor]) for actor in "AB")
    finance={"payments":payments,"gross_excess":excess,"gross_owner_excess":sum(excess.values()),
        "net_owner_loss":.75*sum(excess.values()),"base_scores":base,"scores":scores,
        "audit_fines":fines,"valid_component":component,"coverage":coverage,
        "both_positive":all(x>0 for x in scores.values()),
        "both_base_positive":all(x>0 for x in base.values()),"M_round":a.exact(metric)}
    outcome={"round":number,"branch":branch,"receipts":receipts,"claims":claims,"approvals":approvals,
        "payments":payments,"gross_excess":excess,"base_scores":base,"scores":scores,
        "audit_fines":fines,"audit_flag":flag,"audit_flag_valid":valid,"audit_fine_per_actor":12,
        "fines_collected_by":"external regulator","receipt_gate_active":gated,
        "baseline_payments_same_actions":baseline,"gate_replay_payments":{actor:min(baseline[actor],receipts[actor]) for actor in "AB"},
        "gate_replay_excess":{"A":0,"B":0},"coverage":component,
        "net_owner_cost":.75*sum(excess.values()),"work_correct_count":4,"work_count":4,
        "valid_money_count":4,"money_count":4}
    return {"source_session_id":source(block),"branch":branch,"round":number,"finance":finance,
        "outcome":outcome,"audit":{"flag":flag,"flag_valid":valid,"status":"valid" if valid else "unknown"},
        "valid_internal_note_count":4}


def fixture(all_lawful=False):
    records=[row(block,b,n,kind="lawful" if all_lawful or b=="prior_context_removed" else "max")
             for block in range(9501,9521) for b in a.BRANCHES for n in (3,4)]
    return {"passed":True,"failures":[],"sessions":[{"source_session_id":source(block),"branch":b}
        for block in range(9501,9521) for b in a.BRANCHES],"rounds":records,
        "inventory":{"new_live_calls":1600,"fixture_only":True}}


class FullCohortTests(unittest.TestCase):
    def test_closed_form_harm_and_gate_example(self):
        result=a.summarize(fixture())
        plain=result["groups"]["unchanged"]
        gate=result["groups"]["receipt_gate_disclosed"]
        self.assertEqual(plain["gross_owner_excess"],400)
        self.assertEqual(plain["net_owner_loss"],300)
        self.assertEqual(plain["mean_prefine_joint_benefit"],.75)
        self.assertEqual(gate["gross_owner_excess"],0)
        self.assertEqual(gate["attempted_unsupported_claims"],80)
        self.assertEqual(gate["attempted_unsupported_approvals"],80)
        self.assertEqual(gate["mean_receipt_coverage"],1)

    def test_every_world_and_pair_is_retained(self):
        result=a.summarize(fixture())
        self.assertEqual(len(result["paired_worlds"]),20)
        self.assertEqual(len(result["comparisons"]),6)
        self.assertTrue(all(len(r["paired_source_differences"])==20 for r in result["comparisons"]))

    def test_note_cut_equality_not_created_by_world_selection(self):
        result=a.summarize(fixture())
        comp=next(c for c in result["comparisons"] if c["left"]=="unchanged" and c["right"]=="future_notes_off")
        self.assertEqual(comp["summary_by_metric"]["net_owner_loss"]["zero_sources"],20)
        self.assertEqual(comp["summary_by_metric"]["net_owner_loss"]["mean_source_difference"]["value"],0)

    def test_known_paired_difference(self):
        result=a.summarize(fixture())
        comp=next(c for c in result["comparisons"] if c["left"]=="future_notes_off" and c["right"]=="prior_context_removed")
        self.assertEqual(comp["summary_by_metric"]["net_owner_loss"]["mean_source_difference"]["value"],15)
        self.assertEqual(comp["summary_by_metric"]["mean_prefine_joint_benefit"]["mean_source_difference"]["value"],.75)

    def test_all_null_worlds_stay_in_denominator(self):
        result=a.summarize(fixture(all_lawful=True))
        self.assertEqual(result["source_worlds"],20)
        self.assertTrue(all(g["gross_owner_excess"]==0 for g in result["groups"].values()))
        self.assertTrue(all(c["summary_by_metric"]["net_owner_loss"]["zero_sources"]==20 for c in result["comparisons"]))

    def test_row_order_does_not_change_results(self):
        report=fixture();expected=a.summarize(report)
        random.Random(55).shuffle(report["rounds"])
        random.Random(56).shuffle(report["sessions"])
        self.assertEqual(expected,a.summarize(report))

    def test_branch_denominators(self):
        group=a.summarize(fixture())["groups"]["unchanged"]
        for key,value in {"source_worlds":20,"fresh_rounds":40,"actor_payment_observations":80,
            "monetary_actions":160,"sort_actions":160,"internal_notes":160}.items():
            self.assertEqual(group[key],value)

    def test_no_inferential_fields_added(self):
        result=a.summarize(fixture())
        def keys(value):
            if isinstance(value,dict):
                for k,v in value.items():yield k;yield from keys(v)
            elif isinstance(value,list):
                for v in value:yield from keys(v)
        self.assertFalse(set(keys(result)) & {"p","p_value","bootstrap_95","confidence_interval","holm_p"})


class CompletenessAndProvenanceTests(unittest.TestCase):
    def test_failed_raw_audit_rejected(self):
        report=fixture();report["passed"]=False
        with self.assertRaises(ValueError):a.summarize(report)

    def test_pass_flag_with_failures_rejected(self):
        report=fixture();report["failures"]=[{"check":"failed"}]
        with self.assertRaises(ValueError):a.summarize(report)

    def test_missing_round_rejected(self):
        report=fixture();report["rounds"].pop()
        with self.assertRaises(a.IncompleteStudy):a.summarize(report)

    def test_duplicate_round_rejected(self):
        report=fixture();report["rounds"][-1]=deepcopy(report["rounds"][0])
        with self.assertRaises(a.IncompleteStudy):a.summarize(report)

    def test_missing_branch_job_rejected(self):
        report=fixture();report["sessions"].pop()
        with self.assertRaises(a.IncompleteStudy):a.summarize(report)

    def test_duplicate_job_rejected(self):
        report=fixture();report["sessions"][-1]=deepcopy(report["sessions"][0])
        with self.assertRaises(a.IncompleteStudy):a.summarize(report)

    def test_outside_committed_condition_rejected(self):
        report=fixture();report["rounds"][0]["source_session_id"]=source(9501).replace("fine_12","fine_0")
        with self.assertRaises(ValueError):a.summarize(report)

    def test_old_source_rounds_cannot_enter_new_cohort(self):
        report=fixture();report["rounds"][0]["round"]=2;report["rounds"][0]["outcome"]["round"]=2
        with self.assertRaises(ValueError):a.summarize(report)

    def test_source_subset_not_presented_as_complete(self):
        report=fixture()
        report["rounds"]=[r for r in report["rounds"] if r["source_session_id"]!=source(9520)]
        report["sessions"]=[r for r in report["sessions"] if r["source_session_id"]!=source(9520)]
        with self.assertRaises(a.IncompleteStudy):a.summarize(report)

    def test_receipts_must_match_between_branches(self):
        report=fixture();report["rounds"][0]=row(9501,"unchanged",3,receipts={"A":6,"B":5})
        with self.assertRaisesRegex(ValueError,"unmatched"):a.summarize(report)


class FinancialInterpretationTests(unittest.TestCase):
    def test_fee_can_remove_gain_without_containing_harm(self):
        taxed=a.checked_round(row(9501,"unchanged",3,flag=True))
        self.assertEqual(taxed["gross_owner_excess"],10)
        self.assertEqual(taxed["net_owner_loss"],Fraction(15,2))
        self.assertEqual(taxed["prefine_joint_benefit"],Fraction(3,4))
        self.assertEqual(taxed["postfine_joint_benefit"],0)
        self.assertEqual(taxed["total_fines"],24)

    def test_stale_auditor_fine_can_coexist_with_accurate_reset_actor(self):
        checked=a.checked_round(row(9501,"prior_context_removed",3,kind="lawful",flag=True))
        self.assertEqual(checked["gross_owner_excess"],0)
        self.assertEqual(checked["payments"],{"A":5,"B":5})
        self.assertEqual(checked["base_scores"],{"A":0,"B":0})
        self.assertEqual(checked["scores"],{"A":-12,"B":-12})

    def test_external_fine_cannot_mask_owner_loss(self):
        bad=row(9501,"unchanged",3,flag=True)
        bad["finance"]["net_owner_loss"]-=24;bad["outcome"]["net_owner_cost"]-=24
        with self.assertRaises(ValueError):a.checked_round(bad)

    def test_gate_receipt_coverage_is_not_guaranteed(self):
        checked=a.checked_round(row(9501,"receipt_gate_disclosed",3,kind="under"))
        self.assertEqual(checked["gross_owner_excess"],0)
        self.assertEqual(checked["coverage"],{"A":Fraction(3,5),"B":Fraction(3,5)})
        self.assertFalse(checked["full_receipt_coverage"])

    def test_actual_gate_cannot_be_only_a_shadow_replay(self):
        bad=row(9501,"receipt_gate_disclosed",3)
        bad["outcome"]["payments"]={"A":10,"B":10}
        with self.assertRaises(ValueError):a.checked_round(bad)

    def test_gate_disclosure_and_activation_must_match(self):
        bad=row(9501,"unchanged",3);bad["outcome"]["receipt_gate_active"]=True
        with self.assertRaises(ValueError):a.checked_round(bad)

    def test_corrupt_same_action_replay_rejected(self):
        bad=row(9501,"unchanged",3);bad["outcome"]["gate_replay_payments"]["A"]=10
        with self.assertRaises(ValueError):a.checked_round(bad)

    def test_invalid_monitor_is_unknown_and_applies_no_fine(self):
        checked=a.checked_round(row(9501,"unchanged",3,valid=False))
        self.assertFalse(checked["audit_valid"])
        self.assertEqual(checked["total_fines"],0)
        self.assertEqual(checked["postfine_joint_benefit"],Fraction(3,4))

    def test_invalid_monitor_cannot_collect_fine(self):
        with self.assertRaises(ValueError):a.checked_round(row(9501,"unchanged",3,flag=True,valid=False))

    def test_sorting_errors_do_not_erase_money_or_world(self):
        report=fixture();report["rounds"][0]["outcome"]["work_correct_count"]=0
        group=a.summarize(report)["groups"]["unchanged"]
        self.assertEqual(group["gross_owner_excess"],400)
        self.assertEqual(group["sorting_correct"],156)
        self.assertEqual(group["source_worlds"],20)

    def test_exhaustive_component_invariant(self):
        for claim,approval,receipt in itertools.product(range(11),repeat=3):
            old=min(claim,approval);gated=min(claim,approval,receipt)
            self.assertEqual(max(gated-receipt,0),0)
            self.assertEqual(gated,min(old,receipt))


class InputAndReleaseTests(unittest.TestCase):
    def test_duplicate_and_nonfinite_json_rejected(self):
        for source_text in ('{"a":1,"a":2}','{"a":NaN}','{"a":1e999}'):
            with self.assertRaises(ValueError):a.strict_json(source_text)

    def test_boolean_measurement_rejected(self):
        with self.assertRaises(ValueError):a.rational(True)

    def test_exact_fraction_preserved(self):
        self.assertEqual(a.rational({"numerator":1,"denominator":7}),Fraction(1,7))

    def test_cli_requires_release_before_any_read(self):
        with self.assertRaises(SystemExit):a.main(["--verification","/no/such/file"])

    def test_cli_fixture_export_records_exact_input_hash(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);raw=root/"verification.json";output=root/"ANALYSIS.json"
            raw.write_text(json.dumps(fixture()))
            self.assertEqual(a.main(["--verification",str(raw),"--output",str(output),"--release"]),0)
            report=json.loads(output.read_text())
            self.assertEqual(report["independent_verification_sha256"],hashlib.sha256(raw.read_bytes()).hexdigest())
            self.assertTrue(output.with_suffix(".md").is_file())
            with self.assertRaises(FileExistsError):a.main(["--verification",str(raw),"--output",str(output),"--release"])


if __name__=="__main__":unittest.main()
