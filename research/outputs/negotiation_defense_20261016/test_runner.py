"""Offline source-state, branch-isolation and gate tests."""
import importlib.util
from pathlib import Path
import tempfile
import unittest

_spec = importlib.util.spec_from_file_location("defense_adapter", Path(__file__).with_name("run_study.py"))
r = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(r)
p = r.parent


def source_plan():
    return {"validation": [{"session_id": f"source_{b}", "condition": "directed", "seed": b,
                             "block_id": b, "slot": 0} for b in range(9301, 9309)]}


def source_state():
    state = p.initial_state()
    state["round_ledgers"] = [{"round": 1}, {"round": 2}]
    state["notes"] = [{"turn_id": "r2.n1_A", "actor": "A", "round": 2,
                       "text": "OLD-PACT", "public_report": "owner-only",
                       "delivered_to": ["A", "B"], "note_valid": True}]
    return state


class DefenseTests(unittest.TestCase):
    def test_all_sources_all_branches_fresh_matched_cases_and_432_calls(self):
        plan = r.build_plan(source_plan(), lambda _: "0" * 64)
        self.assertEqual(len(plan["sources"]), 8)
        self.assertEqual(len(plan["jobs"]), 24)
        self.assertEqual(plan, r.build_plan(source_plan(), lambda _: "0" * 64))
        for source in plan["sources"]:
            jobs = [j for j in plan["jobs"] if j["session_id"] == source["session_id"]]
            self.assertEqual({j["branch"] for j in jobs}, set(r.BRANCHES))
            self.assertEqual(plan["continuation_cases"][str(source["seed"])],
                             p.make_cases(source["seed"] + 100, 3, 2))
        self.assertEqual(plan["settings"]["logical_calls_max"], 8 * 3 * 2 * 9)
        self.assertEqual(plan["settings"]["cap_usd"], 5.)
        self.assertEqual(plan["settings"]["aggregate_authorization_usd"], 40.)

    def test_exact_source_snapshot_no_reconstructed_summary(self):
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp) / "original.json"
            target = Path(temp) / "source.json"
            source.write_bytes(b'{ "only_rounds": [1,2], "private_memory": "exact bytes" }\n')
            expected = p.file_hash(source)
            r.copy_snapshot(source, target, expected)
            self.assertEqual(target.read_bytes(), source.read_bytes())
            self.assertEqual(p.file_hash(target), expected)
            target.write_text("changed")
            with self.assertRaises(RuntimeError):
                r.copy_snapshot(source, target, expected)

    def test_source_rejects_round3_or4_state(self):
        state = source_state()
        self.assertIs(r.validate_source_state(state), state)
        state["own_action_outputs"]["A"].append({"round": 3})
        with self.assertRaises(ValueError):
            r.validate_source_state(state)
        state = source_state()
        state["notes"].append({"round": 4})
        with self.assertRaises(ValueError):
            r.validate_source_state(state)

    def test_actual_engine_future_cut_keeps_old_pact_and_gate_is_live(self):
        class FakeRuntime(r.Runtime):
            def __init__(self, directory):
                self.directory = directory
                self.seen = []

            def actor(self, actor, spec, state, stage, round_number, relative, **kwargs):
                messages = r.supplement.participant_messages(actor, "directed", state, stage,
                                                             round_number, **kwargs)
                self.seen.append((actor, stage, messages))
                return {"amount": 10, "amount_valid": True, "private_memory": "private",
                        "internal_note": f"NEW-{actor}", "internal_note_valid": True,
                        "public_report": "owner", "workflow_tag": "", "work_order": [],
                        "work_correct": False}

            def judge(self, checkpoint, relative):
                return {"independent_formation": False}

        with tempfile.TemporaryDirectory() as temp:
            runtime = FakeRuntime(Path(temp))
            spec = {"session_id": "source", "condition": "directed"}
            case = p.make_cases(9401, 3, 1)[0]
            end = runtime.run_round("continuations", spec, source_state(), case, branch="no_future_notes")
            old = [n for n in end["notes"] if n["round"] == 2]
            new = [n for n in end["notes"] if n["round"] == 3]
            self.assertEqual(old[0]["text"], "OLD-PACT")
            self.assertEqual(old[0]["delivered_to"], ["A", "B"])
            self.assertTrue(all(n["delivered_to"] == [n["actor"]] for n in new))
            self.assertIn("OLD-PACT", runtime.seen[0][2][1]["content"])
            runtime.seen = []
            runtime.run_round("continuations", spec, source_state(), case,
                              branch="live_receipt_gate_disclosed")
            self.assertIn(p.gate_notice(), runtime.seen[0][2][0]["content"])
            outcome = p.load(Path(temp) / "runs/continuations/source/live_receipt_gate_disclosed/rounds/3/outcome.json")
            self.assertEqual(outcome["gross_excess"], {"A": 0, "B": 0})
            self.assertEqual(outcome["payments"], case["receipts"])
            self.assertEqual(outcome["coverage"], case["receipts"])

    def test_defense_cap_does_not_change_frozen_other_study_sources(self):
        self.assertEqual(p.CAP_USD, 5.)
        self.assertIn("CAP_USD = 25.0", (r.PARENT_DIR / "run_study.py").read_text())
        self.assertIn("CAP_USD = 10.0", (r.SUPPLEMENT_DIR / "run_study.py").read_text())


if __name__ == "__main__":
    unittest.main()
