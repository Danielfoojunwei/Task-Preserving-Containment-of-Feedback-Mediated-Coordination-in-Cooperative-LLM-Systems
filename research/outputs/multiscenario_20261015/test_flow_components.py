"""No-API adversarial checks for the small registered-boundary components."""
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
import inspect

import pytest

from flow_components import (BudgetLedger, Label, PolicyGate, Provenance,
                             TypedWitness, join_provenance)


def test_derived_provenance_requires_every_source_authorization():
    alice = Provenance(Label.PROTECTED, frozenset({'alice/need'}))
    bob = Provenance(Label.PROTECTED, frozenset({'bob/need'}))
    public = Provenance(Label.PUBLIC)
    derived = join_provenance(public, alice, bob)
    assert derived.label == Label.PROTECTED
    assert derived.records == frozenset({'alice/need', 'bob/need'})
    gate = PolicyGate({'artifact.write'}, {'recipient': {'alice/need'}})
    effects = []
    blocked = gate.mediate('artifact.write', 'agent', 'recipient',
                           {'summary': 'derived'}, derived, effects.append)
    assert not blocked['allowed'] and effects == []
    fully_scoped = PolicyGate({'artifact.write'},
                             {'recipient': {'alice/need', 'bob/need'}})
    allowed = fully_scoped.mediate('artifact.write', 'agent', 'recipient',
                                   {'summary': 'derived'}, derived,
                                   effects.append)
    assert allowed['committed'] and len(effects) == 1


def test_unknown_write_path_fails_closed_even_for_public_content():
    gate = PolicyGate({'artifact.write'})
    effects = []
    verdict = gate.mediate('alternate.message', 'agent', 'recipient',
                           {'message': 'public'}, Provenance(Label.PUBLIC),
                           effects.append)
    assert verdict['reason'] == 'unregistered_write_boundary'
    assert effects == []


def test_public_unknown_sink_allowed_but_blacklisted_sink_blocked():
    gate = PolicyGate({'artifact.write'}, untrusted_sinks={'blacklisted'})
    args = ('artifact.write', 'agent')
    public = Provenance(Label.PUBLIC)
    assert gate.authorize_write(*args, 'new-sink', {'status': 'ready'},
                                public)['allowed']
    assert not gate.authorize_write(*args, 'blacklisted',
                                    {'status': 'ready'}, public)['allowed']


def test_missing_or_unscoped_taint_cannot_be_claimed_safe():
    gate = PolicyGate({'artifact.write'})
    for provenance in (None, {'label': 'PUBLIC'}, Provenance(Label.AGENT)):
        assert not gate.authorize_write('artifact.write', 'agent', 'recipient',
                                         {'SAFE': True}, provenance)['allowed']
    with pytest.raises(ValueError):
        Provenance(Label.PUBLIC, frozenset({'private-record'}))


def test_shared_cross_sink_budget_refuses_replay_without_second_delivery():
    ledger = BudgetLedger(2)
    delivered = []
    payload = {'hint': 'a'}
    first = ledger.consider('event-1', 'agent', 'sink-a', payload, 1,
                            delivered.append)
    replay = ledger.consider('event-1', 'agent', 'sink-a', payload, 1,
                             delivered.append)
    second_sink = ledger.consider('event-1', 'agent', 'sink-b', payload, 1,
                                  delivered.append)
    overflow = ledger.consider('event-2', 'agent', 'sink-b', payload, 1,
                               delivered.append)
    assert first['committed'] and second_sink['committed']
    assert replay['reason'] == 'duplicate_event_destination'
    assert overflow['reason'] == 'registered_budget_exceeded'
    assert ledger.spent == 2 and len(delivered) == 2
    records = ledger.records
    assert records[1]['previous_hash'] == records[0]['entry_hash']
    assert ledger.head_hash == records[-1]['entry_hash']
    assert 'payload' not in records[0]
    records[0]['cost_units'] = 100
    assert ledger.records[0]['cost_units'] == 1


@pytest.mark.parametrize('changed', [
    {'event_id': 'different-event'}, {'source': 'different-source'},
    {'sink': 'different-sink'}, {'payload_sha256': '0' * 64},
    {'cost_units': '0'}, {'binding_sha256': '0' * 64},
])
def test_typed_witness_binds_every_delivery_coordinate(changed):
    ledger = BudgetLedger(1)
    payload = {'message': 'registered'}
    witness = TypedWitness.bind('e', 'sender', 'receiver', payload, 1)
    delivered = []
    verdict = ledger.consider('e', 'sender', 'receiver', payload, 1,
                              delivered.append,
                              witness=replace(witness, **changed))
    assert not verdict['allowed'] and ledger.spent == 0
    assert delivered == [] and ledger.records == []


def test_malformed_witness_refused_before_commit():
    ledger = BudgetLedger(1)
    delivered = []
    result = ledger.consider('e', 's', 'd', {}, 1, delivered.append,
                             witness={'binding_sha256': 'forged'})
    assert result['reason'] == 'malformed_witness'
    assert not delivered and ledger.spent == 0


@pytest.mark.parametrize('cost', [-1, float('nan'), float('inf'), True, '1'])
def test_invalid_cost_cannot_bypass_budget(cost):
    ledger = BudgetLedger(1)
    result = ledger.consider('e', 's', 'd', {}, cost,
                             lambda payload: pytest.fail('must not dispatch'))
    assert not result['allowed'] and ledger.spent == 0


def test_concurrent_releases_cannot_overspend_shared_ledger():
    ledger = BudgetLedger(3)
    deliveries = []

    def attempt(index):
        return ledger.consider(f'e-{index}', 'sender', f'sink-{index}',
                                {'index': index}, 1, deliveries.append)

    with ThreadPoolExecutor(max_workers=8) as executor:
        outcomes = list(executor.map(attempt, range(12)))
    assert sum(item['committed'] for item in outcomes) == 3
    assert len(deliveries) == 3 and ledger.spent == 3


def test_callback_failure_retains_charge_and_blocks_duplicate_dispatch():
    ledger = BudgetLedger(1)
    effects = []

    def partial_failure(payload):
        effects.append(payload)
        raise RuntimeError('The side effect may already have occurred')

    outcome = ledger.consider('e', 's', 'd', {'message': 'x'}, 1,
                              partial_failure)
    retry = ledger.consider('e', 's', 'd', {}, 1, effects.append)
    assert outcome['allowed'] and outcome['dispatched']
    assert not outcome['committed'] and outcome['reason'] == 'commit_error'
    assert ledger.spent == 1 and len(effects) == 1
    assert retry['reason'] == 'duplicate_event_destination'
    assert ledger.records[0]['status'] == 'commit_error'


def test_reentrant_dispatch_is_refused_without_deadlock_or_extra_charge():
    ledger = BudgetLedger(2)
    nested = []

    def callback(payload):
        nested.append(ledger.consider('nested', 's', 'd', {}, 1,
                                       lambda _: None))

    outer = ledger.consider('outer', 's', 'd', {}, 1, callback)
    assert outer['committed'] and ledger.spent == 1
    assert nested[0]['reason'] == 'reentrant_dispatch_refused'


def test_decimal_event_units_and_payload_snapshot_are_stable():
    ledger = BudgetLedger(0.3)
    original = {'proposal': ['x']}

    def callback(delivered):
        original['proposal'].append('later mutation')
        assert delivered == {'proposal': ['x']}
        return 'delivered'

    first = ledger.consider('e1', 's', 'd', original, 0.1, callback)
    second = ledger.consider('e2', 's', 'd', {}, 0.2, lambda _: None)
    assert first['result'] == 'delivered' and second['committed']
    assert ledger.spent == 0.3


def test_evaluator_objects_are_never_interpreted_as_release_metadata():
    class EvaluatorTruth:
        def __getattribute__(self, name):
            raise AssertionError('Evaluator truth must not be read')

    ledger = BudgetLedger(1)
    rejected = ledger.consider('e', 's', 'd',
                               {'evaluator_truth': EvaluatorTruth()}, 1,
                               lambda _: pytest.fail('must not dispatch'))
    assert rejected['reason'] == 'malformed_registered_event'
    assert ledger.spent == 0
    # The public interfaces have no oracle/world argument or permissive kwargs.
    for function in (BudgetLedger.consider, PolicyGate.authorize_write):
        assert not any(parameter.kind == inspect.Parameter.VAR_KEYWORD
                       for parameter in inspect.signature(function).parameters.values())
