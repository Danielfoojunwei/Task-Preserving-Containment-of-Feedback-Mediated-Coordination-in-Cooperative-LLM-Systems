"""Small host-enforced components inspired by FLOWSEAL and OCELOT.

This is not either paper's full algorithm. Costs are registered-event units,
NOT calibrated privacy bits. No trained defender, semantic checker, signed
rubrics, credal audit, or channel-global guarantee is implemented. Callers must
register boundaries, provenance, destinations and costs in trusted host code;
actor assertions do not establish provenance or authorization.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from decimal import Decimal
from enum import IntEnum
import hashlib
import json
import math
import threading
from types import MappingProxyType


class Label(IntEnum):
    PUBLIC = 0
    AGENT = 1
    PROTECTED = 2


def _name(value):
    if type(value) is not str or not value or len(value) > 256:
        raise ValueError('Expected a nonempty registered identifier')
    return value


def _units(value):
    if type(value) not in (int, float) or not math.isfinite(value) or value < 0:
        raise ValueError('Expected finite nonnegative registered-event units')
    return Decimal(str(value))


def _json_value(value):
    # Strict JSON avoids implicit stringification of keys, NaN and custom
    # encoders. It also prevents arbitrary object methods from supplying truth.
    if value is None or type(value) in (str, bool, int):
        return
    if type(value) is float and math.isfinite(value):
        return
    if type(value) is list:
        for item in value:
            _json_value(item)
        return
    if type(value) is dict and all(type(key) is str for key in value):
        for item in value.values():
            _json_value(item)
        return
    raise ValueError('Payload must be finite plain JSON')


def _canonical(value):
    _json_value(value)
    return json.dumps(value, sort_keys=True, separators=(',', ':'),
                      ensure_ascii=False, allow_nan=False).encode('utf-8')


def _digest(value):
    return hashlib.sha256(_canonical(value)).hexdigest()


@dataclass(frozen=True)
class Provenance:
    label: Label
    records: frozenset[str] = frozenset()

    def __post_init__(self):
        if type(self.label) is not Label:
            raise ValueError('A registered lattice label is required')
        if type(self.records) is not frozenset:
            raise ValueError('Protected record identifiers must be immutable')
        for record in self.records:
            _name(record)
        if self.records and self.label == Label.PUBLIC:
            raise ValueError('Protected provenance cannot have a public label')


def join_provenance(*sources):
    """Preserve the highest source label and every protected record ID."""
    if not sources or any(type(item) is not Provenance for item in sources):
        raise ValueError('At least one registered provenance value is required')
    return Provenance(max(item.label for item in sources),
                      frozenset().union(*(item.records for item in sources)))


@dataclass(frozen=True)
class TypedWitness:
    """A typed host binding, not a cryptographic attestation or LLM verdict."""
    event_id: str
    source: str
    sink: str
    payload_sha256: str
    cost_units: str
    binding_sha256: str

    @classmethod
    def bind(cls, event_id, source, sink, payload, cost):
        event_id, source, sink = map(_name, (event_id, source, sink))
        units = str(_units(cost).normalize())
        payload_hash = _digest(payload)
        binding = _digest([event_id, source, sink, payload_hash, units])
        return cls(event_id, source, sink, payload_hash, units, binding)


class BudgetLedger:
    """One pooled budget across all sources/sinks on this ledger instance.

    `consider` calls `commit_fn(authorized_payload_copy)` at most once per
    (event_id, source, sink). Authorization, reservation and dispatch occur
    under one lock. Distinct sinks charge separately against the shared budget.
    Replays are refused. A callback exception retains the reservation because
    the host cannot prove that no side effect occurred; it is explicitly logged.
    The caller owns callback atomicity and must inspect `committed` as well as
    `allowed`. Hashes bind data and audit order; they do not authenticate the host.
    """

    def __init__(self, budget):
        self._budget = _units(budget)
        self._spent = Decimal(0)
        self._seen = set()
        self._records = []
        self._head = '0' * 64
        self._lock = threading.RLock()
        self._dispatching = False

    @property
    def spent(self):
        with self._lock:
            return float(self._spent)

    @property
    def budget(self):
        return float(self._budget)

    @property
    def records(self):
        with self._lock:
            return deepcopy(self._records)

    @property
    def head_hash(self):
        with self._lock:
            return self._head

    def _refuse(self, phase, reason):
        return {'allowed': False, 'committed': False, 'dispatched': False,
                'phase': phase, 'reason': reason, 'charged_units': 0.0,
                'spent_units': float(self._spent),
                'budget_units': float(self._budget)}

    def consider(self, event_id, source, sink, payload, cost, commit_fn, *,
                 witness=None):
        # Bind and Validate use only explicit event metadata. No world state,
        # evaluator labels, private-cost oracle, or arbitrary **kwargs exist.
        try:
            _canonical(payload)
            snapshot = deepcopy(payload)
            expected = TypedWitness.bind(event_id, source, sink, snapshot, cost)
        except (ValueError, TypeError, OverflowError, RecursionError):
            with self._lock:
                return self._refuse('bind', 'malformed_registered_event')
        with self._lock:
            if witness is not None and type(witness) is not TypedWitness:
                return self._refuse('validate', 'malformed_witness')
            if witness is not None and witness != expected:
                return self._refuse('bind', 'witness_binding_mismatch')
            if not callable(commit_fn):
                return self._refuse('validate', 'missing_commit_function')
            if self._dispatching:
                return self._refuse('commit', 'reentrant_dispatch_refused')
            key = (event_id, source, sink)
            if key in self._seen:
                return self._refuse('commit', 'duplicate_event_destination')
            units = _units(cost)
            if self._spent + units > self._budget:
                return self._refuse('cost', 'registered_budget_exceeded')

            # Reserve before invoking an irreversible callback. An error cannot
            # free capacity that may already have produced a delivery.
            self._spent += units
            self._seen.add(key)
            entry = {'event_id': event_id, 'source': source, 'sink': sink,
                     'payload_sha256': expected.payload_sha256,
                     'binding_sha256': expected.binding_sha256,
                     'cost_units': float(units),
                     'spent_units': float(self._spent),
                     'previous_hash': self._head}
            self._dispatching = True
            try:
                result = commit_fn(deepcopy(snapshot))
                entry['status'] = 'committed'
                response = {'allowed': True, 'committed': True,
                            'dispatched': True, 'phase': 'commit',
                            'reason': 'authorized', 'result': result}
            except Exception as exc:
                entry['status'] = 'commit_error'
                entry['error_type'] = type(exc).__name__
                response = {'allowed': True, 'committed': False,
                            'dispatched': True, 'phase': 'commit',
                            'reason': 'commit_error',
                            'error_type': type(exc).__name__}
            finally:
                self._dispatching = False
            self._head = _digest(entry)
            entry['entry_hash'] = self._head
            self._records.append(entry)
            response.update(charged_units=float(units),
                            spent_units=float(self._spent),
                            budget_units=float(self._budget),
                            payload_sha256=expected.payload_sha256,
                            binding_sha256=expected.binding_sha256,
                            entry_hash=self._head)
            return response


class PolicyGate:
    """Registered write-boundary and scoped provenance authorization only.

    `grants` maps sink IDs to the protected record IDs authorized for that sink.
    Empty/unknown boundaries fail closed. Explicitly untrusted sinks always
    fail. Unknown sinks may receive public data. Tainted data requires every
    source record's grant; unknown/unnamed taint cannot be declassified here.
    No actor-controlled `SAFE` override or semantic inference is implemented.
    """

    def __init__(self, registered_boundaries=(), grants=None, untrusted_sinks=()):
        self._boundaries = frozenset(_name(x) for x in registered_boundaries)
        grants = {} if grants is None else grants
        self._grants = MappingProxyType({
            _name(sink): frozenset(_name(record) for record in records)
            for sink, records in grants.items()})
        self._untrusted = frozenset(_name(x) for x in untrusted_sinks)

    def authorize_write(self, boundary, source, sink, payload, provenance):
        try:
            for identifier in (boundary, source, sink):
                _name(identifier)
            _canonical(payload)
        except (ValueError, TypeError, OverflowError, RecursionError):
            return {'allowed': False, 'reason': 'malformed_registered_write'}
        if boundary not in self._boundaries:
            return {'allowed': False, 'reason': 'unregistered_write_boundary'}
        if type(provenance) is not Provenance:
            return {'allowed': False, 'reason': 'missing_registered_provenance'}
        if sink in self._untrusted:
            return {'allowed': False, 'reason': 'explicitly_untrusted_sink'}
        if provenance.label != Label.PUBLIC:
            if not provenance.records:
                return {'allowed': False, 'reason': 'unscoped_taint'}
            if not provenance.records <= self._grants.get(sink, frozenset()):
                return {'allowed': False, 'reason': 'unauthorized_provenance'}
        return {'allowed': True, 'reason': 'registered_write_authorized',
                'payload_sha256': _digest(payload)}

    def mediate(self, boundary, source, sink, payload, provenance, commit_fn):
        verdict = self.authorize_write(boundary, source, sink, payload,
                                       provenance)
        if not verdict['allowed']:
            return dict(verdict, committed=False, dispatched=False)
        # The trusted dispatcher must actually route every registered write
        # through this gate. This helper cannot intercept an omitted channel.
        snapshot = deepcopy(payload)
        if _digest(snapshot) != verdict['payload_sha256']:
            return {'allowed': False, 'committed': False, 'dispatched': False,
                    'reason': 'payload_changed_after_authorization'}
        result = commit_fn(deepcopy(snapshot))
        return dict(verdict, committed=True, dispatched=True, result=result)
