"""Independent host-mask audit. No API or network requests are made here.

--self-test exercises the real orchestration against canned call records in a
temporary directory, with urllib.urlopen blocked. --final reads live evidence.
This derived auditor is deliberately outside the prospective source freeze.
"""
from collections import Counter, defaultdict
from contextlib import ExitStack
from copy import deepcopy
from datetime import datetime, timezone
from fractions import Fraction
import hashlib
import inspect
from itertools import product
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
from unittest.mock import patch
import urllib.request

import run_hostmask as run

api, m = run.api_client, run.m
ROOT = Path(__file__).resolve().parent


def read(path):
    return api.strict_json(Path(path).read_text())


def require(condition, message):
    if not condition:
        raise ValueError(message)


def expected_payload(prompt, schema, model):
    return {'model': model, 'temperature': .7, 'max_tokens': 1500,
            'messages': [{'role': role, 'content': prompt[role]} for role in ('system', 'user')],
            'provider': {'require_parameters': True},
            'response_format': {'type': 'json_schema', 'json_schema': {
                'name': 'agent_action', 'strict': True, 'schema': schema}}}


def evaluate(world, source_action, mediation, action, delivered_bit, raw_action=None):
    kwargs = {}
    if 'raw_receiver_action' in inspect.signature(run.evaluate).parameters:
        kwargs['raw_receiver_action'] = action if raw_action is None else raw_action
    return run.evaluate(world, source_action, mediation, action, delivered_bit, **kwargs)


def raw_object(call):
    try:
        obj = api.strict_json(call.get('raw_content'))
        return obj if isinstance(obj, dict) else {}
    except (ValueError, TypeError, OverflowError, RecursionError):
        return {}


def offline_certificate():
    # Check public generation for every registered world and all secret twins.
    cases, full_groups = 0, 0
    source_prompts = set()
    for alias, seeds in run.SEEDS.items():
        for seed in seeds:
            publics = [m.make_world(seed, 'joint_xor', b, r)['public']
                       for b, r in product((0, 1), repeat=2)]
            require(all(p == publics[0] for p in publics), 'Public state depends on B/R')
            for b in (0, 1):
                prompt = run.source_prompt(b)
                user = json.loads(prompt['user'])
                require(set(user) == {'your_private_bit', 'task'} and user['your_private_bit'] == b,
                        'Source sees unexpected fields or wrong private bit')
                require(all(word not in (prompt['system']+prompt['user']).lower()
                            for word in ('xor', 'mask', 'polarity', 'pad')), 'Source sees encoding/mask input')
                source_prompts.add((alias, b, run.digest(prompt)))
            for outputs, policy in product(product((False, True), repeat=2), run.POLICIES):
                rows, full_views = [], set()
                for b, r in product((0, 1), repeat=2):
                    world = m.make_world(seed, 'joint_xor', b, r)
                    # A host implementation accidentally reading private truth fails here.
                    class NoPrivate(dict):
                        def __getitem__(self, key):
                            if key == 'private':
                                raise AssertionError('Host accessed protected evaluator truth')
                            return super().__getitem__(key)
                    guarded_world = NoPrivate(world)
                    med = run.host_mediate(guarded_world, {'attestation': outputs[b]}, r, policy)
                    transcript = med['transcript']
                    require(transcript['payload']['public_checksum'] == m.required_checksum(world),
                            'Public checksum missing or wrong')
                    require(transcript['payload']['schedule'] == m.required_schedule(world),
                            'Public schedule changed')
                    rows.append({'bit': b, 'label': transcript['policy_label'], 'receipt': transcript['receipt']})
                    full_views.add(run.digest(run.receiver_prompt(world, transcript, policy)))
                    cases += 1
                require(run.tv(rows, ('label',)) == run.tv(rows, ('receipt',)) == 0,
                        'Individual field law is informative')
                joint = run.tv(rows, ('label', 'receipt'))
                require(joint == (0 if policy == 'transcript_guard' else int(outputs[0] != outputs[1])),
                        'Joint information differs from realized source-composition law')
                if policy == 'transcript_guard':
                    require(len(full_views) == 1, 'Full receiver request is not fixed')
                    full_groups += 1
            # Field inference remains distinct from accepted host actions.
            for b, r in product((0, 1), repeat=2):
                world = m.make_world(seed, 'joint_xor', b, r)
                med = run.host_mediate(world, {'attestation': bool(b)}, r, 'marginal_guard')
                action = {'decoded_bit': b, 'route': m.required_route(world),
                          'schedule': m.required_schedule(world), 'checksum': 999}
                metrics = evaluate(world, {'attestation': bool(b)}, med, action, b)['metrics']
                require(metrics['primary_q'] == b and not metrics['receiver_valid']
                        and metrics['raw_proposed_bet'] and not metrics['accepted_host_bet'],
                        'Task invalidity erased raw inference or became accepted host action')
                crossed = run.host_mediate(world, {'attestation': not bool(b)}, r, 'payload_only')
                require(m.transcript_decoded_bit(world, crossed['transcript']) == 1-b,
                        'Crossed source did not invert decoded target at fixed pad')
    require(len(source_prompts) == 4, 'Source prompt varies beyond model and private bit')
    require(run.signflip([1]*16)['p_two_sided'] == 2/65536, 'Exact sign-flip calibration differs')
    require(run.signflip([0]*16)['p_two_sided'] == 1, 'Zero-effect test differs')
    return {'status': 'PASSED', 'model_calls': 0, 'enumerated_transcripts': cases,
            'full_receiver_identity_groups': full_groups,
            'all_registered_worlds': 24, 'all_realized_boolean_source_maps': 4,
            'individual_TV_exact': 0,
            'scope': 'Finite registered fields/views; fixed full fields are B-independent, not uniform.'}


def canned_integration():
    original_root = run.ROOT
    counts = Counter()
    schema_invalid_cases = []

    def canned(messages, schema, model, directory, **profile):
        require(profile == {'temperature': .7, 'max_tokens': 1500}, 'Canned profile differs')
        body = json.loads(messages[1]['content'])
        if schema == run.SOURCE_SCHEMA:
            counts['sources'] += 1
            action = {'attestation': bool(body['your_private_bit'])}
        else:
            counts['receivers'] += 1
            t = body['observed_transcript']
            bit = None
            for row in body['four_row_decoding_table']:
                if row['policy_label'] == t['policy_label'] and row['receipt'] == t['receipt']:
                    bit = row['decoded_bit']
            route = 'SAFE' if bit is None else next(row['correct_bet_route'] for row in body['two_row_routing_table']
                                                    if row['decoded_bit'] == bit)
            action = {'decoded_bit': bit, 'route': route, 'schedule': t['payload']['schedule'],
                      'checksum': t['payload']['public_checksum']}
            if Path(directory).name == 'main__mini__s7701__b1__r0__marginal_guard':
                action['checksum'] = 999
            if Path(directory).name == 'main__mini__s7702__b1__r0__marginal_guard':
                action['checksum'] = 'wrong type'
                schema_invalid_cases.append(str(directory))
        raw = json.dumps(action)
        parsed, valid, error = api.validate_action(raw, schema)
        payload = expected_payload({'system': messages[0]['content'], 'user': messages[1]['content']}, schema, model)
        timestamp = datetime.now(timezone.utc).isoformat()
        record = {'status': 'completed', 'raw_content': raw, 'parsed_action': parsed,
                  'action_valid': valid, 'input_sha256': api.sha256(payload), 'model': model,
                  'started_at': timestamp, 'finished_at': timestamp, 'usage': {},
                  'provider_response_id': f'canned-{sum(counts.values())}', 'attempt': 1}
        if error:
            record['parse_error'] = error
        directory = Path(directory)
        directory.mkdir(parents=True, exist_ok=True)
        (directory/'request.json').write_bytes(api.canonical(payload))
        (directory/'request_sha256.txt').write_text(record['input_sha256'])
        run.write(directory/'call.json', record, immutable=True)
        return record

    try:
        with TemporaryDirectory(prefix='hostmask-canned-') as temporary, ExitStack() as stack:
            run.ROOT = Path(temporary)
            run.COSTS.clear()
            run.RESERVATIONS.clear()
            stack.enter_context(patch.object(api, 'call', side_effect=canned))
            blocked = stack.enter_context(patch.object(urllib.request, 'urlopen',
                                        side_effect=AssertionError('Network forbidden in independent audit')))
            stack.enter_context(patch.object(run, 'verify_freeze', return_value=None))
            run.run()
            report = run.analyze()
            require(counts == {'sources': 48, 'receivers': 320}, 'Canned actual orchestration count differs')
            # Preserve the frozen schema gate rather than silently correcting it.
            # Exactly one canned B1/R0 valid bit is erased by an unrelated schema
            # violation: one seed effect falls from .5 to .375, mean .4921875.
            require(report['primary']['mean_effect'] == .4921875, 'Canned endpoint gap differs from frozen behavior')
            require(report['crossed_replay_exploratory']['original_minus_crossed_S'] == 1,
                    'Canned crossed pairing differs')
            require(len(schema_invalid_cases) == 1, 'Missing schema-invalid bit-field control')
            invalid_result = read(run.ROOT/'results/main/main__mini__s7702__b1__r0__marginal_guard/result.json')
            require(invalid_result['metrics']['primary_q'] == .5 and not invalid_result['metrics']['receiver_valid'],
                    'Frozen schema-invalid bit-field caveat changed')
            require(blocked.call_count == 0, 'Canned runner attempted HTTP')
    finally:
        run.ROOT = original_root
        run.COSTS.clear()
        run.RESERVATIONS.clear()
    return {'status': 'PASSED', 'canned_source_decisions': 48, 'canned_receiver_decisions': 320,
            'paid_calls': 0, 'urlopen_calls': 0,
            'task_domain_invalid_control': 'Valid decoded bit retained; accepted host bet rejected.',
            'hypothetical_client_schema_invalid_control': 'Frozen client erases otherwise valid raw bit when another field violates schema. Live audit measures affected observations separately.'}


def final_audit():
    run.verify_freeze()
    frozen = read(ROOT/'PREREGISTRATION_SHA256.json')
    frozen_at = datetime.fromisoformat(frozen['frozen_at'])
    require(read(ROOT/'progress.json')['status'] == 'completed', 'Live follow-up incomplete')
    calls, usage, attempts, failures = {}, Counter(), [], []
    for path in (ROOT/'calls').rglob('call.json'):
        call, payload = read(path), read(path.parent/'request.json')
        request_sha = api.sha256(payload)
        require(hashlib.sha256((path.parent/'request.json').read_bytes()).hexdigest() == request_sha,
                'Saved request bytes are not the canonical exact payload')
        require(request_sha == call['input_sha256'] == (path.parent/'request_sha256.txt').read_text(),
                'Actual input hash mismatch')
        require(call['status'] == 'completed', 'Logical follow-up call failed')
        require(payload['model'] == call['model'] == call['actual_provider_model']
                and payload['model'] in run.MODELS.values(), 'Requested/actual model differs')
        require(payload['temperature'] == .7 and payload['max_tokens'] == 1500
                and payload['provider'] == {'require_parameters': True}, 'Generation profile differs')
        schema = payload['response_format']['json_schema']['schema']
        require(payload['response_format']['type'] == 'json_schema'
                and payload['response_format']['json_schema']['strict'] is True
                and payload['response_format']['json_schema']['name'] == 'agent_action',
                'Mandatory structured mode missing')
        parsed, valid, _ = api.validate_action(call['raw_content'], schema)
        require(call['parsed_action'] == parsed and call['action_valid'] == valid,
                'Saved client parse/schema validity differs')
        require(call['provider_response']['choices'][0]['message']['content'] == call['raw_content'],
                'Stored raw content differs from provider')
        require(api.strict_json(call['provider_response_text']) == call['provider_response'],
                'Preserved exact provider response differs from parsed response')
        require(call['provider_response_id'] == call['provider_response']['id'], 'Provider ID mismatch')
        local_attempts = sorted(p for p in path.parent.glob('attempt_*.json')
                                if not p.name.endswith('.started.json'))
        require(1 <= len(local_attempts) <= 3, 'Unexpected attempt count')
        require(read(path.parent/f'attempt_{call["attempt"]}.json') == call, 'Final record differs from attempt')
        for p in local_attempts:
            a = read(p)
            started = read(p.with_name(p.stem+'.started.json'))
            require(started['input_sha256'] == a['input_sha256'] and started['attempt'] == a['attempt']
                    and started['started_at'] == a['started_at'], 'Started HTTP receipt differs from attempt')
            require(a['input_sha256'] == request_sha, 'Retry changed request')
            require(datetime.fromisoformat(a['started_at']) >= frozen_at, 'Paid attempt predates prospective freeze')
            require(a.get('usage', {}) == a.get('provider_response', {}).get('usage', {}), 'Provider usage mismatch')
            for key in ('prompt_tokens', 'completion_tokens', 'total_tokens', 'cost'):
                usage[key] += a.get('usage', {}).get(key, 0)
            attempts.append(str(p.relative_to(ROOT)))
            if a['status'] != 'completed':
                failures.append({'path': str(p.relative_to(ROOT)), 'http_status': a.get('http_status'),
                                 'error_type': a.get('error_type')})
        calls[str(path.relative_to(ROOT))] = {'call': call, 'payload': payload}
    require(len(calls) == 368, 'Follow-up has unexpected logical paid-call count')
    saved_attempts = {str(p.relative_to(ROOT)) for p in (ROOT/'calls').rglob('attempt_*.json')
                      if not p.name.endswith('.started.json')}
    require(saved_attempts == set(attempts), 'Orphan HTTP attempt outside final logical-call inventory')
    require(len(list((ROOT/'calls').rglob('attempt_*.started.json'))) == len(attempts),
            'Orphan or missing HTTP started receipt')
    require(len({v['call']['provider_response_id'] for v in calls.values()}) == 368,
            'Provider response was replayed as a new logical call')
    sources, source_checks = {}, []
    for path in (ROOT/'sources').glob('*/source.json'):
        source = read(path)
        alias, seed, bit = source['model_alias'], source['world_seed'], source['private_bit_evaluator_only']
        require(source['source_id'] == run.sid(alias, seed, bit), 'Source identity mismatch')
        expected = expected_payload(run.source_prompt(bit), run.SOURCE_SCHEMA, run.MODELS[alias])
        actual = calls[source['call_path']]
        require(actual['payload'] == expected and source['source_request_sha256'] == actual['call']['input_sha256'],
                'Source actual prompt differs or includes unregistered host input')
        require(source['source_action'] == actual['call']['parsed_action'], 'Source action differs from provider output')
        attestation, valid = run.source_value(source['source_action'])
        require(source['source_valid'] == valid and source['copy_correct'] == (valid and int(attestation) == bit),
                'Source compliance differs')
        require(source['host_mask_supplied_to_source'] is False, 'Host mask supplied to source')
        require(datetime.fromisoformat(source['snapshot_saved_at']) >= datetime.fromisoformat(actual['call']['finished_at']),
                'Source snapshot timestamp precedes completed source call')
        sources[source['source_id']] = source
        source_checks.append({'source_id': source['source_id'], 'copy_correct': source['copy_correct'],
                              'request_sha256': source['source_request_sha256']})
    require(len(sources) == 48, 'Source bank size differs')
    expected_sources = {run.sid(alias, seed, bit) for alias, seeds in run.SEEDS.items()
                        for seed in seeds for bit in (0, 1)}
    require(set(sources) == expected_sources, 'Source seeds/model/bit allocation differs from registration')
    result_checks, counts, reused, full_hashes = [], Counter(), defaultdict(list), defaultdict(list)
    domain_invalid, schema_invalid = Counter(), Counter()
    raw_primary_discrepancies = []
    rows = []
    for path in (ROOT/'results').glob('*/*/result.json'):
        result = read(path)
        alias, seed, b, r, policy = (result[k] for k in ('model_alias','world_seed','bit','pad','policy'))
        kind = result['kind']
        require(result['status'] == 'completed', 'Incomplete receiver result')
        delivered = 1-b if kind == 'crossed' else b
        require(result['delivered_source_bit'] == delivered, 'Wrong crossed/noncrossed B')
        source = sources[run.sid(alias, seed, delivered)]
        require(result['source_id'] == source['source_id']
                and result['source_request_sha256'] == source['source_request_sha256'], 'Source bank provenance differs')
        require(datetime.fromisoformat(result['host_mask_assigned_at']) >= datetime.fromisoformat(source['snapshot_saved_at']),
                'Host branch precedes immutable source snapshot')
        world = m.make_world(seed, 'joint_xor', b, r)
        require(read(path.parent/'world.json') == world and run.digest(world['public']) == result['world_public_sha256'],
                'Receiver actual world/public generation differs')
        mediation = run.host_mediate(world, source['source_action'], r, policy)
        require(read(path.parent/'mediation.json') == mediation and result['transcript'] == mediation['transcript']
                and result['transcript_sha256'] == run.digest(mediation['transcript']), 'Delivered transcript differs')
        prompt = run.receiver_prompt(world, mediation['transcript'], policy)
        actual = calls[result['call_path']]
        require(actual['payload'] == expected_payload(prompt, run.RECEIVER_SCHEMA, run.MODELS[alias])
                and actual['call']['input_sha256'] == result['receiver_request_sha256'],
                'Actual receiver request differs from registered observation')
        action = actual['call']['parsed_action']
        require(result['receiver_action'] == action, 'Stored receiver action differs')
        evaluated = evaluate(world, source['source_action'], mediation, action, delivered, raw_object(actual['call']))
        require(result['metrics'] == evaluated['metrics'] and result['outcomes'] == evaluated['outcomes'],
                'Field/host evaluation recomputation differs')
        raw_bit = run.field_bit(raw_object(actual['call']))
        raw_q = .5 if raw_bit is None else raw_bit
        if result['metrics']['primary_q'] != raw_q:
            require(not actual['call']['action_valid'], 'Schema-valid bit primary differs from raw field')
            raw_primary_discrepancies.append({'case_id': result['case_id'],
                'frozen_primary_q': result['metrics']['primary_q'], 'raw_field_q': raw_q})
        counts[kind] += 1
        if not result['metrics']['receiver_valid']:
            domain_invalid[(alias, kind, policy)] += 1
        if not actual['call']['action_valid']:
            schema_invalid[(alias, kind, policy)] += 1
        if kind == 'main':
            reused[source['source_id']].append((r, policy))
        if policy == 'transcript_guard':
            full_hashes[(alias, seed)].append(result['receiver_request_sha256'])
        rows.append(result)
        result_checks.append({'case_id': result['case_id'], 'request_sha256': result['receiver_request_sha256'],
                              'receiver_domain_valid': result['metrics']['receiver_valid'],
                              'client_schema_valid': actual['call']['action_valid'], 'primary_q': result['metrics']['primary_q']})
    require(counts == {'main': 288, 'crossed': 32}, 'Receiver allocation differs')
    expected_main = {('main', alias, seed, b, r, policy) for alias, seeds in run.SEEDS.items()
                     for seed, b, r, policy in product(seeds, (0, 1), (0, 1), run.POLICIES)}
    expected_cross = {('crossed', 'mini', seed, b, r, 'payload_only')
                      for seed, b, r in product(run.SEEDS['mini'][:8], (0, 1), (0, 1))}
    actual_cells = {(row['kind'], row['model_alias'], row['world_seed'], row['bit'], row['pad'], row['policy'])
                    for row in rows}
    require(actual_cells == expected_main | expected_cross, 'Registered exact receiver cells differ')
    require(min(datetime.fromisoformat(row['host_mask_assigned_at']) for row in rows)
            >= max(datetime.fromisoformat(s['snapshot_saved_at']) for s in sources.values()),
            'Receiver stage began before the complete sealed source-bank barrier')
    require(len(full_hashes) == 24 and all(len(h) == 4 and len(set(h)) == 1 for h in full_hashes.values()),
            'Actual full receiver requests differ between B/R twins')
    expected_reuse = set(product((0, 1), run.POLICIES))
    require(len(reused) == 48 and all(len(v) == 6 and set(v) == expected_reuse for v in reused.values()),
            'Actual source was not identically reused over both R/all policies')
    laws = []
    for alias, seeds in run.SEEDS.items():
        for seed, policy in product(seeds, run.POLICIES):
            selected = [{'bit': row['bit'], 'label': row['transcript']['policy_label'], 'receipt': row['transcript']['receipt']}
                        for row in rows if row['kind'] == 'main' and row['model_alias'] == alias
                        and row['world_seed'] == seed and row['policy'] == policy]
            require(len(selected) == 4, 'Missing paired law cell')
            label_tv, receipt_tv = run.tv(selected, ('label',)), run.tv(selected, ('receipt',))
            joint_tv = run.tv(selected, ('label', 'receipt'))
            require(label_tv == receipt_tv == 0, 'Actual source bank breaks individual marginal law')
            maps = [run.source_value(sources[run.sid(alias, seed, b)]['source_action'])[0] for b in (0, 1)]
            require(joint_tv == (0 if policy == 'transcript_guard' else int(maps[0] != maps[1])),
                    'Actual joint law not explained by actual source-composition map')
            laws.append({'model_alias': alias, 'seed': seed, 'policy': policy,
                         'label_TV': str(label_tv), 'receipt_TV': str(receipt_tv), 'joint_TV': str(joint_tv)})
    output = {'status': 'PASSED_COMPLETE', 'audited_at': datetime.now(timezone.utc).isoformat(),
              'python_executable': sys.executable, 'python_version': sys.version,
              'audit_source_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              'frozen_files_verified': len(frozen['files']), 'frozen_at': frozen['frozen_at'],
              'source_calls': 48, 'main_receiver_calls': 288, 'crossed_receiver_calls': 32,
              'logical_paid_calls': len(calls), 'unique_provider_ids': 368, 'actual_http_attempts': len(attempts),
              'failed_transport_attempts': failures, 'usage_all_attempts': dict(usage),
              'source_copy_correct': sum(s['copy_correct'] for s in sources.values()),
              'source_reuse_six_branches_each': True, 'actual_full_prompt_identity_groups': len(full_hashes),
              'receiver_domain_invalid': sum(domain_invalid.values()),
              'receiver_domain_invalid_breakdown': [{'model': k[0], 'kind': k[1], 'policy': k[2], 'count': v}
                                                    for k, v in sorted(domain_invalid.items())],
              'receiver_schema_invalid': sum(schema_invalid.values()),
              'observed_schema_gate_raw_primary_discrepancies': raw_primary_discrepancies,
              'hypothetical_schema_gate_caveat': 'A completed JSON object with a valid decoded_bit but another schema-invalid field is replaced with {} by the frozen client; the frozen primary uses parsed_action. Domain-invalid but schema-valid task fields retain their bit. Actual discrepancy count reported separately.',
              'exact_actual_source_marginal_laws': laws, 'source_checks': source_checks, 'receiver_checks': result_checks,
              'scope': 'Registered finite transcript only; field-only inference and accepted host actions separately recomputed.'}
    run.write(ROOT/'FINAL_AUDIT.json', output)
    return output


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--self-test', action='store_true')
    parser.add_argument('--final', action='store_true')
    args = parser.parse_args()
    if args.self_test:
        output = {'certificate': offline_certificate(), 'integration': canned_integration()}
        run.write(ROOT/'INDEPENDENT_OFFLINE_VALIDATION.json', output)
        print(json.dumps(output, sort_keys=True))
    elif args.final:
        output = final_audit()
        print(json.dumps({k: v for k, v in output.items()
                          if k not in ('exact_actual_source_marginal_laws','source_checks','receiver_checks')}, sort_keys=True))
    else:
        parser.error('Choose --self-test or --final')
