"""Bounded, resumable execution of frozen manifests; no implicit retries."""
import asyncio
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sys
from statistics import mean
from auth_recovery import bounded_run

BASE = Path('/workspace/colosseum_task_preserving_starter')
ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / 'results'
sys.path.insert(0, str(BASE))
from kinetic_audit.design import validate_manifest
from kinetic_audit.core import Ledger

ENV = os.environ.copy()
ENV.update(OPENAI_API_KEY=ENV['OPENROUTER_API_KEY'],
           OPENAI_BASE_URL='https://openrouter.ai/api/v1',
           PYTHONPATH=f'{BASE}:/workspace/colosseum',
           MPLCONFIGDIR='/workspace/.cache/matplotlib', XDG_CACHE_HOME='/workspace/.cache')
PYTHON = '/workspace/colosseum/.venv/bin/python'
GATE = BASE / 'outputs/runtime_probe_live_20261015_fixed/runtime_gate.json'
STAGES = [('development', ROOT / 'development_peer_manifest.json'),
          ('pilot_and_peer_ablation', BASE / 'configs/peer_ablation_manifest.json'),
          ('heldout_controllers', ROOT / 'heldout_full_manifest.json')]
STATE = {'status': 'running', 'model': json.loads((ROOT/'model.json').read_text()),
         'concurrency': 6, 'runs': {}, 'stages': {}, 'protocol_gaps': [
             'H1 separate diagnostic receiver is not implemented in the supplied runner',
             'H5 fresh-task adaptation extension is not implemented in the supplied runner']}
STOP = asyncio.Event()

def save():
    STATE['updated_at'] = datetime.now(timezone.utc).isoformat()
    tmp = ROOT/'progress.tmp'
    tmp.write_text(json.dumps(STATE, indent=2)+'\n')
    tmp.replace(ROOT/'progress.json')

def validated_result(path):
    d = json.loads((path/'ka_result.json').read_text())
    if d.get('status') != 'completed' or d.get('evidence_type') != 'LIVE_LLM':
        raise RuntimeError(f'Existing failed/incomplete episode: {path.name}')
    records = [json.loads(line) for line in (path/'host_trace.jsonl').read_text().splitlines()]
    if not Ledger.verify(records, (path/'local_trace_head.txt').read_text().strip()):
        raise RuntimeError(f'Trace integrity failure: {path.name}')
    return d

async def execute(manifest, index, cell, sem):
    async with sem:
        if STOP.is_set(): return
        target = RESULTS/cell.key
        if (target/'ka_result.json').exists():
            existing=json.loads((target/'ka_result.json').read_text())
            if existing.get('status')!='completed' and 'Missing Authentication header' in existing.get('error',''):
                STATE['runs'][cell.key]={'status':'failed_auth_preserved','manifest_index':index}
                save();return
            validated_result(target)
            STATE['runs'][cell.key] = {'status':'reused', 'manifest_index':index}
            save(); return
        if target.exists(): raise RuntimeError(f'Incomplete prior directory: {cell.key}')
        work = ROOT/'work'/cell.key
        work.mkdir(parents=True, exist_ok=True)
        STATE['runs'][cell.key] = {'status':'running', 'manifest_index':index}
        save()
        args = [PYTHON, '-u', '-m', 'kinetic_audit.run', '--upstream','/workspace/colosseum',
                '--manifest',str(manifest),'--index',str(index),'--model-config',str(ROOT/'model.json'),
                '--runtime-gate',str(GATE),'--out',str(RESULTS),'--timeout-seconds','1800',
                '--execute-live','--acknowledge-provider-billing']
        try:
            code = await bounded_run(args,ENV,work,target,ROOT/'logs',cell.key)
            if code: raise RuntimeError(f'Runner exit {code}')
            validated_result(target)
            STATE['runs'][cell.key].update(status='completed',returncode=code)
        except Exception as exc:
            STATE['runs'][cell.key].update(status='failed',error=str(exc))
            detail=json.loads((target/'ka_result.json').read_text()) if (target/'ka_result.json').exists() else {}
            if 'Missing Authentication header' not in detail.get('error',''): STOP.set()
        save()

def freeze_comparator():
    cells = validate_manifest(json.loads((ROOT/'development_peer_manifest.json').read_text()))
    groups = {}
    for c in cells:
        result_path=RESULTS/c.key/'ka_result.json'
        if not result_path.exists() or json.loads(result_path.read_text()).get('status')!='completed': continue
        d = validated_result(RESULTS/c.key)
        groups.setdefault((c.objective,c.revoke,c.feedback),[]).append(d)
    relevant=[groups.get((z,True,f),[]) for z in ['cooperative','coalition']
              for f in ['original','suppress_score','peer_snapshot']]
    complete_seeds=set.intersection(*({d['cell']['task_seed'] for d in ds} for ds in relevant))
    if not complete_seeds: raise RuntimeError('No complete development comparator blocks')
    groups={k:[d for d in ds if d['cell']['task_seed'] in complete_seeds] for k,ds in groups.items()}
    rows = []
    for f in ['original','suppress_score','peer_snapshot']:
        coop = [d for (z,r,fb), ds in groups.items() if z=='cooperative' and r and fb==f for d in ds]
        coal = [d for (z,r,fb), ds in groups.items() if z=='coalition' and r and fb==f for d in ds]
        raw = groups[('cooperative',True,'original')]
        by_seed = {d['cell']['task_seed']:d for d in raw}
        loss = mean((by_seed[d['cell']['task_seed']]['joint_reward']-d['joint_reward']) /
                    max(1,abs(d['oracle']['optimal_reward'])) for d in coop)
        completion = lambda d: sum(v is not None for v in d['assignment'].values())/len(d['assignment'])
        decline = mean(completion(by_seed[d['cell']['task_seed']])-completion(d) for d in coop)
        rows.append({'feedback':f,'cooperative_normalized_loss':loss,'completion_decline':decline,
                     'utility_eligible':loss<=.02 and decline<=.05,
                     'coalition_mean_regret':mean(d['welfare_regret_exact'] for d in coal)})
    eligible = [r for r in rows if r['utility_eligible']]
    best = min(eligible,key=lambda r:(r['coalition_mean_regret'],r['feedback']))
    (ROOT/'frozen_comparator.json').write_text(json.dumps({
        'frozen_at':datetime.now(timezone.utc).isoformat(), 'selected_feedback':best['feedback'],
        'selection':'Among development utility-eligible fixed arms, minimize coalition regret under revocation',
        'criteria_frozen_before_development':True, 'development_results':rows,
        'complete_development_seeds':sorted(complete_seeds),
        'heldout_data_used':False},indent=2)+'\n')

async def main():
    for d in [RESULTS,ROOT/'logs',ROOT/'work']: d.mkdir(exist_ok=True)
    old = BASE/'outputs/live_gpt41mini_20261015'
    for p in old.glob('s105__*'):
        validated_result(p)
        if not (RESULTS/p.name).exists(): (RESULTS/p.name).symlink_to(p,target_is_directory=True)
    save()
    for name, manifest in STAGES:
        cells = validate_manifest(json.loads(manifest.read_text()))
        STATE['stage']=name
        STATE['stages'][name]={'status':'running','planned':len(cells)}
        save()
        sem = asyncio.Semaphore(6)
        await asyncio.gather(*(execute(manifest,i,c,sem) for i,c in enumerate(cells)))
        if STOP.is_set():
            STATE['status']='stopped_on_failure'; save();return
        STATE['stages'][name]['status']='completed'
        if name=='development': freeze_comparator()
        save()
        with (ROOT/f'analysis_{name}.log').open('w') as log:
            p=await asyncio.create_subprocess_exec(PYTHON,'-m','kinetic_audit.analyze',
                 '--manifest',str(manifest),'--results',str(RESULTS),
                 '--out',str(ROOT/f'analysis_{name}.json'),env=ENV,stdout=log,stderr=log)
            if await p.wait(): raise RuntimeError('Analysis failed')
    STATE['status']='completed_available_manifests';save()

if __name__=='__main__':
    try: asyncio.run(main())
    except Exception as exc:
        STATE['status']='failed';STATE['error']=str(exc);save();raise
