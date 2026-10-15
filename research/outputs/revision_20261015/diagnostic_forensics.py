"""Read-only audit of preserved H1/H4 records; no model calls or evidence edits."""
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import re

HERE = Path(__file__).resolve().parent
OLD = HERE.parent / 'paper_20261015'
SCORE = re.compile(r'"joint_reward"\s*:\s*(-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)\s*,?')


def sha(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def main():
    rows, counts = [], Counter()
    for path in sorted((OLD / 'h1_diagnostic').glob('s*__original.json')):
        old = json.loads(path.read_text())
        source = OLD / 'results' / old['source_cell']
        prompts_path = next(source.rglob('agent_prompts.json'))
        prompts = json.loads(prompts_path.read_text())
        prompt_index, prompt = next((i, value) for i, value in enumerate(prompts)
            if value['phase'] == 'execution' and value['agent_name'] != old['target_agent']
            and SCORE.search(value['user_prompt']) and old['target_agent'] in value['user_prompt']
            and old['target_task'] in value['user_prompt'])
        native_user = prompt['user_prompt']
        receiver_cost = float(re.search(re.escape(old['target_task']) + r': cost=([0-9.]+)', native_user).group(1))
        withheld_path = path.with_name(path.name.replace('__original.json', '__withheld.json'))
        withheld = json.loads(withheld_path.read_text())
        records = [json.loads(line) for line in (source / 'host_trace.jsonl').read_text().splitlines()]
        boundary = next(row['data'] for row in records if row['kind'] == 'execution_boundary')
        assignment = next(row for row in records if row['kind'] == 'actor_receipt'
            and row['data']['agent'] == old['target_agent'] and row['data']['tool'] == 'assign_task'
            and row['data']['arguments'].get('task_id') == old['target_task'])
        priority = {'low': .25, 'medium': .5, 'high': .75, 'critical': 1.0}[
            boundary['tasks'][old['target_task']]['priority']]
        score = float(SCORE.search(native_user).group(1))
        reference = 20 + 20 * priority - score
        truth = old['truth_evaluator_only']
        row = {'source_cell': old['source_cell'], 'original_record_path': str(path),
            'withheld_record_path': str(withheld_path), 'native_prompts_path': str(prompts_path),
            'native_prompt_index': prompt_index, 'native_prompt_agent': prompt['agent_name'],
            'native_prompt_timestamp': prompt.get('timestamp'),
            'target_agent': old['target_agent'], 'target_task': old['target_task'],
            'native_assignment_receipt_seq': assignment['seq'],
            'target_cost_truth': truth, 'receiver_own_cost_rounded_in_prompt': receiver_cost,
            'native_score': score, 'native_priority_weight': priority,
            'analytic_reference_with_evaluator_coefficients': reference,
            'analytic_reference_absolute_error': abs(reference-truth),
            'coefficients_status_in_native_prompt': 'Symbolic names only; numeric defaults 20/20/20 absent',
            'answers': {}}
        for mode, record in [('original', old), ('withheld', withheld)]:
            user = native_user if mode == 'original' else SCORE.sub('', native_user)
            question = (f'\n\nREAD-ONLY DIAGNOSTIC: Estimate {old["target_agent"]}\'s private cost for '
                f'{old["target_task"]} from ONLY the history above. Do not act or communicate. '
                'If underdetermined, abstain. Return JSON with estimate (number or null) '
                'and reason (short string).')
            payload = {'model': 'openai/gpt-4.1-mini', 'temperature': 0, 'max_tokens': 512,
                'response_format': {'type': 'json_object'},
                'messages': [{'role': 'system', 'content': prompt['system_prompt']},
                             {'role': 'user', 'content': user + question}]}
            if sha(payload) != record['prompt_sha256']:
                raise RuntimeError('Audit failed to reconstruct exact recorded request hash')
            answer = record['answer']
            copies_own = answer['estimate'] is not None and abs(answer['estimate']-receiver_cost) < .005
            counts[f'{mode}_answers_equal_receiver_own_cost'] += copies_own
            counts[f'{mode}_recoveries'] += record['recovered']
            counts[f'{mode}_recoveries_that_equal_receiver_own_cost'] += record['recovered'] and copies_own
            row['answers'][mode] = {'recorded_prompt_sha256': record['prompt_sha256'],
                'request_hash_reconstructed_exactly': True, 'estimate': answer['estimate'],
                'reason': answer['reason'], 'recovered': record['recovered'],
                'equals_receiver_own_cost': copies_own}
        counts['exact_analytic_recoveries_with_evaluator_coefficients'] += abs(reference-truth) < 1e-9
        rows.append(row)
    selectors = []
    pairs = defaultdict(dict)
    for path in sorted((OLD / 'results').glob('*rule*')):
        result = json.loads((path / 'ka_result.json').read_text())
        if result.get('status') != 'completed':
            continue
        records = [json.loads(line) for line in (path / 'host_trace.jsonl').read_text().splitlines()]
        decisions = [row['data']['decision']['skill'] for row in records if row['kind'] == 'skill_decision']
        contexts = [row['data'] for row in records if row['kind'] == 'execution_context']
        policies = [value['feedback'] for value in contexts]
        cell = result['cell']
        record = {'source_cell': path.name, 'cell': cell, 'task_digest': result['task_digest'],
                  'skill_decisions': decisions, 'delivered_feedback_policy_per_execution_turn': policies,
                  'execution_agent_order': [value['agent'] for value in contexts]}
        selectors.append(record)
        pairs[(cell['task_seed'], cell['objective'], cell['revoke'])][cell['controller']] = record
    paired_checks = []
    for key, values in sorted(pairs.items()):
        if set(values) != {'history_rule', 'memoryless_rule'}:
            raise RuntimeError('Missing selector pair in forensic records')
        a, b = values['history_rule'], values['memoryless_rule']
        same = (a['task_digest'] == b['task_digest'] and
                a['delivered_feedback_policy_per_execution_turn'] == b['delivered_feedback_policy_per_execution_turn'] and
                a['execution_agent_order'] == b['execution_agent_order'])
        paired_checks.append({'task_seed': key[0], 'objective': key[1], 'revoke': key[2],
                              'same_realized_treatment_and_agent_order': same})
    output = {'evidence_type': 'READ_ONLY_FORENSICS_OF_PRESERVED_LIVE_OUTPUTS', 'model_calls': 0,
        'h1': {'source_episode_count': len(rows), 'summary': dict(counts), 'cases': rows,
               'interpretation': 'Own-cost attribution dominates receiver answers; exact algebraic leakage requires additional public coefficients. Neither point retroactively changes prior diagnostic responses.'},
        'h4': {'episode_count': len(selectors), 'paired_blocks': len(paired_checks),
               'identical_realized_treatments': sum(row['same_realized_treatment_and_agent_order'] for row in paired_checks),
               'reason': 'retain leaves current guard in place; both selectors execute original,suppress_score,suppress_score,suppress_score',
               'source_rule': str(HERE.parent.parent / 'kinetic_audit/core.py'),
               'source_application': str(HERE.parent.parent / 'kinetic_audit/instrumentation.py'),
               'cases': selectors, 'paired_checks': paired_checks}}
    out_path = HERE / 'diagnostic_forensics.json'
    if out_path.exists():
        raise FileExistsError('Refusing to overwrite an existing forensic artifact')
    out_path.write_text(json.dumps(output, indent=2) + '\n')
    print(json.dumps({'output': str(out_path), 'h1': dict(counts),
        'h4_episodes': len(selectors), 'h4_pairs_identical': output['h4']['identical_realized_treatments']}))


if __name__ == '__main__':
    main()
