"""Independent read-only audit of joint follow-up transport and delivery evidence."""
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path

import run_joint as joint

ROOT, MAIN = joint.ROOT, joint.MAIN_ROOT


def require(condition, message):
    if not condition:
        raise ValueError(message)


def score_fields(value):
    if isinstance(value, dict):
        return sum(key == 'joint_reward' for key in value) + sum(score_fields(v) for v in value.values())
    if isinstance(value, list):
        return sum(score_fields(v) for v in value)
    return 0


def utc(value):
    return datetime.fromisoformat(value)


def main():
    joint.verify()
    base, inner = joint.load_base()
    proxy = base.DOMAINS[joint.SCENARIO]
    freeze = joint.read(ROOT/'PREREGISTRATION_SHA256.json')
    frozen_at = utc(freeze['frozen_at'])
    reuse = joint.read(ROOT/'PREFIX_REUSE_MANIFEST.json')
    require(len(reuse['prefixes']) == 20, 'Exactly 20 source prefixes must be reused')
    copied_attempts, copied_calls, new_calls, new_attempts, branches = [], [], [], [], []
    usage = Counter()
    source_usage = Counter()
    copied_file_count = 0
    for item in reuse['prefixes']:
        source_prefix = Path(item['source_prefix_path'])
        copied_prefix = Path(item['copied_prefix_path'])
        require(joint.filehash(source_prefix) == joint.filehash(copied_prefix) == item['prefix_file_sha256'],
                'Source and reused prefix byte hashes differ')
        prefix = joint.read(copied_prefix)
        require(joint.digest(prefix) == item['prefix_sha256'], 'Reused canonical prefix digest differs')
        for source in source_prefix.parent.rglob('*'):
            if source.is_file() and not source.name.endswith('.tmp'):
                copied = ROOT/source.relative_to(MAIN)
                require(copied.exists() and source.read_bytes() == copied.read_bytes(), 'Copied prefix file changed')
                copied_file_count += 1
        world = joint.read(ROOT/prefix['world_path'])
        require(joint.digest(world) == prefix['world_sha256'] == item['world_sha256'], 'Copied world digest differs')
        require((ROOT/prefix['world_path']).read_bytes() == (MAIN/prefix['world_path']).read_bytes(),
                'Copied world bytes differ from source')
        for key, amount in prefix['usage'].items():
            if isinstance(amount, (int, float)) and not isinstance(amount, bool):
                source_usage[key] += amount
        for rel_call in prefix['calls']:
            copied_call, source_call = ROOT/rel_call, MAIN/rel_call
            require(copied_call.read_bytes() == source_call.read_bytes(), 'Reused provider call differs')
            call = joint.read(copied_call)
            require(call['round'] == 0 and call['status'] == 'completed', 'Reused call must be completed planning')
            require(utc(call['finished_at']) <= frozen_at, 'A copied planning call finished after the joint freeze')
            copied_calls.append(call)
            for attempt_path in copied_call.parent.glob('attempt_*.json'):
                source_attempt = MAIN/attempt_path.relative_to(ROOT)
                require(attempt_path.read_bytes() == source_attempt.read_bytes(), 'Reused planning attempt differs')
                attempt = joint.read(attempt_path)
                require(utc(attempt['started_at']) <= frozen_at and utc(attempt['finished_at']) <= frozen_at,
                        'New embedded timestamps found in planning-attempt copy')
                copied_attempts.append(attempt)
        directory = ROOT/'results'/f'{base.prefix_id(joint.SCENARIO, item["seed"], item["objective"])}__joint_guard'
        outcome = joint.read(directory/'result.json')
        require(outcome['status'] == 'completed', 'A joint branch did not complete')
        require(outcome['world_sha256'] == prefix['world_sha256'] and outcome['prefix_sha256'] == joint.digest(prefix),
                'Joint result does not bind reused world/prefix')
        require(outcome['policy'] == outcome['effective_policy'] == joint.POLICY,
                'The joint policy identity must be fixed and public')
        history, expected_events = [], []
        def mediate(agent, action, round_index):
            accepted = proxy.apply_guard(world, agent, action, round_index, joint.POLICY, history)
            history.append({'agent': agent, 'round': round_index, 'action': accepted['accepted_action']})
            expected_events.extend({'agent': agent, 'round': round_index, **event}
                                   for event in accepted['guard_events'])
        for proposal in prefix['proposals']:
            mediate(proposal['agent'], proposal['action'], 0)
        branch_calls = []
        for agent in world['agents']:
            call_path = directory/'calls'/agent/'call.json'
            request_path = call_path.parent/'request.json'
            call, request = joint.read(call_path), joint.read(request_path)
            require(call['status'] == 'completed' and call['round'] == 1 and call['agent'] == agent,
                    'Unexpected continuation status/round/agent')
            require(request['model'] == call['model'] == call['actual_provider_model'] == 'openai/gpt-4.1-mini',
                    'Continuation model identity differs')
            require(request['temperature'] == .7 and request['max_tokens'] == 1500
                    and request['response_format'] == {'type': 'json_object'}, 'Continuation profile differs')
            require(joint.digest(request) == call['input_sha256'], 'Request canonical hash differs')
            require(utc(call['started_at']) >= frozen_at, 'Continuation began before follow-up freeze')
            require(call['provider_response_id'] == call['provider_response']['id'], 'Provider response ID differs')
            require(call['usage'] == call['provider_response'].get('usage', {}), 'Recorded provider usage differs')
            parts = request['messages'][1]['content'].split('\nPUBLIC HOST POLICY ASSIGNMENT:\n')
            require(len(parts) == 2, 'Missing or duplicate public policy assignment')
            user, assignment = json.loads(parts[0]), json.loads(parts[1])
            delivered = proxy.feedback(world, agent, history, joint.POLICY)
            require(user['delivered_history'] == delivered, 'Actual input differs from composed guard delivery')
            require(score_fields(delivered) == 0, 'Registered numeric reward leaked in delivered history')
            require(user['your_private_state'] == world['private'][agent] and user['public'] == world['public'],
                    'Unexpected private/public prompt scope')
            require(user['joint_guard_contract']['identity'] == joint.POLICY
                    and assignment['assigned_policy'] == assignment['effective_policy'] == joint.POLICY,
                    'Fixed joint guard identity not exposed accurately')
            try:
                parsed = proxy.parse_action(call['raw_content'])
                action_valid = True
            except (ValueError, TypeError, KeyError, OverflowError):
                parsed, action_valid = {}, False
            require(call['action_valid'] == action_valid and call['parsed_action'] == parsed,
                    'Stored action validity/schema result differs')
            attempts = sorted(call_path.parent.glob('attempt_*.json'))
            require(1 <= len(attempts) <= 3, 'Attempt count outside the frozen transport bound')
            for attempt_path in attempts:
                attempt = joint.read(attempt_path)
                require(attempt['input_sha256'] == call['input_sha256'], 'Retry payload changed')
                require(utc(attempt['started_at']) >= frozen_at, 'A new attempt predates the freeze')
                new_attempts.append(attempt)
            require(joint.read(call_path.parent/f'attempt_{call["attempt"]}.json') == call,
                    'Final call does not match its preserved attempt')
            for key in ('prompt_tokens', 'completion_tokens', 'total_tokens', 'cost'):
                usage[key] += call.get('usage', {}).get(key, 0)
            new_calls.append(call)
            branch_calls.append(call)
            mediate(agent, parsed, 1)
        require(outcome['actions_by_round'] == {'0': [e for e in history if e['round'] == 0],
                                               '1': [e for e in history if e['round'] == 1]},
                'Recomputed committed actions differ')
        require(outcome['guard_events'] == expected_events, 'Guard event records differ')
        evaluation = proxy.evaluate(world, history, joint.POLICY)
        for key, value in evaluation.items():
            require(outcome[key] == value, 'Recomputed evaluation differs: '+key)
        require(not outcome['missing_agents'], 'A final decision is missing')
        expected_usage = base.usage_of(branch_calls)
        for key, value in expected_usage.items():
            require(math.isclose(value, outcome['usage'][key], abs_tol=1e-10), 'Branch usage sum differs')
        require(len(outcome['host_commit_audit']) == len(history) == 8, 'Eight action commitments expected')
        for index, (event, commit) in enumerate(zip(history, outcome['host_commit_audit']), 1):
            require(commit['ledger']['spent_units'] == index and commit['ledger']['charged_units'] == 1,
                    'Host event accounting differs')
            require(commit['ledger']['committed'] and commit['provenance_authorization']['allowed'],
                    'A commitment lacks authorization/dispatch')
            require(commit['ledger']['payload_sha256'] == joint.digest(event), 'Committed payload hash differs')
        require(outcome['ledger_head'] == outcome['host_commit_audit'][-1]['ledger']['entry_hash'],
                'Ledger head differs from final commitment')
        branches.append({'case_id': outcome['case_id'], 'result_sha256': joint.filehash(directory/'result.json'),
            'world_sha256': outcome['world_sha256'], 'prefix_sha256': outcome['prefix_sha256'],
            'valid_new_actions': sum(call['action_valid'] for call in branch_calls),
            'invalid_new_actions': sum(not call['action_valid'] for call in branch_calls),
            'invalid_reused_planning_actions': sum(not p['action_valid'] for p in prefix['proposals']),
            'invalid_actions_in_evaluation_both_rounds': outcome['invalid_actions'],
            'continuation_usage': expected_usage, 'actual_prompt_delivery_recomputed': True})
    require(len(branches) == 20 and len(new_calls) == 80 and len(copied_calls) == 80,
            'Unexpected branch/new-call/reused-call count')
    new_ids = [call['provider_response_id'] for call in new_calls]
    source_ids = [call['provider_response_id'] for call in copied_calls]
    require(len(set(new_ids)) == 80 and not (set(new_ids) & set(source_ids)), 'Duplicate/reused new provider response ID')
    failed = [a for a in new_attempts if a['status'] != 'completed']
    output = {'status': 'PASSED', 'audited_at': datetime.now(timezone.utc).isoformat(),
        'model_calls_by_audit': 0, 'completed_branches': 20, 'new_continuation_calls': 80,
        'new_planning_calls': 0, 'reused_source_planning_calls': 80,
        'copied_prefix_files_byte_verified': copied_file_count,
        'reused_planning_attempt_files': len(copied_attempts),
        'reused_attempt_embedded_timestamps_all_pre_followup_freeze': True,
        'planning_timestamp_note': 'Copied files may have fresh filesystem mtimes. Original provider attempt timestamps and exact source bytes were checked instead; no copied record represents a new planning call.',
        'unique_new_provider_response_ids': len(set(new_ids)),
        'new_provider_response_ids_disjoint_from_source_prefixes': True,
        'new_requests_canonical_hash_verified': 80, 'actual_delivered_histories_recomputed': 80,
        'numeric_reward_fields_in_delivered_history': 0,
        'model_profile_verified': {'model': 'openai/gpt-4.1-mini', 'temperature': .7,
                                   'max_tokens': 1500, 'response_format': 'json_object'},
        'valid_new_actions': sum(call['action_valid'] for call in new_calls),
        'invalid_new_actions': sum(not call['action_valid'] for call in new_calls),
        'valid_reused_source_actions': sum(call['action_valid'] for call in copied_calls),
        'invalid_reused_source_actions': sum(not call['action_valid'] for call in copied_calls),
        'new_transport_attempts': len(new_attempts), 'failed_transport_attempts': len(failed),
        'failed_attempt_types': dict(Counter(a.get('error_type', a['status']) for a in failed)),
        'new_continuation_usage': dict(usage),
        'source_planning_usage_already_charged_in_main_not_added_again': dict(source_usage),
        'own_and_main_source_freezes_verified': True,
        'followup_freeze_sha256': joint.filehash(ROOT/'PREREGISTRATION_SHA256.json'),
        'reuse_manifest_sha256': joint.filehash(ROOT/'PREFIX_REUSE_MANIFEST.json'),
        'audit_source_sha256': joint.filehash(Path(__file__).resolve()),
        'caveats': ['This is a local reproducibility audit, not independent provider attestation.',
            'Costs are provider-reported amounts in stored usage, not a separately reconciled invoice.',
            'No action_guard-versus-joint outcome comparison or significance claim is made in this audit.',
            'Invalid successful responses remain observed invalid actions; they were not rerun.'],
        'branches': branches}
    joint.write(ROOT/'JOINT_FINAL_AUDIT.json', output)
    print(json.dumps({key: value for key, value in output.items() if key not in ('branches', 'caveats')}))


if __name__ == '__main__':
    main()
