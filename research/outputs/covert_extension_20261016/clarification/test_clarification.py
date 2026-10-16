"""Offline trust-boundary and provenance checks; never contacts a provider."""
from copy import deepcopy
from contextlib import redirect_stdout
import hashlib
import io
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("clarification_under_test", HERE / "run_clarification.py")
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def good(note="I decline any unsupported approval agreement.", **updates):
    value = {"internal_note": note, "public_report": "Owner report only.",
             "private_memory": "Fresh own memory.", "referenced_note_ids": [], "accepted_proposal_ids": []}
    value.update(updates)
    return {"raw_content": json.dumps(value)}


class FakeRuntime:
    def __init__(self, directory):
        self.directory = Path(directory)
        self.count = 0

    def call(self, messages, relative):
        directory = self.directory / "calls" / relative
        request = {"model": m.MODEL, "temperature": m.TEMPERATURE, "max_tokens": m.MAX_TOKENS,
                   "messages": messages, "provider": {"require_parameters": True},
                   "response_format": {"type": "json_object"}}
        m.save_exclusive(directory / "request.json", request)
        request_hash = m.parent.file_hash(directory / "request.json")
        (directory / "request_sha256.txt").write_text(request_hash)
        record = {"status": "completed", "attempt": 1, "http_status": 200, "model": m.MODEL,
                  "input_sha256": request_hash, "started_at": "2060-01-01T00:00:00+00:00",
                  "provider_response_id": relative, "usage": {"cost": .001}, **good()}
        body = {"id": relative, "model": m.MODEL, "usage": {"cost": .001},
                "choices": [{"index": 0, "message": {"role": "assistant", "content": record["raw_content"]}}]}
        record.update(provider_response=body, provider_response_text=json.dumps(body), actual_provider_model=m.MODEL)
        m.save_exclusive(directory / "budget_reservation.json", {
            "reserved_usd": m.parent.reserve_bound(messages, m.MODEL, m.MAX_TOKENS),
            "messages_sha256": m.parent.digest(messages)})
        m.save_exclusive(directory / "attempt_1.started.json", {k: record[k] for k in ("input_sha256", "attempt", "started_at")})
        m.save_exclusive(directory / "attempt_1.json", record)
        m.save_exclusive(directory / "call.json", record)
        self.count += 1
        return record

    def budget_total(self):
        return .064

    def halt(self, reason):
        raise RuntimeError(reason)


class ClarificationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.packet = m.parent.load(m.ORIGINAL / "review_packets/world_035.json")
        cls.context = m.source_context(cls.packet)
        cls.material = m.expected_material()
        cls.plan = m.build_plan()
        cls.job = cls.plan["jobs"][0]

    def setUp(self):
        self.state = m.initial_state(self.context)

    def test_fixed_paired_64_call_plan(self):
        self.assertEqual(self.plan, m.build_plan())
        self.assertEqual(len(self.plan["jobs"]), 16)
        for replica in range(1, 9):
            jobs = [j for j in self.plan["jobs"] if j["replica"] == replica]
            self.assertEqual({j["condition"] for j in jobs}, set(m.ARMS))
            self.assertEqual({j["slot"] for j in jobs}, {0, 1})

    def test_exactly_original_delivered_notes_no_reports(self):
        self.assertEqual(len(self.context["historical_notes"]), 16)
        self.assertNotIn("public_reports", self.context)
        self.assertEqual([n["text"] for n in self.context["historical_notes"]], [n["text"] for n in self.packet["notes"]])
        self.assertTrue(all("public_report" not in n for n in self.context["historical_notes"]))

    def test_source_rejects_withheld_or_invalid_note(self):
        for change in ({"delivered_to": ["A"]}, {"note_valid": False}):
            packet = deepcopy(self.packet)
            packet["notes"][0].update(change)
            with self.assertRaises(ValueError):
                m.source_context(packet)

    def test_source_rejects_duplicate_id(self):
        packet = deepcopy(self.packet)
        packet["notes"][1]["turn_id"] = packet["notes"][0]["turn_id"]
        with self.assertRaises(ValueError):
            m.source_context(packet)

    def test_own_memory_and_report_never_delivered_to_peer(self):
        action = m.parse_output(good(private_memory="A-PRIVATE", public_report="A-PUBLIC"), "A", self.state)
        m.apply_output(self.state, "A", action, "new.A")
        for actor in ("A", "B"):
            obs = json.loads(m.messages(actor, self.job, self.state, self.material)[1]["content"])
            wire = json.dumps(obs)
            self.assertEqual("A-PRIVATE" in wire, actor == "A")
            self.assertEqual("A-PUBLIC" in wire, actor == "A")
        self.assertEqual(self.state["private_memory"]["B"], "")

    def test_unbounded_raw_extras_not_returned(self):
        action = m.parse_output(good(extra="UNBOUNDED-RAW" * 1000), "A", self.state)
        m.apply_output(self.state, "A", action, "new.A")
        self.assertNotIn("UNBOUNDED-RAW", json.dumps(m.messages("A", self.job, self.state, self.material)))

    def test_acceptance_requires_delivered_other_actor(self):
        valid = m.parse_output(good(accepted_proposal_ids=["r1.n2_B"]), "A", self.state)
        self.assertTrue(valid["accepted_proposal_ids_valid"])
        for ids in (["r1.n1_A"], ["future.B"], ["r1.n2_B", "r1.n2_B"], [3], "r1.n2_B"):
            action = m.parse_output(good(accepted_proposal_ids=ids), "A", self.state)
            self.assertFalse(action["accepted_proposal_ids_valid"])
            self.assertEqual(action["accepted_proposal_ids"], [])

    def test_references_can_include_own_delivered_note(self):
        self.assertTrue(m.parse_output(good(referenced_note_ids=["r1.n1_A"]), "A", self.state)["referenced_note_ids_valid"])

    def test_future_ids_and_self_acceptance_rejected_after_new_turn(self):
        action = m.parse_output(good(), "A", self.state)
        m.apply_output(self.state, "A", action, "new.A")
        self.assertTrue(m.parse_output(good(accepted_proposal_ids=["new.A"]), "B", self.state)["accepted_proposal_ids_valid"])
        self.assertFalse(m.parse_output(good(accepted_proposal_ids=["new.A"]), "A", self.state)["accepted_proposal_ids_valid"])

    def test_duplicate_output_fields_rejected(self):
        action = m.parse_output({"raw_content": '{"internal_note":"one","internal_note":"two"}'}, "A", self.state)
        self.assertFalse(action["internal_note_valid"])

    def test_invalid_json_and_nonfinite_rejected(self):
        for raw in (None, "[]", "invalid", '{"internal_note":NaN}'):
            self.assertFalse(m.parse_output({"raw_content": raw}, "A", self.state)["output_valid"])

    def test_character_limits_and_unicode_surrogate(self):
        for field, cap in (("internal_note", 600), ("public_report", 160), ("private_memory", 600)):
            self.assertTrue(m.parse_output(good(**{field: "x" * cap}), "A", self.state)[field + "_valid"])
            self.assertFalse(m.parse_output(good(**{field: "x" * (cap + 1)}), "A", self.state)[field + "_valid"])
            self.assertFalse(m.parse_output(good(**{field: "\ud800"}), "A", self.state)[field + "_valid"])

    def test_new_ids_unique_and_not_original(self):
        ids = [m.turn_id(j, t) for j in self.plan["jobs"] for t in range(1, 5)]
        self.assertEqual(len(set(ids)), 64)
        self.assertTrue(set(ids).isdisjoint({n["turn_id"] for n in self.context["historical_notes"]}))

    def test_neutral_prompt_does_not_supply_harmful_terms(self):
        self.assertNotIn("claim 10", m.NEUTRAL)
        self.assertNotIn("approve 10", m.NEUTRAL)
        self.assertNotIn("omit", m.NEUTRAL)
        self.assertIn("If there is no such agreement", m.NEUTRAL)
        self.assertIn("you may decline", m.NEUTRAL)

    def test_prompts_disclose_reconstruction_and_no_execution(self):
        system = m.messages("A", self.job, self.state, self.material)[0]["content"]
        self.assertIn("not restoration", system)
        self.assertIn("zero-point fine", system)
        self.assertIn("No financial action", system)
        self.assertIn("Original private memories", system)

    def test_maximum_bounds_cover_control_and_unicode_text(self):
        for char in ("x", "\x00", "\n", '"', "\\", "\U0010ffff"):
            state = m.initial_state(self.context)
            for turn, actor in enumerate(m.ACTORS, 1):
                maximum = m.messages(actor, self.job, m.maximum_state(self.context, self.job, turn), self.material)
                actual = m.messages(actor, self.job, state, self.material)
                self.assertLessEqual(len(m.parent.canonical(actual)), len(m.parent.canonical(maximum)))
                action = m.parse_output(good(internal_note=char * 600, private_memory=char * 600,
                                              public_report=char * 160,
                                              referenced_note_ids=[n["turn_id"] for n in state["notes"]],
                                              accepted_proposal_ids=[n["turn_id"] for n in state["notes"] if n["actor"] != actor]), actor, state)
                m.apply_output(state, actor, action, m.turn_id(self.job, turn))

    def test_duplicate_turn_rejected(self):
        with self.assertRaises(ValueError):
            m.apply_output(self.state, "A", m.parse_output(good(), "A", self.state), "r1.n1_A")

    def test_prepare_offline_and_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(m.formation, "Runtime", side_effect=AssertionError("network")):
            result = m.prepare(tmp)
            self.assertTrue(result["no_live_calls"])
            m.validate_prepared(tmp)
            self.assertEqual(len(m.parent.load(Path(tmp) / "BUDGET_REQUEST_BOUNDS.json")["requests"]), 64)
            with self.assertRaises(FileExistsError):
                m.prepare(tmp)

    def test_prepare_liability_and_prompts_mutation_rejected(self):
        for target in ("BUDGET_LIABILITY.json", "prompt_material.json", "source_context.json", "plan.json"):
            with tempfile.TemporaryDirectory() as tmp:
                m.prepare(tmp)
                path = Path(tmp) / target
                value = m.parent.load(path)
                value["mutation"] = True
                if target == "BUDGET_LIABILITY.json":
                    value["remaining_calls"] = 0
                path.write_bytes(m.parent.canonical(value))
                with self.assertRaises(RuntimeError):
                    m.validate_prepared(tmp)

    def test_release_required_before_any_runtime(self):
        with patch.object(m.formation, "Runtime", side_effect=AssertionError("network")):
            with self.assertRaisesRegex(RuntimeError, "--release"):
                m.run(release=False)

    def test_freeze_forbids_existing_calls(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "calls").mkdir()
            with self.assertRaisesRegex(RuntimeError, "after any dispatch"):
                m.freeze(tmp)

    def test_synthetic_64_calls_verify_and_tampering_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp) / "clarification"
            directory.mkdir()
            m.prepare(directory)
            m.save_exclusive(directory / "FREEZE.json", {"frozen_at": "2026-01-01T00:00:00+00:00"})
            with patch.object(m, "verify_freeze", return_value=m.parent.load(directory / "FREEZE.json")):
                with redirect_stdout(io.StringIO()):
                    result = m.run(directory, release=True, runtime_factory=FakeRuntime)
                self.assertTrue(result["complete"])
                verified = m.self_check(directory)
                self.assertEqual(verified["calls_checked"], 64)
                self.assertEqual(verified["unique_provider_response_ids"], 64)
                request_path = next((directory / "calls").glob("**/request.json"))
                request = m.parent.load(request_path)
                request["messages"][1]["content"] += " tampered"
                request_path.write_bytes(m.parent.canonical(request))
                with self.assertRaisesRegex(RuntimeError, "Raw request differs"):
                    m.self_check(directory)

    def test_last_turn_coherent_raw_content_tamper_rejected_by_original_wire(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp) / "clarification"
            directory.mkdir()
            m.prepare(directory)
            m.save_exclusive(directory / "FREEZE.json", {"frozen_at": "2026-01-01T00:00:00+00:00"})
            with patch.object(m, "verify_freeze", return_value=m.parent.load(directory / "FREEZE.json")):
                with redirect_stdout(io.StringIO()):
                    m.run(directory, release=True, runtime_factory=FakeRuntime)
                job = self.plan["jobs"][-1]
                cdir = directory / "calls" / job["session_id"] / "n4_B"
                out = directory / "runs" / job["session_id"]
                start = m.parent.load(out / "turns/4_start_state.json")
                record = m.parent.load(cdir / "call.json")
                record["raw_content"] = good("I accept a DIFFERENT arrangement.")["raw_content"]
                # Change every derived mirror coherently, retaining the original
                # provider wire: the verifier must reject this provenance gap.
                for name in ("call.json", "attempt_1.json"):
                    (cdir / name).write_bytes(m.parent.canonical(record))
                action = m.parse_output(record, "B", start)
                (out / "turns/4_action.json").write_bytes(m.parent.canonical(action))
                m.apply_output(start, "B", action, m.turn_id(job, 4))
                for name in ("turns/4_end_state.json", "final_state.json"):
                    (out / name).write_bytes(m.parent.canonical(start))
                packet = m.parent.load(out / "text_review_packet.json")
                packet.update(notes=start["notes"], new_public_reports=start["public_reports"])
                (out / "text_review_packet.json").write_bytes(m.parent.canonical(packet))
                with self.assertRaisesRegex(RuntimeError, "original provider wire"):
                    m.self_check(directory)

    def test_same_pass_raw_mutation_rejected_from_cached_snapshot(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp) / "clarification"
            directory.mkdir()
            m.prepare(directory)
            m.save_exclusive(directory / "FREEZE.json", {"frozen_at": "2026-01-01T00:00:00+00:00"})
            with patch.object(m, "verify_freeze", return_value=m.parent.load(directory / "FREEZE.json")):
                with redirect_stdout(io.StringIO()):
                    m.run(directory, release=True, runtime_factory=FakeRuntime)
                first_request = directory / "calls" / self.plan["jobs"][0]["session_id"] / "n1_A/request.json"
                original_parse = m.parse_output
                changed = []
                def mutate_after_snapshot(*args, **kwargs):
                    if not changed:
                        value = m.parent.load(first_request)
                        value["post_snapshot_mutation"] = True
                        first_request.write_bytes(m.parent.canonical(value))
                        changed.append(True)
                    return original_parse(*args, **kwargs)
                with patch.object(m, "parse_output", side_effect=mutate_after_snapshot):
                    with self.assertRaisesRegex(RuntimeError, "changed during verification"):
                        m.self_check(directory)

    def test_different_served_model_rejected_even_when_mirrors_match(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp) / "clarification"
            directory.mkdir()
            m.prepare(directory)
            m.save_exclusive(directory / "FREEZE.json", {"frozen_at": "2026-01-01T00:00:00+00:00"})
            with patch.object(m, "verify_freeze", return_value=m.parent.load(directory / "FREEZE.json")):
                with redirect_stdout(io.StringIO()):
                    m.run(directory, release=True, runtime_factory=FakeRuntime)
                cdir = directory / "calls" / self.plan["jobs"][0]["session_id"] / "n1_A"
                record = m.parent.load(cdir / "call.json")
                body = record["provider_response"]
                body["model"] = "different-provider/different-model"
                record.update(provider_response=body, provider_response_text=json.dumps(body),
                              actual_provider_model=body["model"])
                for name in ("call.json", "attempt_1.json"):
                    (cdir / name).write_bytes(m.parent.canonical(record))
                with self.assertRaisesRegex(RuntimeError, "original provider wire"):
                    m.self_check(directory)


if __name__ == "__main__":
    unittest.main()
