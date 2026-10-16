#!/usr/bin/env python3
"""Fresh optional confirmation. Import, prepare, freeze, and tests make no API calls."""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from copy import deepcopy
import importlib.util
import json
import math
from pathlib import Path
import random
import threading

HERE = Path(__file__).resolve().parent
PILOT = HERE.parent / "agreement_pilot_20261015"
SPEC = importlib.util.spec_from_file_location("immutable_agreement_pilot", PILOT / "run_pilot.py")
p = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(p)
BUDGET_USD = 5.0
ASSIGNMENT_SEED = 83008318
DISPATCH_SEED = 83188300
VISIBILITY_LABELS = {"none", "agreement_visible", "agreement_out_of_view", "agreement_strict_covert"}


def session_id(specification):
    return f"{specification['condition']}_{specification['seed']}_slot{specification['slot']}"


def make_plan(model=p.MINI):
    if model not in (p.MINI, p.FULL):
        raise ValueError("Only the two predeclared model profiles are available")
    rng = random.Random(ASSIGNMENT_SEED)
    sessions = []
    assignments = []
    for seed in range(8301, 8313):
        deliveries = ["delivered", "withheld"]
        rng.shuffle(deliveries)
        assignments.append({"seed": seed, "slot0": deliveries[0], "slot1": deliveries[1]})
        for slot, delivery in enumerate(deliveries):
            sessions.append({"seed": seed, "condition": "selfish", "slot": slot,
                             "delivery": delivery, "model": model})
    sessions += [{"seed": seed, "condition": "cooperative", "slot": 0,
                  "delivery": "delivered", "model": model} for seed in range(8313, 8319)]
    dispatch = [session_id(specification) for specification in sessions]
    random.Random(DISPATCH_SEED).shuffle(dispatch)
    return {"study": "fresh reciprocal reimbursement confirmation", "sessions": sessions,
            "cases_per_session": 4, "assignment_seed": ASSIGNMENT_SEED,
            "dispatch_seed": DISPATCH_SEED, "slot_assignments": assignments,
            "dispatch_order": dispatch, "base_logical_calls": 660,
            "metadata_hidden_review_calls": 96, "total_logical_calls": 756,
            "model": model, "temperature": p.TEMPERATURE, "max_tokens": p.MAX_TOKENS,
            "budget_usd": BUDGET_USD, "maximum_concurrent_sessions": 3,
            "transport_attempts_per_call": 1, "pilot_prompt_material_sha256": p.digest(p.prompt_material()),
            "formation_release": "All 30 preparation labels frozen before future cases are generated or called.",
            "analysis": "analyze_confirmation.py; frozen ANALYSIS_PLAN.md"}


def local_source_hashes():
    paths = {name: HERE / name for name in ("run_confirmation.py", "PROTOCOL.md", "test_confirmation.py",
                                          "analyze_confirmation.py", "ANALYSIS_PLAN.md", "test_analysis.py")}
    paths.update({"imported_pilot_runner": PILOT / "run_pilot.py",
                  "imported_pilot_protocol": PILOT / "PROTOCOL.md",
                  "imported_pilot_tests": PILOT / "test_pilot.py",
                  "evidence_standard": PILOT / "EVIDENCE_STANDARD.md",
                  "borrowed_api_client": p.CLIENT_PATH,
                  "pilot_freeze": PILOT / "pilot" / "FREEZE.json"})
    return {key: p.file_hash(path) for key, path in paths.items()}


def prepare(directory, model=p.MINI):
    directory = Path(directory)
    p.save_new(directory / "plan.json", make_plan(model))
    p.save_new(directory / "prompt_material.json", p.prompt_material())
    p.save_new(directory / "finite_certificate.json", p.finite_certificate())
    return {"prepared": True, "network_calls": 0, "model": model,
            "planned_calls": 756, "directory": str(directory)}


def freeze(directory):
    directory = Path(directory)
    plan = p.load(directory / "plan.json")
    if plan != make_plan(plan["model"]):
        raise ValueError("Prepared plan changed")
    if p.load(directory / "prompt_material.json") != json.loads(p.canonical(p.prompt_material())):
        raise ValueError("Prepared imported prompts changed")
    if (directory / "FREEZE.json").exists():
        verify_freeze(directory)
        return p.load(directory / "FREEZE.json")
    return p.save_new(directory / "FREEZE.json", {"frozen_at": p.now(),
        "source_hashes": local_source_hashes(), "prepared_hashes": {name: p.file_hash(directory / name)
            for name in ("plan.json", "prompt_material.json", "finite_certificate.json")},
        "scope": "Fresh worlds; local hash/time freeze before calls, not independent public attestation."})


def verify_freeze(directory):
    directory = Path(directory)
    data = p.load(directory / "FREEZE.json")
    if data["source_hashes"] != local_source_hashes():
        raise ValueError("Frozen implementation, analysis, or imported source changed")
    for name, expected in data["prepared_hashes"].items():
        if p.file_hash(directory / name) != expected:
            raise ValueError("Frozen prepared artifact changed")
    return True


def visible_notes(authored_notes, actor, delivery):
    if delivery not in ("delivered", "withheld"):
        raise ValueError("Unknown delivery condition")
    return deepcopy(authored_notes if delivery == "delivered" else
                    [note for note in authored_notes if note["participant"] == actor])


def make_cases(seed):
    # This constructor is called only after preparation labels are frozen.
    # Both slots in a block use these same four future case objects.
    return [{"case_index": index, "case": p.make_case(seed * 100 + index)} for index in range(1, 5)]


def metadata_hidden_review_prompt(actor, case, claims):
    prompt = p.review_prompt(actor, case, claims)
    content = json.loads(prompt["content"])
    for key in ("workflow_tag", "public_report", "work_order"):
        del content["colleague_claim"][key]
    return {"role": "user", "content": json.dumps(content, ensure_ascii=False)}


class ConfirmationRunner(p.Runner):
    def __init__(self, directory, client=None, budget=BUDGET_USD):
        self.directory = Path(directory)
        self.client = client or p.load_client()
        self.budget = budget
        self.lock = threading.Lock()
        self.stop = threading.Event()
        self.reserved = sum(p.load(path)["reserved_usd"] for path in self.directory.rglob("budget_reservation.json"))
        self.actual_reported = 0.0
        self.logical_calls = 0

    def prep_session(self, specification):
        directory = self.directory / "sessions" / session_id(specification)
        p.save_new(directory / "specification.json", specification)
        contexts = {actor: p.participant_context(actor, specification["condition"]) for actor in ("A", "B")}
        authored = []
        preparation = []
        deliveries = []
        for index, actor in enumerate(p.PREP_ACTORS):
            observed = visible_notes(authored, actor, specification["delivery"])
            user = p.prep_prompt(actor, index, observed)
            messages = contexts[actor] + [user]
            name = f"prep_{index + 1}_{actor}"
            record = self.invoke(messages, specification["model"], directory / "calls" / name)
            action = p.parse_action(record, "preparation", client=self.client)
            p.save_new(directory / "actions" / f"{name}.json", action)
            contexts[actor] = messages + [{"role": "assistant", "content": record.get("raw_content") or "{}"}]
            note = {"participant": actor, "preparation_turn": index + 1,
                    "internal_note": action["internal_note"], "note_valid": action["internal_note_valid"]}
            authored.append(note)
            preparation.append({"participant": actor, "preparation_turn": index + 1, "action": action})
            deliveries.append({"recipient": actor, "before_turn": index + 1, "observed_notes": observed,
                               "request_path": f"calls/{name}/request.json"})
        return p.save_new(directory / "preparation_checkpoint.json", {
            "specification": specification, "authored_notes": authored,
            "delivered_notes": {actor: visible_notes(authored, actor, specification["delivery"]) for actor in ("A", "B")},
            "preparation_actions": preparation, "delivery_log": deliveries,
            "actor_contexts": contexts, "actor_context_sha256": {actor: p.digest(contexts[actor]) for actor in ("A", "B")}})

    def case_session(self, specification, common_cases):
        directory = self.directory / "sessions" / session_id(specification)
        checkpoint_path = directory / "preparation_checkpoint.json"
        checkpoint = p.load(checkpoint_path)
        outputs = []
        for entry in common_cases:
            index, case = entry["case_index"], entry["case"]
            target = directory / "cases" / f"case_{index}"
            p.save_new(target / "case.json", {"case_index": index, "case": case,
                      "preparation_checkpoint_sha256": p.file_hash(checkpoint_path)})
            # Every case branches independently from exactly the same preparation;
            # no previous claim, approval, settlement, or case feedback is carried.
            contexts = deepcopy(checkpoint["actor_contexts"])
            claims = {}
            for actor in ("A", "B"):
                notes = {"role": "user", "content": json.dumps({
                    "complete_preparation_workspace": checkpoint["delivered_notes"][actor]}, ensure_ascii=False)}
                messages = contexts[actor] + [notes, p.claim_prompt(actor, case)]
                record = self.invoke(messages, specification["model"], target / "calls" / f"claim_{actor}")
                claims[actor] = p.parse_action(record, "claim", case["public_tasks"], self.client)
                p.save_new(target / "actions" / f"claim_{actor}.json", claims[actor])
                contexts[actor] = messages + [{"role": "assistant", "content": record.get("raw_content") or "{}"}]
            p.save_new(target / "claims_fixed_before_reviews.json", claims)
            reviews = {}
            for actor in ("A", "B"):
                messages = contexts[actor] + [p.review_prompt(actor, case, claims)]
                record = self.invoke(messages, specification["model"], target / "calls" / f"review_{actor}")
                reviews[actor] = p.parse_action(record, "review", case["public_tasks"], self.client)
                p.save_new(target / "actions" / f"review_{actor}.json", reviews[actor])
            outcome = {"specification": specification, "case_index": index, "case": case,
                       "claims": claims, "reviews": reviews, "outcomes": p.outcomes(case, claims, reviews),
                       "preparation_checkpoint_sha256": p.file_hash(checkpoint_path)}
            p.save_new(target / "outcome.json", outcome)
            if specification["condition"] == "selfish" and specification["delivery"] == "delivered":
                hidden_reviews = {}
                for actor in ("A", "B"):
                    # Full preparation and the actor's own fixed claim remain.
                    # Only three optional fields of the peer's claim are removed.
                    messages = contexts[actor] + [metadata_hidden_review_prompt(actor, case, claims)]
                    record = self.invoke(messages, specification["model"],
                                         target / "calls" / f"metadata_hidden_review_{actor}")
                    hidden_reviews[actor] = p.parse_action(record, "review", case["public_tasks"], self.client)
                    p.save_new(target / "actions" / f"metadata_hidden_review_{actor}.json", hidden_reviews[actor])
                hidden = {"specification": specification, "case_index": index, "case": case,
                          "claims": claims, "reviews": hidden_reviews,
                          "outcomes": p.outcomes(case, claims, hidden_reviews),
                          "preparation_checkpoint_sha256": p.file_hash(checkpoint_path),
                          "branch": "optional_peer_claim_metadata_hidden"}
                p.save_new(target / "metadata_hidden_outcome.json", hidden)
            outputs.append(outcome)
        return outputs


def dispatch(runner, specifications, worker, *, probe_first):
    failures = []
    if probe_first and specifications:
        try:
            worker(specifications[0])
        except Exception as exc:
            runner.stop.set()
            failures.append({"session": session_id(specifications[0]), "error_type": type(exc).__name__})
        remaining = specifications[1:]
    else:
        remaining = specifications
    if not failures:
        with ThreadPoolExecutor(max_workers=3) as pool:
            futures = {pool.submit(worker, spec): spec for spec in remaining}
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as exc:
                    runner.stop.set()
                    failures.append({"session": session_id(futures[future]), "error_type": type(exc).__name__})
    return failures


def ordered_specs(plan):
    lookup = {session_id(spec): spec for spec in plan["sessions"]}
    return [lookup[key] for key in plan["dispatch_order"]]


def prep(directory):
    directory = Path(directory)
    verify_freeze(directory)
    plan = p.load(directory / "plan.json")
    runner = ConfirmationRunner(directory)
    failures = dispatch(runner, ordered_specs(plan), runner.prep_session, probe_first=True)
    status = {"stage": "preparation", "complete_checkpoints": len(list(directory.glob("sessions/*/preparation_checkpoint.json"))),
              "planned_checkpoints": 30, "failures": failures, "blind_next_step": "Freeze transcript-only formation labels before --cases."}
    p.save_new(directory / "PREPARATION_STATUS.json", status)
    return status


def release_cases(directory, labels_path):
    directory = Path(directory)
    verify_freeze(directory)
    plan = p.load(directory / "plan.json")
    labels = p.load(labels_path)
    if not isinstance(labels.get("labels_frozen_at"), str) or not isinstance(labels.get("labels"), list):
        raise ValueError("Labels require labels_frozen_at and a labels list")
    expected = {(s["seed"], s["condition"], s["slot"], s["delivery"]) for s in plan["sessions"]}
    actual = []
    for label in labels["labels"]:
        key = (label.get("seed"), label.get("condition"), label.get("slot"), label.get("delivery"))
        if not isinstance(label.get("formation_qualified"), bool) or label.get("visibility_label") not in VISIBILITY_LABELS:
            raise ValueError("Every label must contain a Boolean formation decision and known visibility label")
        if (not label["formation_qualified"]) != (label["visibility_label"] == "none"):
            raise ValueError("Formation and visibility label are inconsistent")
        actual.append(key)
    if len(actual) != 30 or len(set(actual)) != 30 or set(actual) != expected:
        raise ValueError("Exactly one formation label is required for each planned session")
    checkpoints = {}
    for spec in plan["sessions"]:
        key = session_id(spec)
        path = directory / "sessions" / key / "preparation_checkpoint.json"
        value = p.load(path)
        if value["specification"] != spec:
            raise ValueError("Preparation checkpoint belongs to another specification")
        checkpoints[key] = p.file_hash(path)
    p.save_new(directory / "formation_labels.json", labels)
    release = {"formation_labels_sha256": p.file_hash(directory / "formation_labels.json"),
               "preparation_checkpoints": checkpoints,
               "scope": "Labels frozen before first case generation; root is responsible for transcript-only review."}
    p.save_new(directory / "CASES_RELEASE.json", release)
    # Only now are future case data generated and recorded.
    common = {}
    for seed in sorted({spec["seed"] for spec in plan["sessions"]}):
        common[seed] = make_cases(seed)
        p.save_new(directory / "common_cases" / f"{seed}.json", common[seed])
    return plan, common


def cases(directory, labels_path):
    directory = Path(directory)
    plan, common = release_cases(directory, labels_path)
    runner = ConfirmationRunner(directory)
    failures = dispatch(runner, ordered_specs(plan),
                        lambda spec: runner.case_session(spec, common[spec["seed"]]), probe_first=False)
    status = {"stage": "cases", "complete_base_case_outcomes": len(list(directory.glob("sessions/*/cases/*/outcome.json"))),
              "complete_metadata_hidden_case_outcomes": len(list(directory.glob("sessions/*/cases/*/metadata_hidden_outcome.json"))),
              "planned_base_case_outcomes": 120, "planned_metadata_hidden_case_outcomes": 48,
              "failures": failures, "next_step": "Run separately frozen analysis; no results inferred here."}
    p.save_new(directory / "CASE_STATUS.json", status)
    return status


def analyze(directory):
    directory = Path(directory)
    verify_freeze(directory)
    script = HERE / "analyze_confirmation.py"
    spec = importlib.util.spec_from_file_location("frozen_confirmation_analysis", script)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if not hasattr(module, "analyze"):
        raise RuntimeError("Frozen analysis must expose analyze(directory)")
    return module.analyze(directory)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    stages = parser.add_mutually_exclusive_group(required=True)
    for name in ("prepare", "freeze", "prep", "cases", "analyze"):
        stages.add_argument("--" + name, action="store_true")
    parser.add_argument("--directory", type=Path, default=HERE / "confirmation")
    parser.add_argument("--model", choices=(p.MINI, p.FULL), default=p.MINI)
    parser.add_argument("--labels", type=Path)
    args = parser.parse_args(argv)
    if args.prepare:
        value = prepare(args.directory, args.model)
    elif args.freeze:
        value = freeze(args.directory)
    elif args.prep:
        value = prep(args.directory)
    elif args.cases:
        if not args.labels:
            parser.error("--cases requires --labels containing frozen preparation-only judgments")
        value = cases(args.directory, args.labels)
    else:
        value = analyze(args.directory)
    print(json.dumps(value, indent=2))


if __name__ == "__main__":
    main()
