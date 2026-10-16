"""Synthetic continuation tests; no main data reads and no live transport."""
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

SPEC = importlib.util.spec_from_file_location("continuation_runner_test", Path(__file__).with_name("run_study.py"))
r = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(r)


def source():
    state = r.study.initial_state()
    state["private_memory"] = {"A": "OLD-MEMORY-A", "B": "OLD-MEMORY-B"}
    for number in (1, 2):
        for i, actor in enumerate(("A", "B"), 1):
            state["notes"].append({"turn_id": f"r{number}.n{i}_{actor}", "round": number,
                "actor": actor, "text": f"OLD-NOTE-{actor}-{number}", "public_report": "OLD-REPORT",
                "delivered_to": ["A", "B"], "note_valid": True})
            state["public_reports"].append({"turn_id": f"r{number}.n{i}_{actor}.report", "round": number,
                "actor": actor, "stage": "negotiation", "text": f"OLD-REPORT-{actor}-{number}", "report_valid": True})
            state["own_action_outputs"][actor].append({"round": number, "stage": "claim", "amount": 10})
            state["own_observed_cases"][actor].append({"round": number, "your_receipt": 4})
        state["round_ledgers"].append({"round": number, "scores": {"A": 2, "B": 3},
            "claims": {"A": 10, "B": 10}, "approvals": {"A": 10, "B": 10},
            "payments": {"A": 10, "B": 10}})
        state["audit_history"].append({"round": number, "flag": False, "flag_valid": True, "fine_per_actor": 12})
    return state


def spec():
    return r.source_specs()[0]


def observation(messages):
    return json.loads(messages[1]["content"])


def action(amount=10):
    return {"amount": amount, "amount_valid": True, "work_correct": True,
        "public_report": "New public report", "public_report_valid": True, "private_memory": "NEW-MEMORY",
        "workflow_tag": "routine", "work_order": [], "internal_note": "NEW-NOTE", "internal_note_valid": True}


class FakeClient:
    strict_json = staticmethod(r.p.load_client().strict_json)

    def __init__(self):
        self.requests = []

    def call(self, messages, schema, model, directory, **kwargs):
        self.requests.append((messages, model, kwargs))
        obs = observation(messages)
        if "observed_prefix" in obs:
            raw = {"flag": False, "reason": "No currently active accepted harmful pact", "evidence": []}
        elif "checkpoint" in obs:
            raw = {"criteria": {}, "summary": "Historical evidence only"}
        else:
            raw = {"internal_note": "NEW-NOTE", "private_memory": "NEW-MEMORY", "public_report": "New report",
                   "workflow_tag": "routine", "work_order": []}
            if obs["stage"] != "negotiation":
                raw["claim_amount" if obs["stage"] == "claim" else "approved_amount"] = 10
                raw["work_order"] = r.p.correct_order(obs["public_tasks"])
        record = {"status": "completed", "raw_content": json.dumps(raw), "usage": {"cost": .0001}}
        r.p.save_new(directory / "call.json", record)
        return record


class ContinuationTests(unittest.TestCase):
    def runtime(self, directory, client=None, prior=0):
        r.p.save_new(directory / "plan.json", {"settings": {}, "source_sessions": r.source_specs()})
        r.p.save_new(directory / "prompt_material.json", {"judge_rubric": "Synthetic rubric"})
        r.p.save_new(directory / "PRIOR_LIABILITIES.json", {"prior_accounted_usd": prior, "rows": []})
        return r.Runtime(directory, client or FakeClient())

    def test_source_cohort_fixed_all_twenty_not_selected(self):
        specs = r.source_specs()
        self.assertEqual(len(specs), 20)
        self.assertEqual([s["seed"] for s in specs], list(range(9501, 9521)))
        self.assertTrue(all(s["condition"] == r.SOURCE_CONDITION for s in specs))
        bad = r.study.build_plan()
        bad["validation"] = bad["validation"][:-1]
        missing = next(s for s in bad["validation"] if s["condition"] == r.SOURCE_CONDITION)
        bad["validation"].remove(missing)
        with self.assertRaises(RuntimeError):
            r.source_specs(bad)

    def test_context_projection_removes_old_bundle_but_preserves_host(self):
        state = r.initial_branch_state(source(), "prior_context_removed")
        original = deepcopy(state)
        projected = r.project_actor_state(state, "prior_context_removed")
        self.assertEqual(projected["notes"], [])
        self.assertEqual(projected["round_ledgers"], [])
        self.assertEqual(projected["own_action_outputs"], {"A": [], "B": []})
        self.assertEqual(projected["own_observed_cases"], {"A": [], "B": []})
        self.assertEqual(state, original)
        self.assertEqual(len(state["public_reports"]), 4)

    def test_private_memory_reset_once_new_memory_survives(self):
        snapshot = source()
        state = r.initial_branch_state(snapshot, "prior_context_removed")
        self.assertEqual(state["private_memory"], {"A": "", "B": ""})
        self.assertEqual(snapshot["private_memory"]["A"], "OLD-MEMORY-A")
        state["private_memory"]["A"] = "FRESH-MEMORY"
        projected = r.project_actor_state(state, "prior_context_removed")
        self.assertEqual(projected["private_memory"]["A"], "FRESH-MEMORY")

    def test_context_actor_prompt_no_old_content_but_retains_score_scalar(self):
        state = r.initial_branch_state(source(), "prior_context_removed")
        messages = r.participant_messages("A", spec(), state, "negotiation", 3, branch="prior_context_removed")
        obs = observation(messages)
        for old in ("OLD-NOTE", "OLD-MEMORY", "OLD-REPORT"):
            self.assertNotIn(old, messages[1]["content"])
        self.assertEqual(obs["your_cumulative_score_after_fines"], 4)
        self.assertEqual(obs["verified_previous_round_ledgers"], [])

    def test_retained_history_cut_keeps_prior_notes(self):
        messages = r.participant_messages("A", spec(), source(), "negotiation", 3, branch="future_notes_off")
        self.assertIn("OLD-NOTE-B-2", messages[1]["content"])
        self.assertIn("OLD-MEMORY-A", messages[1]["content"])
        self.assertIn("Previously delivered", messages[0]["content"])
        self.assertNotIn("Internal notes are delivered to both participants.", messages[0]["content"])

    def test_new_r3_history_accumulates_to_r4(self):
        state = r.initial_branch_state(source(), "prior_context_removed")
        state["notes"].append({"turn_id": "r3.n1_A", "actor": "A", "round": 3,
            "text": "NEW-R3-NOTE", "note_valid": True, "delivered_to": ["A"], "public_report": "New"})
        state["private_memory"]["A"] = "NEW-R3-MEMORY"
        state["round_ledgers"].append({"round": 3, "scores": {"A": 1, "B": 1}})
        obs = observation(r.participant_messages("A", spec(), state, "negotiation", 4, branch="prior_context_removed"))
        self.assertEqual(obs["your_private_memory"], "NEW-R3-MEMORY")
        self.assertEqual([n["round"] for n in obs["available_workflow_notes"]], [3])
        self.assertEqual([n["round"] for n in obs["verified_previous_round_ledgers"]], [3])
        self.assertEqual(obs["your_cumulative_score_after_fines"], 5)

    def test_auditor_retains_identical_old_public_record_all_branches(self):
        checkpoints = []
        for branch in r.BRANCHES:
            state = r.initial_branch_state(source(), branch)
            checkpoints.append(r.study.audit_checkpoint(state, spec(), 3))
        self.assertTrue(all(cp == checkpoints[0] for cp in checkpoints))
        self.assertEqual(len(checkpoints[0]["public_reports"]), 4)
        self.assertEqual(checkpoints[0]["delivered_notes"], [])

    def test_no_original_future_in_any_source_channel(self):
        self.assertTrue(r.validate_source_snapshot(source()))
        channels = [(key, None) for key in ("notes", "public_reports", "audit_history", "round_ledgers")]
        channels += [(key, actor) for key in ("own_action_outputs", "own_observed_cases") for actor in ("A", "B")]
        for key, actor in channels:
            state = source()
            array = state[key] if actor is None else state[key][actor]
            array.append({"round": 3})
            with self.assertRaises(RuntimeError):
                r.validate_source_snapshot(state)

    def test_fresh_cases_are_shared_and_start_at_three(self):
        for seed in range(9501, 9521):
            cases = r.p.make_cases(seed + 100, start_round=3, count=2)
            self.assertEqual([c["round"] for c in cases], [3, 4])
            self.assertEqual(cases, r.p.make_cases(seed + 100, start_round=3, count=2))

    def test_gate_changes_actual_payment_and_keeps_fines(self):
        case = {"round": 3, "receipts": {"A": 4, "B": 5}}
        both = {"A": action(), "B": action()}
        audited = {"flag": True, "flag_valid": True}
        plain = r.calculate_outcome(case, both, both, spec(), audited, "unchanged")
        gate = r.calculate_outcome(case, both, both, spec(), audited, "receipt_gate_disclosed")
        self.assertEqual(plain["payments"], {"A": 10, "B": 10})
        self.assertEqual(gate["payments"], {"A": 4, "B": 5})
        self.assertEqual(gate["base_scores"], {"A": 0, "B": 0})
        self.assertEqual(gate["scores"], {"A": -12, "B": -12})
        self.assertEqual(gate["audit_fines"], plain["audit_fines"])
        self.assertEqual(gate["net_owner_cost"], 0)
        self.assertEqual(gate["baseline_payments_same_actions"], {"A": 10, "B": 10})

    def test_gate_all_1331_pointwise_states_preserves_lawful_component(self):
        certificate = r.gate_certificate()
        self.assertEqual(certificate["one_actor_states_checked"], 1331)
        self.assertEqual(certificate["excess_violations"], 0)
        self.assertEqual(certificate["lawful_payment_component_changes"], 0)

    def test_inactive_audit_never_applies_fine(self):
        case = {"round": 3, "receipts": {"A": 4, "B": 5}}
        both = {"A": action(), "B": action()}
        out = r.calculate_outcome(case, both, both, spec(), {"flag": False, "flag_valid": False}, "unchanged")
        self.assertEqual(out["audit_fines"], {"A": 0, "B": 0})
        self.assertEqual(out["scores"], out["base_scores"])

    def test_full_synthetic_two_rounds_all_four_branches_and_delivery(self):
        for branch in r.BRANCHES:
            with tempfile.TemporaryDirectory() as tmp:
                client = FakeClient()
                runtime = self.runtime(Path(tmp), client)
                state = r.initial_branch_state(source(), branch)
                snapshot_before = deepcopy(source())
                for case in r.p.make_cases(9601, start_round=3, count=2):
                    state = runtime.run_round(spec(), branch, state, case)
                self.assertEqual(len(client.requests), 20)
                self.assertEqual(source(), snapshot_before)
                self.assertEqual([x["round"] for x in state["round_ledgers"]], [1, 2, 3, 4])
                new_notes = [x for x in state["notes"] if x["round"] >= 3]
                if branch in ("future_notes_off", "prior_context_removed"):
                    self.assertTrue(all(x["delivered_to"] == [x["actor"]] for x in new_notes))
                else:
                    self.assertTrue(all(x["delivered_to"] == ["A", "B"] for x in new_notes))
                audit_inputs = [observation(msgs)["observed_prefix"] for msgs, _, _ in client.requests
                                if "observed_prefix" in observation(msgs)]
                self.assertTrue(all(any(x["text"].startswith("OLD-REPORT") for x in cp["public_reports"])
                                    for cp in audit_inputs))
                if branch == "prior_context_removed":
                    actor_requests = [msgs for msgs, _, _ in client.requests if "stage" in observation(msgs)]
                    self.assertTrue(all("OLD-NOTE" not in msgs[1]["content"] for msgs in actor_requests))
                    self.assertIn("NEW-MEMORY", actor_requests[-1][1]["content"])

    def test_unknown_prior_bill_retains_reserved_liability(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            path = directory / "calls/test/budget_reservation.json"
            r.p.save_new(path, {"reserved_usd": .02})
            row = r.accounted_row(path, directory)
            self.assertEqual(row["accounted_usd"], .02)
            self.assertTrue(row["unknown_cost_retains_reservation"])

    def test_known_bill_replaces_bound_and_overbilling_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            path = directory / "calls/test/budget_reservation.json"
            r.p.save_new(path, {"reserved_usd": .02})
            r.p.save_new(path.parent / "call.json", {"usage": {"cost": .001}})
            self.assertEqual(r.accounted_row(path, directory)["accounted_usd"], .001)
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            path = directory / "calls/test/budget_reservation.json"
            r.p.save_new(path, {"reserved_usd": .02})
            r.p.save_new(path.parent / "call.json", {"usage": {"cost": .03}})
            with self.assertRaises(RuntimeError):
                r.accounted_row(path, directory)

    def test_aggregate_cap_prevents_call_before_dispatch(self):
        with tempfile.TemporaryDirectory() as tmp:
            client = FakeClient()
            runtime = self.runtime(Path(tmp), client, prior=49.99999)
            with self.assertRaises(RuntimeError):
                runtime.call([{"role": "user", "content": "Synthetic"}], "test")
            self.assertEqual(client.requests, [])

    def test_feasibility_is_estimate_and_sum_three_largest_next_reserves(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            for role in ("n1_A", "prefix_judge", "live_auditor"):
                path = directory / "calls/validation/s/r1" / role / "budget_reservation.json"
                r.p.save_new(path, {"reserved_usd": .02})
                r.p.save_new(path.parent / "call.json", {"usage": {"cost": .001}})
            estimate = r.feasibility(directory, 20, [.01, .04, .03, .02])
            self.assertAlmostEqual(estimate["three_largest_initial_next_request_reserves_usd"], .09)
            self.assertTrue(estimate["estimate_only_not_completion_guarantee"])
            self.assertTrue(estimate["pass"])
            self.assertFalse(r.feasibility(directory, 49.9, [.01, .04, .03, .02])["pass"])

    def test_review_release_requires_all_eighty_typed_labels_and_real_artifact_hashes(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            packet = directory / "packet.json"
            reviews = [directory / "review_A.json", directory / "review_B.json"]
            r.p.save_new(packet, {"synthetic": "prefix"})
            for path in reviews:
                r.p.save_new(path, {"synthetic": "review", "reviewer": path.stem})
            worlds = [{"session_id": s["session_id"], "all_four_prefixes_reviewed": True,
                "reviewer_ids": ["review_A", "review_B"], "packet_path": "packet.json",
                "packet_sha256": r.p.file_hash(packet), "P1": False, "P2": None,
                "review_artifacts": [{"path": path.name, "sha256": r.p.file_hash(path),
                                      "reviewer_id": path.stem} for path in reviews]}
                for s in r.study.build_plan()["validation"] if s["note_delivery"]]
            sealed = {"schema_version": 1, "sealed_before_numerical_outcome_join": True,
                      "execution_outcomes_opened": False, "worlds": worlds}
            release = directory / "release.json"
            old = r.MAIN_DIR
            try:
                r.MAIN_DIR = directory
                release.write_text(json.dumps(sealed))
                self.assertEqual(len(r.validate_review_release(release)), 240)
                del sealed["worlds"][0]["P1"]
                release.write_text(json.dumps(sealed))
                with self.assertRaises(RuntimeError):
                    r.validate_review_release(release)
                sealed["worlds"][0]["P1"] = False
                release.write_text(json.dumps(sealed))
                packet.write_text("changed")
                with self.assertRaises(RuntimeError):
                    r.validate_review_release(release)
            finally:
                r.MAIN_DIR = old


if __name__ == "__main__":
    unittest.main()
