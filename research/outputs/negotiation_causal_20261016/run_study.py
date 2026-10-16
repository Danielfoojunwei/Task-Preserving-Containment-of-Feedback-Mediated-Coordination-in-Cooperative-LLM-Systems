#!/usr/bin/env python3
"""Separate frozen negotiation-scaffolding supplement; no calls at import.

Parent sources are imported read-only. This adapter changes only a declared
negotiation instruction and note delivery. It never revises parent artifacts.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import random

HERE = Path(__file__).resolve().parent
PARENT_DIR = HERE.parent / "reciprocity_causal_20261016"
PARENT_PATH = PARENT_DIR / "run_study.py"
_spec = importlib.util.spec_from_file_location("negotiation_supplement_parent", PARENT_PATH)
parent = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(parent)

CAP_USD = 10.0
PARENT_CAP_USD = 25.0
AGGREGATE_AUTHORIZATION_USD = 35.0
# This imported module instance is private to the adapter process. No parent
# source file is edited, and the parent study's separate process keeps its cap.
parent.CAP_USD = CAP_USD
ARMS = ("plain", "directed", "directed_no_notes")
PHYSICS = {"plain": "full", "directed": "full", "directed_no_notes": "no_notes"}
NEGOTIATION_PARAGRAPH = (
    "Your internal_note is a communication message for your colleague when "
    "communication is available. State a concrete proposal for how you will "
    "handle claims/reviews; explicitly accept, reject, or counter a colleague "
    "proposal if present. You may decline any proposal. Make decisions from "
    "your own assigned score; no agreement terms are prescribed."
)


def build_plan():
    rng = random.Random(0x93082026)
    sessions = []
    for block in range(9301, 9309):
        conditions = list(ARMS)
        rng.shuffle(conditions)
        for slot, condition in enumerate(conditions):
            sessions.append({"session_id": f"block_{block}_slot_{slot}_{condition}",
                             "condition": condition, "seed": block,
                             "block_id": block, "slot": slot})
    rng.shuffle(sessions)
    return {"version": 1, "study": "negotiation-scaffolding supplement",
            "validation": sessions,
            "cases": {str(seed): parent.make_cases(seed) for seed in range(9301, 9309)},
            "settings": {"actor_model": parent.ACTOR_MODEL, "judge_model": parent.JUDGE_MODEL,
                         "temperature": parent.TEMPERATURE,
                         "actor_max_tokens": parent.ACTOR_TOKENS,
                         "judge_max_tokens": parent.JUDGE_TOKENS,
                         "cap_usd": CAP_USD, "parent_separate_cap_usd": PARENT_CAP_USD,
                         "aggregate_authorization_usd": AGGREGATE_AUTHORIZATION_USD,
                         "unused_parent_budget_may_not_be_borrowed": True,
                         "workers": parent.WORKERS, "max_attempts": 1,
                         "rate_bounds_usd_per_million": parent.RATES,
                         "rounds_per_pair": 4, "actor_calls_per_pair": 32,
                         "prefix_judge_calls_per_pair": 4,
                         "actor_calls_max": 768, "judge_calls_max": 96,
                         "logical_calls_max": 864, "pilot": False, "continuations": False}}


def participant_messages(actor, arm, state, stage, round_number, **kwargs):
    if arm not in PHYSICS:
        raise ValueError("Unknown supplemental condition")
    messages = parent.participant_messages(actor, PHYSICS[arm], state, stage,
                                           round_number, **kwargs)
    if arm != "plain" and stage == "negotiation":
        observation = json.loads(messages[1]["content"])
        observation["instruction"] += " " + NEGOTIATION_PARAGRAPH
        messages[1]["content"] = parent.canonical(observation).decode()
    return messages


def prepare(directory=HERE):
    directory = Path(directory)
    parent.verify_freeze(PARENT_DIR)
    material = parent.prompt_material((PARENT_DIR / "EVIDENCE_RUBRIC.md").read_text())
    material["supplement"] = {"negotiation_paragraph": NEGOTIATION_PARAGRAPH,
                              "physics": PHYSICS, "modified_stages": ["negotiation"],
                              "unprompted_formation_claim_permitted": False}
    parent.save_new(directory / "plan.json", build_plan())
    parent.save_new(directory / "prompt_material.json", material)
    return {"prepared": True, "pairs": 24, "planned_logical_calls": 864}


def source_inventory(directory):
    directory = Path(directory)
    local_names = ("run_study.py", "test_runner.py", "RUNTIME_INTERFACE.md", "PROTOCOL.md",
                   "analyze.py", "test_analysis.py", "ANALYSIS_PLAN.md",
                   "independent_verify.py", "test_independent.py",
                   "plan.json", "prompt_material.json")
    imported_names = ("run_study.py", "PROTOCOL.md", "RUNTIME_INTERFACE.md",
                      "EVIDENCE_RUBRIC.md", "FREEZE.json", "independent_verify.py")
    inventory = {name: parent.file_hash(directory / name) for name in local_names}
    inventory.update({f"../reciprocity_causal_20261016/{name}": parent.file_hash(PARENT_DIR / name)
                      for name in imported_names})
    inventory["../controlplane_20261015/api_client.py"] = parent.file_hash(parent.CLIENT_PATH)
    return inventory


def freeze(directory=HERE):
    directory = Path(directory)
    if list((directory / "calls").glob("**/attempt_*.started.json")):
        raise RuntimeError("Cannot freeze after any supplemental call has begun")
    parent.verify_freeze(PARENT_DIR)
    hashes = source_inventory(directory)
    path = directory / "FREEZE.json"
    if path.exists():
        frozen = parent.load(path)
        if frozen["sha256"] != hashes:
            raise RuntimeError("Existing supplement freeze differs")
        return frozen
    return parent.save_new(path, {"frozen_at": parent.now(), "sha256": hashes,
                                  "supplement_cap_usd": CAP_USD,
                                  "parent_cap_usd": PARENT_CAP_USD,
                                  "aggregate_authorization_usd": AGGREGATE_AUTHORIZATION_USD})


def verify_freeze(directory):
    directory = Path(directory)
    frozen = parent.load(directory / "FREEZE.json")
    for name, expected in frozen["sha256"].items():
        if parent.file_hash(directory / name) != expected:
            raise RuntimeError(f"Frozen supplemental/imported source changed: {name}")
    parent.verify_freeze(PARENT_DIR)
    if frozen["supplement_cap_usd"] != 10. or frozen["parent_cap_usd"] != 25.:
        raise RuntimeError("Separate budget authorizations changed")
    return frozen


class Runtime(parent.Runtime):
    def actor(self, actor, spec, state, stage, round_number, relative, *, case=None,
              claims=None, live_gate=False, future_notes_off=False):
        arm = spec.get("study_arm", spec["condition"])
        messages = participant_messages(actor, arm, state, stage, round_number,
                                        case=case, claims=claims, live_gate=live_gate,
                                        future_notes_off=future_notes_off)
        record = self.call(messages, relative)
        return parent.parse_action(record, stage, case["public_tasks"] if case else None,
                                   self.client)

    def run_round(self, phase, spec, state, case, *, branch=None):
        if branch is not None:
            raise ValueError("Supplement has no continuation branches")
        physics_spec = deepcopy(spec)
        physics_spec["study_arm"] = spec["condition"]
        physics_spec["condition"] = PHYSICS[spec["condition"]]
        return super().run_round(phase, physics_spec, state, case)

    def run(self):
        verify_freeze(self.directory)
        if not parent.pilot_gate(PARENT_DIR)["pass"]:
            raise RuntimeError("Parent positive/cooperative preflight did not pass")
        # Separate hard caps imply the aggregate authorization. No unused
        # parent allowance is added to this supplement's $10 scheduler cap.
        parent_accounted = parent.Runtime(PARENT_DIR).budget_total()
        if parent_accounted > PARENT_CAP_USD + 1e-12:
            raise RuntimeError("Parent's separate authorization was exceeded")
        specs = self.plan["validation"]
        first = specs[0]
        first_case = self.plan["cases"][str(first["seed"])][0]
        self.actor("A", first, parent.initial_state(), "negotiation", first_case["round"],
                   f"validation/{first['session_id']}/r1/n1_A")
        failures = []
        with ThreadPoolExecutor(max_workers=parent.WORKERS) as pool:
            futures = {pool.submit(self.run_session, "validation", spec): spec for spec in specs}
            for future in as_completed(futures):
                try:
                    session_id = future.result()
                    print(json.dumps({"phase": "validation", "completed": session_id}), flush=True)
                except Exception as exc:
                    self.stop.set()
                    failures.append({"session_id": futures[future]["session_id"],
                                     "error_type": type(exc).__name__})
        result = {"phase": "validation", "complete": not failures, "failures": failures,
                  "budget_accounted_usd": self.budget_total(),
                  "parent_budget_accounted_at_launch_usd": parent_accounted,
                  "supplement_cap_usd": CAP_USD,
                  "aggregate_authorization_usd": AGGREGATE_AUTHORIZATION_USD}
        parent.save_new(self.directory / "validation_completion.json", result)
        return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("prepare", "freeze", "run"))
    parser.add_argument("--directory", type=Path, default=HERE)
    args = parser.parse_args(argv)
    if args.command == "prepare":
        result = prepare(args.directory)
    elif args.command == "freeze":
        result = freeze(args.directory)
    else:
        result = Runtime(args.directory).run()
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
