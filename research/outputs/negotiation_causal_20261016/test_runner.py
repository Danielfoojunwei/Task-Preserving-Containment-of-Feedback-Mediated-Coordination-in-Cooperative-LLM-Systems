"""Offline adapter checks; no API calls."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

_spec = importlib.util.spec_from_file_location("negotiation_adapter", Path(__file__).with_name("run_study.py"))
r = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(r)
p = r.parent


class AdapterTests(unittest.TestCase):
    def test_plain_request_identical_to_parent_full(self):
        state = p.initial_state()
        case = p.make_cases(9301)[0]
        claims = {a: {"amount": 10, "amount_valid": True, "workflow_tag": "tag",
                      "public_report": "report", "work_order": []} for a in ("A", "B")}
        for stage in ("negotiation", "claim", "review"):
            kwargs = {} if stage == "negotiation" else {"case": case}
            if stage == "review":
                kwargs["claims"] = claims
            self.assertEqual(r.participant_messages("A", "plain", state, stage, 1, **kwargs),
                             p.participant_messages("A", "full", state, stage, 1, **kwargs))

    def test_directed_only_appends_declared_negotiation_instruction(self):
        state = p.initial_state()
        plain = r.participant_messages("B", "plain", state, "negotiation", 1)
        directed = r.participant_messages("B", "directed", state, "negotiation", 1)
        self.assertEqual(plain[0], directed[0])
        plain_observation = json.loads(plain[1]["content"])
        directed_observation = json.loads(directed[1]["content"])
        expected = plain_observation["instruction"] + " " + r.NEGOTIATION_PARAGRAPH
        self.assertEqual(directed_observation.pop("instruction"), expected)
        plain_observation.pop("instruction")
        self.assertEqual(plain_observation, directed_observation)
        case = p.make_cases(9301)[0]
        self.assertEqual(r.participant_messages("A", "directed", state, "claim", 1, case=case),
                         r.participant_messages("A", "plain", state, "claim", 1, case=case))

    def test_no_notes_never_relays_peer_text_or_routing_metadata(self):
        state = p.initial_state()
        state["notes"] = [{"turn_id": "r1.n1_B", "actor": "B", "round": 1,
                           "text": "PEER-WITHHELD", "public_report": "OWNER-ONLY",
                           "delivered_to": ["B"], "note_valid": True},
                          {"turn_id": "r1.n2_A", "actor": "A", "round": 1,
                           "text": "OWN-RETAINED", "public_report": "OWNER-ONLY",
                           "delivered_to": ["A"], "note_valid": True}]
        state["private_memory"]["B"] = "PEER-PRIVATE-MEMORY"
        payload = r.participant_messages("A", "directed_no_notes", state, "negotiation", 2)[1]["content"]
        self.assertNotIn("PEER-WITHHELD", payload)
        self.assertNotIn("PEER-PRIVATE-MEMORY", payload)
        self.assertNotIn("OWNER-ONLY", payload)
        self.assertNotIn("delivered_to", payload)
        self.assertIn("OWN-RETAINED", payload)
        delivered = r.participant_messages("A", "directed", p.initial_state(), "negotiation", 1)
        withheld = r.participant_messages("A", "directed_no_notes", p.initial_state(), "negotiation", 1)
        self.assertEqual(delivered, withheld)

    def test_eight_matched_three_arm_blocks_and_call_budget(self):
        plan = r.build_plan()
        self.assertEqual(plan, r.build_plan())
        self.assertEqual(len(plan["validation"]), 24)
        for block in range(9301, 9309):
            group = [s for s in plan["validation"] if s["block_id"] == block]
            self.assertEqual({s["condition"] for s in group}, set(r.ARMS))
            self.assertEqual({s["slot"] for s in group}, set(range(3)))
            self.assertEqual(len(plan["cases"][str(block)]), 4)
        settings = plan["settings"]
        self.assertEqual(settings["actor_calls_per_pair"], 32)
        self.assertEqual(settings["prefix_judge_calls_per_pair"], 4)
        self.assertEqual(settings["logical_calls_max"], 24 * (32 + 4))
        self.assertEqual(settings["cap_usd"], 10.)
        self.assertEqual(settings["aggregate_authorization_usd"], 35.)

    def test_actual_round_engine_uses_no_notes_physics_and_exact_call_count(self):
        class FakeRuntime(r.Runtime):
            def __init__(self, directory):
                self.directory = directory
                self.calls = []

            def actor(self, actor, spec, state, stage, round_number, relative, **kwargs):
                self.calls.append(("actor", actor, stage))
                messages = r.participant_messages(actor, spec["study_arm"], state, stage, round_number,
                                                 **kwargs)
                self.last_messages = messages
                return {"amount": 10, "amount_valid": True, "public_report": "owner",
                        "private_memory": "own", "internal_note": "note",
                        "internal_note_valid": True, "workflow_tag": "", "work_order": [],
                        "work_correct": False}

            def judge(self, checkpoint, relative):
                self.calls.append(("judge", None, None))
                self.checkpoint = checkpoint
                return {"independent_formation": False}

        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            runtime = FakeRuntime(directory)
            spec = {"session_id": "test", "condition": "directed_no_notes"}
            state = p.initial_state()
            for case in p.make_cases(9301):
                state = runtime.run_round("validation", spec, state, case)
            self.assertEqual(sum(kind == "actor" for kind, *_ in runtime.calls), 32)
            self.assertEqual(sum(kind == "judge" for kind, *_ in runtime.calls), 4)
            self.assertTrue(all(note["delivered_to"] == [note["actor"]] for note in state["notes"]))

    def test_local_cap_is_ten_and_parent_source_unchanged(self):
        self.assertEqual(p.CAP_USD, 10.)
        self.assertIn("CAP_USD = 25.0", r.PARENT_PATH.read_text())
        class FakeClient:
            def call(self, *args, **kwargs):
                raise AssertionError("Budget rejection must precede transport")
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            p.save_new(directory / "plan.json", r.build_plan())
            p.save_new(directory / "prompt_material.json", {"judge_rubric": "test"})
            p.save_new(directory / "calls/prior/budget_reservation.json", {"reserved_usd": 9.999999})
            runtime = r.Runtime(directory, FakeClient())
            with self.assertRaises(RuntimeError):
                runtime.call([{"role": "user", "content": "test"}], "new")


if __name__ == "__main__":
    unittest.main()
