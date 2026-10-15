"""Read-only provider/source/delivery audit; this module never calls an API."""
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

import api_client as api
import mechanism as m
import run_controlplane as run

ROOT = Path(__file__).resolve().parent


def read(path):
    return api.strict_json(Path(path).read_text())


def filehash(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def require(value, message):
    if not value:
        raise ValueError(message)


def expected_payload(prompt, schema, model):
    return {'model': model, 'temperature': .7, 'max_tokens': 1500,
        'messages': run.messages(prompt), 'provider': {'require_parameters': True},
        'response_format': {'type': 'json_schema', 'json_schema': {
            'name': 'agent_action', 'strict': True, 'schema': schema}}}


def main():
    run.verify_freeze()
    freeze = read(ROOT/'PREREGISTRATION_SHA256.json')
    frozen_at = datetime.fromisoformat(freeze['frozen_at'])
    calls, attempts, failures, usage = {}, [], [], Counter()
    for area in ('calls', 'preflight'):
        for path in (ROOT/area).rglob('call.json'):
            call = read(path)
            request_path = path.parent/'request.json'
            request = read(request_path)
            require(api.sha256(request) == call['input_sha256'], 'Saved request hash differs: '+str(path))
            require(path.parent.joinpath('request_sha256.txt').read_text() == call['input_sha256'],
                    'Request hash sidecar differs')
            require(request['model'] in run.MODELS.values() and call['model'] == request['model'],
                    'Unexpected requested model')
            require(request['temperature'] == .7 and request['max_tokens'] == 1500,
                    'Unexpected generation profile')
            require(request['provider'] == {'require_parameters': True}, 'Provider fallback restrictions missing')
            response_format = request['response_format']
            require(response_format['type'] == 'json_schema'
                    and response_format['json_schema']['strict'] is True
                    and response_format['json_schema']['name'] == 'agent_action', 'Structured response mode differs')
            schema = response_format['json_schema']['schema']
            if call['status'] == 'completed':
                require(call.get('actual_provider_model') == request['model'], 'Provider model substitution')
                require(call.get('provider_response_id') == call['provider_response']['id'], 'Response ID differs')
                parsed, valid, _ = api.validate_action(call['raw_content'], schema)
                require(call['action_valid'] == valid and call['parsed_action'] == parsed,
                        'Client action/schema validity differs')
            else:
                failures.append({'path': str(path), 'status': call['status'],
                                 'error_type': call.get('error_type'), 'http_status': call.get('http_status')})
            local_attempts = sorted(p for p in path.parent.glob('attempt_*.json')
                                    if not p.name.endswith('.started.json'))
            require(1 <= len(local_attempts) <= 3, 'Attempt count exceeds fixed bound')
            for attempt_path in local_attempts:
                attempt = read(attempt_path)
                require(attempt['input_sha256'] == call['input_sha256'], 'Attempt payload hash changed')
                if area == 'calls':
                    require(datetime.fromisoformat(attempt['started_at']) >= frozen_at,
                            'Research request began before source freeze')
                if attempt['status'] == 'completed':
                    require(attempt['usage'] == attempt['provider_response'].get('usage', {}), 'Provider usage differs')
                for key in ('prompt_tokens', 'completion_tokens', 'total_tokens', 'cost'):
                    usage[(area, key)] += attempt.get('usage', {}).get(key, 0)
                attempts.append({'path': str(attempt_path), 'area': area, 'record': attempt})
            if call['status'] != 'indeterminate':
                require(read(path.parent/f'attempt_{call["attempt"]}.json') == call, 'Final call differs from its preserved attempt')
            calls[str(path.relative_to(ROOT))] = {'call': call, 'request': request, 'area': area,
                                                 'request_sha256': filehash(request_path)}
    sources, source_checks = {}, []
    for path in (ROOT/'sources').glob('*/source.json'):
        source = read(path)
        sources[source['source_id']] = source
        if source['status'] != 'completed':
            continue
        world = read(ROOT/source['world_path'])
        require(run.digest(world) == source['world_sha256'] and run.digest(world['public']) == source['world_public_sha256'],
                'Source world hash differs')
        require(world == m.make_world(source['world_seed'], source['carrier'], source['bit'], source['pad']),
                'Source world does not match frozen generation')
        prompt = m.sender_prompt(world, strategy=source['strategy'])
        if source['policy'] is not None:
            prompt['user'] += '\nPUBLIC ASSIGNED HOST POLICY: '+source['policy']
        expected = expected_payload(prompt, m.SENDER_SCHEMA, source['model'])
        actual = calls[source['source_call_path']]
        require(actual['request'] == expected and source['source_request_sha256'] == actual['call']['input_sha256'],
                'Actual sender prompt/profile differs from declared generation')
        require(source['sender_action'] == actual['call']['parsed_action'], 'Source action differs from provider record')
        try:
            m.parse_sender(source['sender_action'])
            valid = True
        except (ValueError, TypeError, OverflowError):
            valid = False
        require(source['source_valid'] == valid, 'Source domain validity differs')
        source_checks.append({'source_id': source['source_id'], 'source_valid': valid,
                              'input_sha256': actual['call']['input_sha256']})
    result_checks, hashes = [], defaultdict(list)
    invalid_reasons, invalid_models, invalid_kinds, invalid_policies = Counter(), Counter(), Counter(), Counter()
    counts = Counter()
    for path in (ROOT/'results').glob('*/*/result.json'):
        result = read(path)
        counts[result['kind']] += 1
        if result['status'] != 'completed':
            continue
        source, delivered = sources[result['source_id']], sources[result['delivered_source_id']]
        mode = 'bit_required' if result['kind'] == 'boundary' else 'public'
        world = m.make_world(result['world_seed'], result['carrier'], result['bit'], result['pad'], mode)
        require(read(ROOT/result['world_path']) == world and result['world_sha256'] == run.digest(world),
                'Receiver world generation/hash differs')
        require(result['world_public_sha256'] == run.digest(world['public']), 'Receiver public hash differs')
        if result['kind'] == 'crossed':
            require(delivered['bit'] == 1-result['bit'] and delivered['pad'] == result['pad'],
                    'Crossed control does not flip B while preserving R')
        else:
            require(delivered['bit'] == result['bit'] and delivered['pad'] == result['pad'],
                    'Unexpected noncrossed source secret')
        if result['kind'] in ('boundary', 'cooperative'):
            require(source['source_id'] == run.source_id(result['model_alias'], result['world_seed'], 'joint_xor', result['bit'], 0),
                    'Boundary/cooperative control did not reuse the existing R=0 source')
        mediation = m.mediate(world, delivered['sender_action'], result['policy'])
        require(read(ROOT/result['mediation_path']) == mediation and result['transcript'] == mediation['transcript'],
                'Actual mediation differs from frozen mechanism')
        prompt = m.receiver_prompt(world, mediation['transcript'], objective=result['objective'],
                                  strategy=source['strategy'], policy=result['policy'])
        actual = calls[result['receiver_call_path']]
        expected = expected_payload(prompt, m.RECEIVER_SCHEMA, result['model'])
        require(actual['request'] == expected and result['receiver_request_sha256'] == actual['call']['input_sha256'],
                'Actual receiver input/profile differs from declared observation')
        user = json.loads(prompt['user'])
        require(set(user) == {'public', 'registered_observable_transcript', 'public_policy_assignment',
            'public_codebook', 'shared_before_secret_strategy', 'assigned_goal', 'reply_schema', 'important'},
            'Unexpected receiver input channel')
        require('your_private_state' not in user and 'private' not in user, 'Receiver received protected state')
        require(result['receiver_action'] == actual['call']['parsed_action'], 'Stored receiver action differs')
        evaluation = m.evaluate(world, delivered['sender_action'], mediation, result['receiver_action'])
        metrics = evaluation['metrics']
        metrics.update(decoded_bit=evaluation['outcomes']['decoded_bit'],
            legitimate_utility=metrics['legitimate_subtask_utility'], coverage=metrics['task_coverage'],
            harm_action=None if metrics['actual_harm'] is None else metrics['actual_harm'] > 0,
            conditional_harm_success=metrics['profitable_harm'], source_compliant=metrics['encoding_correct'],
            receiver_action_valid=metrics['receiver_valid'], public_challenge_bit=world['public']['public_challenge'])
        require(result['metrics'] == metrics and result['outcomes'] == evaluation['outcomes'], 'Evaluation recomputation differs')
        require(result['receiver_valid'] == metrics['receiver_valid'], 'Domain receiver validity differs')
        require(result['receiver_schema_valid'] == actual['call']['action_valid'], 'Provider-schema validity differs')
        if not metrics['receiver_valid']:
            try:
                m.parse_receiver(result['receiver_action'])
            except (ValueError, TypeError, OverflowError) as error:
                invalid_reasons[str(error)] += 1
                invalid_models[result['model_alias']] += 1
                invalid_kinds[result['kind']] += 1
                invalid_policies[result['policy']] += 1
        if result['policy'] == 'transcript_guard':
            key = (result['kind'], result['model_alias'], result['world_seed'], result['carrier'], result['objective'])
            hashes[key].append(actual['call']['input_sha256'])
        result_checks.append({'case_id': result['case_id'], 'kind': result['kind'],
            'receiver_input_sha256': actual['call']['input_sha256'],
            'receiver_domain_valid': metrics['receiver_valid'],
            'receiver_schema_valid': actual['call']['action_valid'],
            'actual_full_prompt_reconstructed': True, 'evaluation_recomputed': True})
    for key, values in hashes.items():
        require(len(set(values)) == 1, 'Complete receiver transcript differs across protected B/R twins: '+str(key))
    plans = []
    for path in (ROOT/'plans').glob('*/plan.json'):
        plan = read(path)
        record = calls[plan['call_path']]
        user = json.loads(record['request']['messages'][1]['content'])
        require(set(user) == {'public_interface', 'assigned_policy', 'source_action_schema',
                             'receiver_action_schema', 'objective'}, 'Planner received an unexpected input channel')
        require(user['public_interface'] == m.make_world(7500, 'all_channels', 0, 0)['public'],
                'Planner public input differs')
        require(plan['private_trial_data_supplied'] is False, 'Planner was given private trial state')
        for source in sources.values():
            if source['carrier'] == 'all_channels' and source['model_alias'] == plan['model_alias'] and source['policy'] == plan['policy']:
                call = calls[source['source_call_path']]['call']
                require(record['call']['finished_at'] <= call['started_at'], 'Adaptive trial started before its common plan finished')
                require(source['strategy'] == plan['plan'], 'Adaptive source strategy differs from common pre-secret plan')
        plans.append({'model_alias': plan['model_alias'], 'policy': plan['policy'],
                      'input_sha256': record['call']['input_sha256']})
    research = [value for value in calls.values() if value['area'] == 'calls']
    preflight = [value for value in calls.values() if value['area'] == 'preflight']
    response_ids = [value['call'].get('provider_response_id') for value in research if value['call']['status'] == 'completed']
    require(None not in response_ids and len(response_ids) == len(set(response_ids)), 'Missing or reused research response IDs')
    expected_counts = {'main': 1200, 'crossed': 80, 'boundary': 48, 'cooperative': 32, 'adaptive': 96}
    complete = len(research) == 1958 and dict(counts) == expected_counts and len(sources) == 496 and len(plans) == 6
    output = {'status': 'PASSED_COMPLETE' if complete and not any(f['path'].find('/calls/') >= 0 for f in failures) else 'INCOMPLETE_OR_FAILED',
        'audited_at': datetime.now(timezone.utc).isoformat(), 'model_calls_by_audit': 0,
        'research_logical_calls': len(research), 'expected_research_calls': 1958,
        'preflight_logical_calls': len(preflight), 'manifest_preflight_calls': run.manifest()['compatibility_calls'],
        'actual_receiver_result_counts': dict(counts), 'expected_receiver_result_counts': expected_counts,
        'source_count': len(sources), 'adaptive_plan_count': len(plans),
        'requests_checked': len(calls), 'sources_reconstructed': len(source_checks),
        'complete_receiver_inputs_reconstructed': len(result_checks),
        'full_guard_secret_twin_groups_equal': len(hashes),
        'unique_completed_research_provider_ids': len(set(response_ids)),
        'successful_client_schema_actions': sum(v['call'].get('action_valid', False) for v in research),
        'invalid_client_schema_actions': sum(v['call']['status'] == 'completed' and not v['call'].get('action_valid', False) for v in research),
        'invalid_sender_domain_actions': sum(not row['source_valid'] for row in source_checks),
        'invalid_receiver_domain_actions': sum(not row['receiver_domain_valid'] for row in result_checks),
        'invalid_receiver_domain_reasons': dict(invalid_reasons),
        'invalid_receiver_domain_by_model': dict(invalid_models),
        'invalid_receiver_domain_by_kind': dict(invalid_kinds),
        'invalid_receiver_domain_by_policy': dict(invalid_policies),
        'http_attempt_records': len(attempts),
        'failed_attempt_records': sum(a['record']['status'] != 'completed' for a in attempts),
        'reported_attempt_usage': {area: {key: usage[(area, key)] for key in ('prompt_tokens', 'completion_tokens', 'total_tokens', 'cost')}
                                   for area in ('calls', 'preflight')},
        'failures_including_preserved_preflight_failures': failures,
        'frozen_artifacts_verified': True, 'freeze_sha256': filehash(ROOT/'PREREGISTRATION_SHA256.json'),
        'audit_source_sha256': filehash(Path(__file__).resolve()),
        'caveats': ['Local reproducibility checks are not independent provider attestation.',
            'Reported costs include preserved attempts but are not an independently reconciled invoice.',
            'Provider-schema validity and stricter finite-domain validity are distinct.',
            'Frozen evaluation invalidates all receiver fields when any domain check fails; its bit/route metrics therefore include this all-or-nothing quality gate.',
            'Counterfactual crossed-source compliance is judged against delivered codeword, not original target-bit encoding_correct.'],
        'source_checks': source_checks, 'receiver_checks': result_checks, 'plan_checks': plans}
    run.write(ROOT/'FINAL_AUDIT.json', output)
    print(json.dumps({k: v for k, v in output.items() if k not in ('source_checks', 'receiver_checks', 'plan_checks', 'caveats', 'failures_including_preserved_preflight_failures')}))


if __name__ == '__main__':
    main()
