"""Independent realized-source-bank composition audit; no receiver outcomes/API.

Information quantities describe four equally weighted realized (B,R) cells per
public world, not a calibrated distribution over repeated LLM generations.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timezone
from fractions import Fraction
import hashlib
from itertools import product
import json
import math
from pathlib import Path

import mechanism as m

ROOT = Path(__file__).resolve().parent


def read(path):
    return json.loads(Path(path).read_text())


def digest(value):
    return hashlib.sha256(m.canonical(value).encode()).hexdigest()


def entropy(rows, fields):
    counts = Counter(tuple(row[field] for field in fields) for row in rows)
    n = len(rows)
    value = -sum((count/n) * math.log2(count/n) for count in counts.values())
    return 0.0 if abs(value) < 1e-12 else value


def mutual_information(rows, left, right):
    fields = tuple(dict.fromkeys(left + right))
    value = entropy(rows, left) + entropy(rows, right) - entropy(rows, fields)
    if -1e-12 < value < 0:
        value = 0.0
    assert value >= 0
    return value


def conditional_information(rows, left, right, given):
    value = (entropy(rows, tuple(dict.fromkeys(left+given))) +
             entropy(rows, tuple(dict.fromkeys(right+given))) - entropy(rows, given) -
             entropy(rows, tuple(dict.fromkeys(left+right+given))))
    if -1e-12 < value < 0:
        value = 0.0
    assert value >= 0
    return value


def total_variation(rows, fields):
    laws = []
    for bit in (0, 1):
        selected = [row for row in rows if row['bit'] == bit]
        counts = Counter(tuple(row[field] for field in fields) for row in selected)
        laws.append({key: Fraction(count, len(selected)) for key, count in counts.items()})
    value = sum((abs(laws[0].get(k, 0)-laws[1].get(k, 0))
                 for k in set(laws[0]) | set(laws[1])), Fraction(0))/2
    return value


def quantities(rows):
    il = mutual_information(rows, ('bit',), ('label',))
    ir = mutual_information(rows, ('bit',), ('receipt',))
    ij = mutual_information(rows, ('bit',), ('label', 'receipt'))
    conditional = conditional_information(rows, ('bit',), ('receipt',), ('label',))
    assert math.isclose(il+conditional, ij, abs_tol=1e-12)
    lt, rt, jt = (total_variation(rows, fields)
                  for fields in (('label',), ('receipt',), ('label', 'receipt')))
    full = total_variation(rows, ('transcript_sha256',))
    return {'I_B_label_bits': il, 'I_B_receipt_bits': ir,
            'I_B_joint_bits': ij, 'I_B_receipt_given_label_bits': conditional,
            'unconditional_field_sum_bits': il+ir,
            'conditional_chain_rule_sum_bits': il+conditional,
            'joint_minus_unconditional_field_sum_bits': ij-il-ir,
            'TV_label': float(lt), 'TV_receipt': float(rt), 'TV_joint': float(jt),
            'TV_full_registered_transcript': float(full),
            'individual_marginals_zero_joint_one': lt == rt == 0 and jt == 1,
            'finite_bank_best_balanced_bit_accuracy': float((1+jt)/2),
            'cells': rows}


def run_audit():
    manifest = read(ROOT / 'manifest.json')
    frozen = read(ROOT / 'PREREGISTRATION_SHA256.json')
    frozen_checks = []
    for entry in frozen['files']:
        path = ROOT / entry['path']
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        assert actual == entry['sha256'], 'Frozen file changed: ' + entry['path']
        frozen_checks.append({'path': entry['path'], 'sha256': actual})
    inventory, source_lookup, errors, invalid = [], {}, [], []
    validity_groups = defaultdict(Counter)
    for alias, seeds in manifest['seeds'].items():
        for seed, carrier in product(seeds, manifest['carriers']):
            pads = (0, 1) if carrier == 'joint_xor' else (0,)
            for bit, pad in product((0, 1), pads):
                identifier = f'{alias}__s{seed}__{carrier}__b{bit}__r{pad}'
                path = ROOT / 'sources' / identifier / 'source.json'
                source = read(path)
                world = m.make_world(seed, carrier, bit, pad)
                assert read(ROOT/source['world_path']) == world
                assert source['world_public_sha256'] == digest(world['public'])
                assert source['world_sha256'] == digest(world)
                call = read(ROOT/source['source_call_path'])
                request = read(ROOT/source['source_request_path'])
                assert digest(request) == source['source_request_sha256'] == call['input_sha256']
                assert source['status'] == call['status'] == 'completed', identifier
                try:
                    parsed = m.parse_sender(call.get('parsed_action', {}))
                    domain_valid = True
                except (ValueError, TypeError, OverflowError):
                    parsed, domain_valid = {}, False
                expected_valid = domain_valid and bool(call.get('action_valid'))
                assert source['source_valid'] == expected_valid
                assert source['sender_action'] == parsed
                compliant = None
                if expected_valid:
                    expected = m.registered_sender_action(world)
                    fields = {'policy_label': ('tag_selector',), 'numeric_receipt': ('probe_valid',),
                              'rejection_status': ('request_token',),
                              'joint_xor': ('tag_selector', 'probe_valid')}[carrier]
                    compliant = all(parsed[field] == expected[field] for field in fields)
                row = {'source_id': identifier, 'model_alias': alias, 'world_seed': seed,
                       'carrier': carrier, 'bit': bit, 'pad': pad,
                       'source_valid': expected_valid,
                       'source_schema_valid': source.get('source_schema_valid'),
                       'encoding_correct': compliant,
                       'sender_action': source['sender_action'],
                       'source_path': str(path.relative_to(ROOT)),
                       'source_request_sha256': source['source_request_sha256']}
                inventory.append(row)
                source_lookup[(alias, seed, carrier, bit, pad)] = (row, world)
                group = validity_groups[(alias, carrier)]
                group['sources'] += 1
                group['domain_valid'] += expected_valid
                group['codebook_compliant'] += compliant is True
                group['codebook_noncompliant'] += compliant is False
                if not expected_valid:
                    invalid.append(row)
    assert len(inventory) == manifest['main_source_calls'] == 400
    worlds = []
    for alias, seeds in manifest['seeds'].items():
        for seed in seeds:
            policy_rows = {}
            adherence = []
            public_hashes = set()
            for policy in manifest['policies']:
                observations = []
                for bit, pad in product((0, 1), (0, 1)):
                    row, world = source_lookup[(alias, seed, 'joint_xor', bit, pad)]
                    public_hashes.add(digest(world['public']))
                    mediated = m.mediate(world, row['sender_action'], policy)
                    t = mediated['transcript']
                    observations.append({'bit': bit, 'pad': pad,
                        'label': t['policy_label'], 'receipt': t['receipt'], 'status': t['status'],
                        'transcript_sha256': digest(t), 'source_id': row['source_id'],
                        'source_valid': row['source_valid'], 'encoding_correct': row['encoding_correct']})
                    if policy == 'payload_only':
                        adherence.append(row['encoding_correct'] is True)
                q = quantities(observations)
                if policy == 'transcript_guard':
                    assert q['TV_full_registered_transcript'] == 0
                    assert q['I_B_joint_bits'] == 0
                policy_rows[policy] = q
            assert len(public_hashes) == 1
            worlds.append({'model_alias': alias, 'world_seed': seed,
                           'world_public_sha256': next(iter(public_hashes)),
                           'all_four_sources_compliant': all(adherence),
                           'compliant_sources': sum(adherence),
                           'policies': policy_rows})
    summary = {}
    for alias in manifest['models']:
        selected = [row for row in worlds if row['model_alias'] == alias]
        summary[alias] = {'worlds': len(selected),
                         'all_four_sources_compliant_worlds': sum(row['all_four_sources_compliant'] for row in selected),
                         'policies': {}}
        for policy in manifest['policies']:
            qs = [row['policies'][policy] for row in selected]
            fields = ['I_B_label_bits', 'I_B_receipt_bits', 'I_B_joint_bits',
                      'I_B_receipt_given_label_bits', 'unconditional_field_sum_bits',
                      'conditional_chain_rule_sum_bits', 'TV_label', 'TV_receipt',
                      'TV_joint', 'TV_full_registered_transcript']
            summary[alias]['policies'][policy] = {
                'individual_marginals_zero_joint_one_worlds': sum(q['individual_marginals_zero_joint_one'] for q in qs),
                'world_mean': {key: sum(q[key] for q in qs)/len(qs) for key in fields}}
    return {'status': 'PASSED_STRUCTURAL_SOURCE_AUDIT',
            'generated_at': datetime.now(timezone.utc).isoformat(),
            'model_calls': 0, 'receiver_outcomes_inspected': False,
            'frozen_files_unchanged': len(frozen_checks),
            'main_source_records': len(inventory), 'joint_worlds': len(worlds),
            'source_validity': [{'model_alias': alias, 'carrier': carrier, **dict(counts)}
                                for (alias, carrier), counts in sorted(validity_groups.items())],
            'invalid_source_records': invalid, 'source_errors': errors,
            'joint_source_summary': summary, 'joint_worlds_detail': worlds,
            'source_inventory': inventory,
            'interpretation': 'These are exact information quantities of the realized equally weighted '
                'four-cell(B,R) source bank in each fixed public world. They do not calibrate the '
                'underlying stochastic LLM kernel, establish repeated-generation privacy costs, '
                'or replace receiver behavior/causal controls. All malformed/noncompliant source '
                'actions remain included through the frozen host fallback.',
            'conditional_accounting_note': 'I(B;label)+I(B;receipt|label)=I(B;label,receipt). '
                'The ideal XOR bank has0+1bit conditional accounting despite0+0 unconditional '
                'marginal information. This is the classical chain rule, not a novel budget theorem.'}


if __name__ == '__main__':
    result = run_audit()
    target = ROOT / 'source_composition_audit.json'
    target.write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    print(json.dumps({'status': result['status'], 'model_calls': 0,
                      'invalid_sources': len(result['invalid_source_records']),
                      'summary': result['joint_source_summary'], 'report': str(target)}))
