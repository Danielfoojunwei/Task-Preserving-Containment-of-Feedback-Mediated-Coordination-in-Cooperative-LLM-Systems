#!/usr/bin/env python3
"""Separate bounded defense continuation study; no network at import.

All eight directed supplement worlds branch from their exact round-2 end state.
This is a new frozen study; earlier studies' no-continuation plans stay intact.
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
SUPPLEMENT_DIR = HERE.parent / "negotiation_causal_20261016"
PARENT_DIR = HERE.parent / "reciprocity_causal_20261016"
_spec = importlib.util.spec_from_file_location("bounded_defense_supplement", SUPPLEMENT_DIR / "run_study.py")
supplement = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(supplement)
parent = supplement.parent
CAP_USD = 5.0
PARENT_CAP_USD = 25.0
SUPPLEMENT_CAP_USD = 10.0
AGGREGATE_AUTHORIZATION_USD = 40.0
parent.CAP_USD = CAP_USD
BRANCHES = ("unchanged", "no_future_notes", "live_receipt_gate_disclosed")


def build_plan(source_plan=None, state_hash_fn=None):
    source_plan = source_plan if source_plan is not None else parent.load(SUPPLEMENT_DIR / "plan.json")
    state_hash_fn = state_hash_fn or parent.file_hash
    sources = []
    for spec in source_plan["validation"]:
        if spec["condition"] != "directed":
            continue
        source = deepcopy(spec)
        source["source_state_path"] = (
            f"../negotiation_causal_20261016/runs/validation/{spec['session_id']}/rounds/2/end_state.json")
        source["source_state_sha256"] = state_hash_fn(HERE / source["source_state_path"])
        source["snapshot_path"] = f"sources/{spec['session_id']}/round2_end_state.json"
        sources.append(source)
    sources.sort(key=lambda item: item["block_id"])
    if len(sources) != 8 or {s["seed"] for s in sources} != set(range(9301, 9309)):
        raise RuntimeError("Exactly all eight directed supplemental worlds are required")
    jobs = [{"session_id": source["session_id"], "branch": branch}
            for source in sources for branch in BRANCHES]
    random.Random(0xDEF8432).shuffle(jobs)
    return {"version": 1, "study": "separate all-directed-world adaptive defense continuations",
            "sources": sources, "jobs": jobs,
            "source_selection": "All eight directed supplemental worlds, without judge or payoff selection",
            "continuation_cases": {str(source["seed"]): parent.make_cases(
                source["seed"] + 100, start_round=3, count=2) for source in sources},
            "settings": {"actor_model": parent.ACTOR_MODEL, "judge_model": parent.JUDGE_MODEL,
                         "temperature": parent.TEMPERATURE,
                         "actor_max_tokens": parent.ACTOR_TOKENS,
                         "judge_max_tokens": parent.JUDGE_TOKENS,
                         "cap_usd": CAP_USD, "parent_separate_cap_usd": PARENT_CAP_USD,
                         "supplement_separate_cap_usd": SUPPLEMENT_CAP_USD,
                         "aggregate_authorization_usd": AGGREGATE_AUTHORIZATION_USD,
                         "unused_other_study_budget_may_not_be_borrowed": True,
                         "workers": parent.WORKERS, "max_attempts": 1,
                         "rate_bounds_usd_per_million": parent.RATES,
                         "branches": list(BRANCHES), "rounds_per_branch": 2,
                         "actor_calls_max": 384, "judge_calls_max": 48,
                         "logical_calls_max": 432, "new_pilot": False,
                         "inference": "descriptive conditional branch comparisons; no new p-values"}}


def validate_source_state(state):
    for note in state["notes"]:
        if note["round"] not in (1, 2):
            raise ValueError("Source contains future negotiation history")
    for actor in ("A", "B"):
        for key in ("own_action_outputs", "own_observed_cases"):
            if any(item["round"] not in (1, 2) for item in state[key][actor]):
                raise ValueError("Source contains future action/case history")
    if [ledger["round"] for ledger in state["round_ledgers"]] != [1, 2]:
        raise ValueError("Source must contain exactly round-1/2 trusted feedback")
    return state


def copy_snapshot(source, target, expected_hash):
    source, target = Path(source), Path(target)
    if parent.file_hash(source) != expected_hash:
        raise RuntimeError("Original round-2 state changed")
    data = source.read_bytes()
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        if target.read_bytes() != data:
            raise RuntimeError("Immutable source snapshot differs")
    else:
        with target.open("xb") as handle:
            handle.write(data)
    return parent.file_hash(target)


def prepare(directory=HERE):
    directory = Path(directory)
    supplement.verify_freeze(SUPPLEMENT_DIR)
    completion = parent.load(SUPPLEMENT_DIR / "validation_completion.json")
    if completion.get("complete") is not True:
        raise RuntimeError("Supplemental validation must complete first")
    plan = build_plan()
    parent.save_new(directory / "plan.json", plan)
    material = parent.load(SUPPLEMENT_DIR / "prompt_material.json")
    material["defense"] = {"branches": list(BRANCHES), "gate_notice": parent.gate_notice(),
                           "source_round": 2, "new_rounds": [3, 4],
                           "future_note_cut_retains_past_delivered_notes": True,
                           "directed_scaffolding_retained": True}
    parent.save_new(directory / "prompt_material.json", material)
    for source in plan["sources"]:
        copy_snapshot(HERE / source["source_state_path"], directory / source["snapshot_path"],
                      source["source_state_sha256"])
    return {"prepared": True, "source_worlds": 8, "branches": 24, "planned_calls": 432}


def source_inventory(directory):
    directory = Path(directory)
    local = ("run_study.py", "test_runner.py", "RUNTIME_INTERFACE.md", "PROTOCOL.md",
             "independent_verify.py", "test_independent.py", "analyze.py",
             "plan.json", "prompt_material.json")
    inventory = {name: parent.file_hash(directory / name) for name in local}
    imported = {
        "reciprocity_causal_20261016": ("run_study.py", "PROTOCOL.md", "RUNTIME_INTERFACE.md",
                                         "EVIDENCE_RUBRIC.md", "FREEZE.json", "independent_verify.py"),
        "negotiation_causal_20261016": ("run_study.py", "PROTOCOL.md", "RUNTIME_INTERFACE.md",
                                        "FREEZE.json", "plan.json", "prompt_material.json",
                                        "independent_verify.py"),
        "controlplane_20261015": ("api_client.py",),
    }
    for folder, names in imported.items():
        for name in names:
            relative = f"../{folder}/{name}"
            inventory[relative] = parent.file_hash(HERE / relative)
    for source in parent.load(directory / "plan.json")["sources"]:
        inventory[source["source_state_path"]] = parent.file_hash(HERE / source["source_state_path"])
        inventory[source["snapshot_path"]] = parent.file_hash(directory / source["snapshot_path"])
    return inventory


def freeze(directory=HERE):
    directory = Path(directory)
    if list((directory / "calls").glob("**/attempt_*.started.json")):
        raise RuntimeError("Cannot freeze after a defense call has begun")
    supplement.verify_freeze(SUPPLEMENT_DIR)
    hashes = source_inventory(directory)
    path = directory / "FREEZE.json"
    if path.exists():
        old = parent.load(path)
        if old["sha256"] != hashes:
            raise RuntimeError("Existing defense freeze differs")
        return old
    return parent.save_new(path, {"frozen_at": parent.now(), "sha256": hashes,
                                  "defense_cap_usd": CAP_USD,
                                  "aggregate_authorization_usd": AGGREGATE_AUTHORIZATION_USD})


def verify_freeze(directory):
    directory = Path(directory)
    frozen = parent.load(directory / "FREEZE.json")
    for name, expected in frozen["sha256"].items():
        if parent.file_hash(directory / name) != expected:
            raise RuntimeError(f"Frozen defense/imported source changed: {name}")
    supplement.verify_freeze(SUPPLEMENT_DIR)
    if frozen["defense_cap_usd"] != 5. or frozen["aggregate_authorization_usd"] != 40.:
        raise RuntimeError("Defense budget authorization changed")
    return frozen


class Runtime(supplement.Runtime):
    def run_round(self, phase, spec, state, case, *, branch=None):
        if branch not in BRANCHES or spec["condition"] != "directed":
            raise ValueError("Only declared directed-source branches are permitted")
        physics_spec = deepcopy(spec)
        physics_spec["study_arm"] = "directed"
        physics_spec["condition"] = "full"
        # Bypass the supplement's no-continuation guard, using the independently
        # frozen parent branch engine in this newly declared separate study.
        return parent.Runtime.run_round(self, phase, physics_spec, state, case, branch=branch)

    def run(self):
        verify_freeze(self.directory)
        if not parent.pilot_gate(PARENT_DIR)["pass"]:
            raise RuntimeError("Parent preflight failed")
        parent_cost = parent.Runtime(PARENT_DIR).budget_total()
        supplement_cost = parent.Runtime(SUPPLEMENT_DIR).budget_total()
        if parent_cost > 25. + 1e-12 or supplement_cost > 10. + 1e-12:
            raise RuntimeError("An earlier study's separate authorization was exceeded")
        sources = {source["session_id"]: source for source in self.plan["sources"]}
        states = {name: validate_source_state(parent.load(self.directory / source["snapshot_path"]))
                  for name, source in sources.items()}
        first = self.plan["jobs"][0]
        first_spec = sources[first["session_id"]]
        first_case = self.plan["continuation_cases"][str(first_spec["seed"])][0]
        branch = first["branch"]
        self.actor("A", first_spec, states[first["session_id"]], "negotiation", 3,
                   f"continuations/{first_spec['session_id']}/{branch}/r3/n1_A",
                   live_gate=branch == "live_receipt_gate_disclosed",
                   future_notes_off=branch == "no_future_notes")
        failures = []
        with ThreadPoolExecutor(max_workers=parent.WORKERS) as pool:
            futures = {}
            for job in self.plan["jobs"]:
                spec = sources[job["session_id"]]
                future = pool.submit(self.run_session, "continuations", spec,
                                     state=states[job["session_id"]],
                                     cases=self.plan["continuation_cases"][str(spec["seed"])],
                                     branch=job["branch"])
                futures[future] = job
            for future in as_completed(futures):
                job = futures[future]
                try:
                    future.result()
                    print(json.dumps({"completed": job["session_id"], "branch": job["branch"]}), flush=True)
                except Exception as exc:
                    self.stop.set()
                    failures.append({**job, "error_type": type(exc).__name__})
        result = {"complete": not failures, "failures": failures,
                  "budget_accounted_usd": self.budget_total(), "defense_cap_usd": CAP_USD,
                  "parent_accounted_at_launch_usd": parent_cost,
                  "supplement_accounted_at_launch_usd": supplement_cost,
                  "aggregate_authorization_usd": AGGREGATE_AUTHORIZATION_USD}
        parent.save_new(self.directory / "continuation_completion.json", result)
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
