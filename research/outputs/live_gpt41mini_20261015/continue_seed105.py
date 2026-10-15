"""Run the remaining seven prespecified seed-105 pilot cells sequentially."""
import json
import os
from pathlib import Path
import subprocess
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent
OVERLAY = Path('/workspace/colosseum_task_preserving_starter')
env = os.environ.copy()
env.update(OPENAI_API_KEY=env['OPENROUTER_API_KEY'],
           OPENAI_BASE_URL='https://openrouter.ai/api/v1',
           PYTHONPATH=f'{OVERLAY}:/workspace/colosseum',
           MPLCONFIGDIR='/workspace/.cache/matplotlib',
           XDG_CACHE_HOME='/workspace/.cache')
state = {'model': 'openai/gpt-4.1-mini', 'temperature': 0.7,
         'max_tokens': 1500, 'task_seed': 105, 'status': 'running', 'runs': []}

def save():
    state['updated_at'] = datetime.now(timezone.utc).isoformat()
    temp = ROOT / 'seed105_progress.tmp'
    temp.write_text(json.dumps(state, indent=2) + '\n')
    temp.replace(ROOT / 'seed105_progress.json')

save()
for index in [39, 26, 35, 3, 8, 25, 31]:
    row = {'manifest_index': index, 'status': 'running'}
    state['runs'].append(row)
    save()
    args = ['/workspace/colosseum/.venv/bin/python', '-u', '-m', 'kinetic_audit.run',
            '--upstream', '/workspace/colosseum',
            '--manifest', str(OVERLAY / 'configs/pilot_manifest.json'),
            '--index', str(index),
            '--model-config', '/workspace/.setup/model.openrouter.paper-gpt41mini.json',
            '--runtime-gate', str(OVERLAY / 'outputs/runtime_probe_live_20261015_fixed/runtime_gate.json'),
            '--out', str(ROOT), '--timeout-seconds', '1800',
            '--execute-live', '--acknowledge-provider-billing']
    try:
        with (ROOT / f'runner_index{index}.log').open('x') as log:
            completed = subprocess.run(args, env=env, cwd='/workspace/colosseum',
                                       stdout=log, stderr=subprocess.STDOUT, timeout=1860)
        row.update(status='completed' if completed.returncode == 0 else 'failed',
                   returncode=completed.returncode)
    except Exception as exc:
        row.update(status='failed', error_type=type(exc).__name__)
    save()
    if row['status'] != 'completed':
        state['status'] = 'stopped_on_failure'
        save()
        break
else:
    state['status'] = 'completed'
    save()
