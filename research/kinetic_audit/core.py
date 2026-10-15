"""Pure contracts shared by the executable adapter and offline tests.

No simulated welfare improvement is used as experimental evidence here.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from enum import Enum
from hashlib import sha256
import json
import math
from pathlib import Path
from typing import Any

class Feedback(str, Enum):
    ORIGINAL = "original"
    PEER_SNAPSHOT = "peer_snapshot"
    SUPPRESS_SCORE = "suppress_score"

SCORE_KEYS = frozenset({"joint_reward"})

def canonical(obj: Any) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), allow_nan=False,
                      ensure_ascii=False).encode("utf-8")

def strip_score(obj: Any) -> Any:
    """Return a fresh view, removing only the verified privileged score key.

    Does not remove task IDs, legitimate state updates, text, or other inferred
    carriers. This is deliberately NOT a universal disclosure sanitizer.
    """
    if isinstance(obj, dict):
        return {k: strip_score(v) for k, v in obj.items() if k not in SCORE_KEYS}
    if isinstance(obj, list):
        return [strip_score(v) for v in obj]
    return obj

def score_paths(obj: Any, path: str = "$") -> list[str]:
    result: list[str] = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k in SCORE_KEYS:
                result.append(f"{path}.{k}")
            result += score_paths(v, f"{path}.{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            result += score_paths(v, f"{path}[{i}]")
    return result

@dataclass(frozen=True)
class Cell:
    task_seed: int
    objective: str
    revoke: bool
    feedback: str
    controller: str = "fixed"
    split: str = "pilot"

    def __post_init__(self):
        if self.objective not in {"cooperative", "coalition"}:
            raise ValueError("unknown objective")
        Feedback(self.feedback)
        if self.controller not in {"fixed", "history_rule", "memoryless_rule"}:
            raise ValueError("unsupported controller (no LLM controller implemented)")
        if self.split not in {"development", "pilot", "heldout"}:
            raise ValueError("unknown split")
        if not isinstance(self.task_seed, int) or isinstance(self.task_seed, bool):
            raise ValueError("integer seed required")

    @property
    def key(self) -> str:
        return (f"s{self.task_seed}__{self.objective}__revoke{int(self.revoke)}"
                f"__{self.feedback}__{self.controller}__{self.split}")

    def to_dict(self) -> dict:
        return asdict(self)

@dataclass(frozen=True)
class SkillState:
    """Host-constructed minimal state; no objectives, costs, reward or free text.

    It describes operational exposure, NOT malicious intent or downstream harm.
    """
    policy_epoch: int
    private_channel_open: bool
    actor_score_events: int
    peer_score_events: int
    prior_actor_score_events: int
    prior_peer_score_events: int
    task_requires_score: bool
    remaining_switches: int

    def __post_init__(self):
        for key, value in asdict(self).items():
            if not isinstance(value, (int, bool)) or value < 0:
                raise ValueError(f"invalid structured field: {key}")

@dataclass(frozen=True)
class SkillDecision:
    skill: str
    reason_code: str
    state_digest: str


def choose_skill(state: SkillState, *, history: bool = True) -> SkillDecision:
    """Frozen rule baseline for an OrchDebate-inspired structured-state interface.

    This baseline deliberately uses NO LLM, learned selection, or self-evolution.
    A learned selector must beat this on held-out data with matched budgets.
    """
    h = sha256(canonical(asdict(state))).hexdigest()
    actor = state.actor_score_events + (state.prior_actor_score_events if history else 0)
    peer = state.peer_score_events + (state.prior_peer_score_events if history else 0)
    if state.remaining_switches <= 0:
        return SkillDecision("retain", "SWITCH_BUDGET_EXHAUSTED", h)
    if state.task_requires_score:
        return SkillDecision("retain", "REQUIRES_LEGITIMATE_SCORE_FEEDBACK", h)
    if actor:
        return SkillDecision("suppress_score", "ACTOR_NUMERIC_EXPOSURE_OBSERVED", h)
    if peer:
        return SkillDecision("peer_snapshot", "PEER_NUMERIC_EXPOSURE_OBSERVED", h)
    return SkillDecision("retain", "NO_REGISTERED_NUMERIC_EXPOSURE", h)


def parse_skill_proposal(value: dict, state: SkillState) -> SkillDecision:
    """Strict untrusted-proposal seam, NOT a model invocation or approval oracle."""
    if set(value) != {"skill", "state_digest"}:
        raise ValueError("proposal must have only skill and state_digest")
    if value["skill"] not in {"retain", "peer_snapshot", "suppress_score"}:
        raise ValueError("not an approved skill")
    h = sha256(canonical(asdict(state))).hexdigest()
    if value["state_digest"] != h:
        raise ValueError("stale state or forged proposal")
    if value["skill"] != "retain" and (state.task_requires_score or state.remaining_switches <= 0):
        raise ValueError("host contract rejects intervention")
    return SkillDecision(value["skill"], "UNTRUSTED_PROPOSAL_HOST_CHECKED", h)

class Ledger:
    """Immutable serialized local snapshots. NOT external attestation.

    Store outside agent tool roots. A digest only detects mutation relative to an
    independently preserved anchor; a compromised writer can rewrite everything.
    """
    def __init__(self, path: Path | None = None):
        self.path = path
        self.records: list[dict] = []
        self.head = "0" * 64
        if path:
            path.parent.mkdir(parents=True, exist_ok=True)
            if path.exists():
                raise FileExistsError(f"Refusing to append to existing experiment: {path}")
            path.touch(mode=0o600)

    def emit(self, kind: str, data: Any) -> dict:
        payload = json.loads(canonical(data))  # snapshot now, reject NaN/unsupported data
        record = {"seq": len(self.records), "kind": kind, "previous": self.head, "data": payload}
        record["digest"] = sha256(canonical(record)).hexdigest()
        self.head = record["digest"]
        self.records.append(record)
        if self.path:
            with self.path.open("a", encoding="utf-8") as f:
                f.write(canonical(record).decode() + "\n")
        return record

    @staticmethod
    def verify(records: list[dict], expected_head: str) -> bool:
        previous = "0" * 64
        for i, original in enumerate(records):
            r = dict(original)
            digest = r.pop("digest", None)
            if r.get("seq") != i or r.get("previous") != previous:
                return False
            if sha256(canonical(r)).hexdigest() != digest:
                return False
            previous = digest
        return previous == expected_head


def finite_number(x: Any) -> float:
    if isinstance(x, bool):
        raise ValueError("boolean is not a reward")
    v = float(x)
    if not math.isfinite(v):
        raise ValueError("nonfinite reward")
    return v
