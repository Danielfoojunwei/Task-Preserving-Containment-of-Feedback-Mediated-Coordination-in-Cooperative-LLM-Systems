"""Real-runtime intervention checks using canned agents, with zero model calls."""
import asyncio
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
import context_experiment as cx

UPSTREAM = Path('/workspace/colosseum')
sys.path.insert(0, str(UPSTREAM))
MODEL = {'provider': 'openai', 'openai': {'model': 'openai/gpt-4.1-mini',
                                       'params': {'max_tokens': 1500, 'temperature': .7}}}


class CannedAgent:
    calls = []

    def __init__(self, client, name, *args, **kwargs):
        self.name = name

    async def generate_response(self, *, agent_name, agent_context,
                                blackboard_context, communication_protocol,
                                prompts, phase, iteration, round_num):
        self.calls.append((phase, agent_name))
        # Exercise native prompt logging and exactly the actual delivered views.
        prompts.get_system_prompt()
        prompts.get_user_prompt(agent_name, agent_context, blackboard_context)
        board_ids = communication_protocol.megaboard.get_agent_blackboards(agent_name)
        for board_id in board_ids:
            await communication_protocol.blackboard_handle_tool_call(
                'post_message', agent_name,
                {'blackboard_id': board_id,
                 'message': f'CANNED_{phase}_{agent_name}_{round_num}'},
                phase=phase, iteration=iteration)
        if phase == 'execution':
            env = communication_protocol.environment
            taken = set(env.assignment.values())
            choice = min((t for t in env.tasks if t not in taken),
                         key=lambda t: env.costs[agent_name][t])
            await communication_protocol.environment_handle_tool_call(
                'assign_task', agent_name, {'task_id': choice},
                phase=phase, iteration=iteration)
        return {'response': 'canned no-model fixture', 'usage': {
            'prompt_tokens': 0, 'completion_tokens': 0, 'total_tokens': 0},
            'model': 'CANNED_NO_MODEL_CALLS', 'tools_executed': 1,
            'conversation_steps': 1}


def runtime():
    value = cx.load_runner(UPSTREAM)
    value.BaseAgent = CannedAgent
    value.get_client_instance = lambda *args, **kwargs: None
    return value


def test_shared_prefix_and_independent_history_posting(tmp_path):
    prefix = tmp_path / 'prefix.json'
    CannedAgent.calls = []
    async def run():
        prep = await cx.execute_context(
            upstream=UPSTREAM, seed=3001, objective='coalition',
            history_visible=True, permission=True, out=tmp_path / 'prepare',
            prefix_path=prefix, model_config=MODEL, prepare=True, runtime=runtime())
        assert prep['status'] == 'PLANNING_PREFIX_PREPARED'
        assert len(CannedAgent.calls) == 8
        assert all(phase == 'planning' for phase, _ in CannedAgent.calls)
        results = []
        for history in (False, True):
            for permission in (False, True):
                result = await cx.execute_context(
                    upstream=UPSTREAM, seed=3001, objective='coalition',
                    history_visible=history, permission=permission,
                    out=tmp_path / f'h{int(history)}p{int(permission)}',
                    prefix_path=prefix, model_config=MODEL, runtime=runtime())
                assert result['status'] == 'completed'
                fidelity = result['context_fidelity']
                assert fidelity['native_prompts_with_policy_notice'] == 4
                assert fidelity['historical_view_correct']
                assert fidelity['planning_model_calls_this_run'] == 0
                assert (fidelity['private_planning_events_visible'] > 0) == history
                assert (fidelity['private_planning_events_hidden'] > 0) != history
                assert fidelity['denied_private_posts'] == (0 if permission else 2)
                assert fidelity['successful_private_posts'] == (2 if permission else 0)
                assert result['unique_task_count'] == 4
                assert result['duplicate_claims'] == 0
                assert result['actual_usage']['total_tokens'] == 0
                # Historical planning records remain stored even when not read.
                assert fidelity['private_planning_events_visible'] + fidelity['private_planning_events_hidden'] == 8
                results.append(result)
        assert len(CannedAgent.calls) == 24  # 8 shared planning + 4 * 4 execution
        assert len({r['prefix_sha256'] for r in results}) == 1
        assert len({r['task_digest'] for r in results}) == 1
        assert len({r['roles_digest'] for r in results}) == 1
        for branch in tmp_path.glob('h*p*'):
            records = [json.loads(s) for s in (branch / 'host_trace.jsonl').read_text().splitlines()]
            assert cx.Ledger.verify(records, (branch / 'local_trace_head.txt').read_text().strip())
            # New private execution records stay readable with history hidden.
            if branch.name == 'h0p1':
                delivered = [e for r in records if r['kind'] == 'board_read'
                             for e in r['data']['delivered_events']]
                assert any('CANNED_execution' in e.get('payload', {}).get('content', '')
                           and e['blackboard_id'] == 1 for e in delivered)
    asyncio.run(run())


def test_tampered_prefix_rejected(tmp_path):
    path = tmp_path / 'prefix.json'
    path.write_text(json.dumps({'prefix_sha256': '0' * 64, 'seed': 3001}))
    try:
        cx.read_prefix(path, 3001, 'coalition', MODEL)
    except ValueError as exc:
        assert 'digest' in str(exc)
    else:
        raise AssertionError('Tampered shared prefix was accepted')


if __name__ == '__main__':
    from tempfile import TemporaryDirectory
    with TemporaryDirectory(dir='/tmp', prefix='context-intervention-test-') as d:
        root = Path(d)
        test_shared_prefix_and_independent_history_posting(root)
        test_tampered_prefix_rejected(root)
    print('2 checks passed; real pinned runtime; canned actors; zero model calls')
