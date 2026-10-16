"""Offline checks of information boundaries, payment rules and immutable scheduling."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

SPEC = importlib.util.spec_from_file_location("causal_runner", Path(__file__).with_name("run_study.py"))
r = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(r)


def action(amount=10, private="", note=""):
    return {"amount": amount, "amount_valid": True, "workflow_tag": "OWNER-TAG",
            "public_report": "OWNER-REPORT", "work_order": ["T1", "T2", "T3", "T4"],
            "work_correct": True, "private_memory": private,
            "internal_note": note, "internal_note_valid": True}


def observe(messages):
    return json.loads(messages[1]["content"])


def raw_record(value):
    return {"raw_content": json.dumps(value), "status": "completed"}


class FakeClient:
    strict_json = staticmethod(r.load_client().strict_json)

    def __init__(self, cost=.001, fail=False):
        self.cost = cost
        self.fail = fail
        self.calls = 0

    def call(self, messages, schema, model, directory, **kwargs):
        self.calls += 1
        result = {"status": "failed" if self.fail else "completed", "usage": {},
                  "raw_content": "{}"}
        if self.cost is not None:
            result["usage"]["cost"] = self.cost
        r.save_new(directory / "call.json", result)
        return result


class RunnerTests(unittest.TestCase):
    def setUp(self):
        self.case = r.make_cases(9201)[0]
        self.state = r.initial_state()

    def test_randomized_plan_complete_and_matched(self):
        plan = r.build_plan()
        self.assertEqual(len(plan["pilot"]), 4)
        main = [item for item in plan["validation"] if item["block_id"]]
        self.assertEqual(len(main), 64)
        for block in range(9201, 9217):
            group = [item for item in main if item["block_id"] == block]
            self.assertEqual({item["condition"] for item in group}, set(r.ARMS))
            self.assertEqual({item["slot"] for item in group}, set(range(4)))
        self.assertEqual(plan, r.build_plan())
        self.assertEqual([case["round"] for case in plan["continuation_cases"]["9201"]], [3, 4])

    def test_peer_private_memory_never_crosses(self):
        self.state["private_memory"]["B"] = "B-SECRET"
        self.state["private_memory"]["A"] = "A-OWN"
        messages = r.participant_messages("A", "full", self.state, "negotiation", 1)
        self.assertIn("A-OWN", messages[1]["content"])
        self.assertNotIn("B-SECRET", messages[1]["content"])

    def test_no_notes_withholds_peer_text_at_future_turns(self):
        r.apply_negotiation(self.state, "B", action(note="B-PRIVATE-NOTE"), "r1.n2_B", 1, deliver=False)
        r.apply_negotiation(self.state, "A", action(note="A-OWN-NOTE"), "r1.n3_A", 1, deliver=False)
        payload = r.participant_messages("A", "no_notes", self.state, "negotiation", 2)[1]["content"]
        self.assertNotIn("B-PRIVATE-NOTE", payload)
        self.assertIn("A-OWN-NOTE", payload)

    def test_owner_reports_not_relayed_in_notes(self):
        r.apply_negotiation(self.state, "B", action(note="DELIVERED-NOTE"), "r1.n2_B", 1)
        payload = r.participant_messages("A", "full", self.state, "negotiation", 1)[1]["content"]
        self.assertIn("DELIVERED-NOTE", payload)
        self.assertNotIn("OWNER-REPORT", payload)
        self.assertNotIn("delivered_to", payload)

    def test_review_peer_view_numeric_only_in_every_arm(self):
        claims = {"A": action(8), "B": action(9)}
        for arm in (*r.ARMS, "assigned", "cooperative"):
            view = observe(r.participant_messages("A", arm, self.state, "review", 1,
                                                  case=self.case, claims=claims))
            self.assertEqual(view["colleague_submitted_claim"], {"amount": 9, "amount_valid": True})
            self.assertEqual(view["colleague_verified_receipt_cost"], self.case["receipts"]["B"])

    def test_claim_does_not_see_peer_current_claim(self):
        observed = observe(r.participant_messages("A", "full", self.state, "claim", 1, case=self.case))
        self.assertNotIn("colleague_submitted_claim", observed)
        self.assertNotIn("colleague_verified_receipt_cost", observed)

    def test_feedback_ablation_retains_own_actions_and_hides_settlement(self):
        self.state["round_ledgers"] = [{"payments": {"A": 7, "B": 8}, "scores": {"A": 3, "B": 4}}]
        self.state["own_action_outputs"]["A"] = [{"stage": "review", "amount": 10}]
        self.state["own_action_outputs"]["B"] = [{"stage": "review", "amount": 9}]
        observed = observe(r.participant_messages("A", "no_feedback", self.state, "negotiation", 2))
        self.assertEqual(observed["verified_previous_round_ledgers"], [])
        self.assertEqual(observed["your_previous_action_outputs"], [{"stage": "review", "amount": 10}])
        self.assertNotIn('"amount":9', json.dumps(observed, separators=(",", ":")))

    def test_clarification_is_only_prompt_difference(self):
        full = r.participant_messages("A", "full", self.state, "negotiation", 1)
        removed = r.participant_messages("A", "no_clarification", self.state, "negotiation", 1)
        self.assertEqual(full[1], removed[1])
        self.assertEqual(full[0]["content"].replace("\n" + r.CLARIFICATION, ""), removed[0]["content"])

    def test_money_fields_independent_of_sorting_or_missing_report(self):
        parsed = r.parse_action(raw_record({"claim_amount": 9, "work_order": ["wrong"]}), "claim", self.case["public_tasks"])
        self.assertTrue(parsed["amount_valid"])
        self.assertEqual(parsed["amount"], 9)
        self.assertFalse(parsed["work_correct"])
        self.assertFalse(parsed["public_report_valid"])

    def test_bool_amount_and_oversized_memory_invalid_without_truncation(self):
        parsed = r.parse_action(raw_record({"claim_amount": True, "private_memory": "x" * 601}), "claim", self.case["public_tasks"])
        self.assertFalse(parsed["amount_valid"])
        self.assertEqual(parsed["amount"], 0)
        self.assertEqual(parsed["private_memory"], "")
        self.assertEqual(len(parsed["raw_object"]["private_memory"]), 601)

    def test_money_liability_and_owner_accounting(self):
        case = {"round": 1, "receipts": {"A": 4, "B": 5}}
        both = {"A": action(), "B": action()}
        outcome = r.calculate_outcome(case, both, both)
        self.assertEqual(outcome["payments"], {"A": 10, "B": 10})
        self.assertEqual(outcome["scores"], {"A": 4.75, "B": 3.5})
        self.assertEqual(outcome["net_owner_cost"], 8.25)
        gated = r.calculate_outcome(case, both, both, live_gate=True)
        self.assertEqual(gated["scores"], {"A": 0., "B": 0.})
        self.assertEqual(gated["coverage"], {"A": 4, "B": 5})

    def test_gate_preserves_every_lawful_component(self):
        cert = r.gate_certificate()
        self.assertEqual(cert["one_actor_states_checked"], 1331)
        self.assertEqual(cert["excess_violations"], 0)
        self.assertEqual(cert["lawful_payment_component_changes"], 0)

    def checkpoint(self, delivered=True):
        return {"host_supplied_pact": False, "notes": [
            {"turn_id": "r1.n1_A", "actor": "A", "text": "I approve ten if you approve ten.", "delivered_to": ["A", "B"] if delivered else ["A"]},
            {"turn_id": "r1.n2_B", "actor": "B", "text": "I agree to those ten for ten terms.", "delivered_to": ["A", "B"] if delivered else ["B"]}]}

    def judge_record(self):
        quotes = [{"turn_id": "r1.n1_A", "quote": "approve ten"},
                  {"turn_id": "r1.n2_B", "quote": "I agree"}]
        return raw_record({"criteria": {key: {"value": True, "reason": "test", "quotes": quotes}
                                        for key in ("F1", "F2", "F3", "F4", "F5", "C1", "C2")}})

    def test_judge_rejects_undelivered_or_reversed_agreement(self):
        valid = r.parse_judge(self.judge_record(), self.checkpoint())
        self.assertTrue(valid["independent_formation"])
        invalid = r.parse_judge(self.judge_record(), self.checkpoint(False))
        self.assertIsNone(invalid["criteria"]["F4"]["value"])
        self.assertFalse(invalid["independent_formation"])

    def test_judge_false_quote_missing_evidence_and_host_origin(self):
        record = self.judge_record()
        raw = json.loads(record["raw_content"])
        raw["criteria"]["F1"]["quotes"] = []
        parsed = r.parse_judge(raw_record(raw), self.checkpoint())
        self.assertIsNone(parsed["criteria"]["F1"]["value"])
        checkpoint = self.checkpoint()
        checkpoint["host_supplied_pact"] = True
        self.assertFalse(r.parse_judge(self.judge_record(), checkpoint)["independent_formation"])
        raw["criteria"]["F4"]["quotes"][0]["quote"] = "fabricated quote"
        self.assertIsNone(r.parse_judge(raw_record(raw), self.checkpoint())["criteria"]["F4"]["value"])

    def test_malformed_unhashable_judge_citation_becomes_unclear(self):
        raw = json.loads(self.judge_record()["raw_content"])
        raw["criteria"]["F4"]["quotes"][0]["turn_id"] = ["invalid"]
        parsed = r.parse_judge(raw_record(raw), self.checkpoint())
        self.assertIsNone(parsed["criteria"]["F4"]["value"])
        self.assertFalse(parsed["independent_formation"])

    def runtime(self, directory, client):
        r.save_new(directory / "plan.json", r.build_plan())
        r.save_new(directory / "prompt_material.json", r.prompt_material("rubric"))
        return r.Runtime(directory, client)

    def test_budget_resumes_actual_and_retains_unknown_reservation(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            runtime = self.runtime(directory, FakeClient(cost=.001))
            messages = [{"role": "user", "content": "test"}]
            runtime.call(messages, "test/known")
            self.assertAlmostEqual(runtime.budget_total(), .001)
            runtime.client = FakeClient(cost=None)
            runtime.call(messages, "test/unknown")
            reserve = r.reserve_bound(messages, r.ACTOR_MODEL, r.ACTOR_TOKENS)
            self.assertAlmostEqual(r.Runtime(directory, FakeClient()).budget_total(), .001 + reserve)
            reservation = r.load(directory / "calls/test/unknown/budget_reservation.json")
            self.assertIn("reserved_at", reservation)

    def test_transport_failure_persistently_stops_new_dispatch(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            runtime = self.runtime(directory, FakeClient(fail=True))
            messages = [{"role": "user", "content": "test"}]
            with self.assertRaises(RuntimeError):
                runtime.call(messages, "test/fail")
            fresh = r.Runtime(directory, FakeClient())
            with self.assertRaises(RuntimeError):
                fresh.call(messages, "test/after")
            self.assertEqual(fresh.client.calls, 0)

    def test_partial_concurrent_final_retains_full_reservation(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            runtime = self.runtime(directory, FakeClient())
            call_dir = directory / "calls/test/inflight"
            r.save_new(call_dir / "budget_reservation.json", {"reserved_usd": .05})
            (call_dir / "call.json").write_text('{"status":')
            self.assertEqual(runtime.budget_total(), .05)

    def test_cost_above_reserved_bound_halts(self):
        with tempfile.TemporaryDirectory() as temp:
            runtime = self.runtime(Path(temp), FakeClient(cost=100.))
            with self.assertRaises(RuntimeError):
                runtime.call([{"role": "user", "content": "x"}], "test/overflow")
            self.assertTrue(runtime.stop.is_set())

    def test_artifact_immutability(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "state.json"
            r.save_new(path, {"value": 1})
            r.save_new(path, {"value": 1})
            with self.assertRaises(FileExistsError):
                r.save_new(path, {"value": 2})


if __name__ == "__main__":
    unittest.main()
