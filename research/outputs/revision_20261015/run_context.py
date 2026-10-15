"""Bounded execution of a frozen shared-prefix factorial design."""
import asyncio
from datetime import datetime,timezone
import hashlib
import itertools
import json
import os
from pathlib import Path
import random
import sys

ROOT=Path(__file__).resolve().parent
PY='/workspace/colosseum/.venv/bin/python'
ENV=os.environ.copy()
ENV.update(OPENAI_API_KEY=ENV['OPENROUTER_API_KEY'],
           OPENAI_BASE_URL='https://openrouter.ai/api/v1',
           MPLCONFIGDIR='/workspace/.cache/matplotlib',XDG_CACHE_HOME='/workspace/.cache')
STATE={'status':'running','stage':'prefixes','prefixes':{},'branches':{},'concurrency':4}

def save():
    STATE['updated_at']=datetime.now(timezone.utc).isoformat()
    temp=ROOT/'context_progress.tmp';temp.write_text(json.dumps(STATE,indent=2)+'\n');temp.replace(ROOT/'context_progress.json')

def manifest():
    path=ROOT/'context_manifest.json'
    if path.exists():return json.loads(path.read_text())
    prefixes=[{'seed':s,'objective':z} for s,z in itertools.product(range(3001,3021),['coalition','cooperative'])]
    branches=[{**p,'history':h,'permission':v} for p in prefixes for h,v in itertools.product([0,1],repeat=2)]
    rng=random.Random(20261015);rng.shuffle(prefixes);rng.shuffle(branches)
    data={'seeds':list(range(3001,3021)),'prefixes':prefixes,'branches':branches,
          'randomization_seed':20261015,'preregistration_sha256':hashlib.sha256((ROOT/'PREREGISTRATION.md').read_bytes()).hexdigest(),
          'adapter_sha256':hashlib.sha256((ROOT/'context_experiment.py').read_bytes()).hexdigest(),
          'source_model':json.loads((ROOT.parent/'paper_20261015/model.json').read_text())}
    data['manifest_sha256']=hashlib.sha256(json.dumps(data,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    path.write_text(json.dumps(data,indent=2)+'\n');return data

async def one(row,prepare,sem):
    key=f's{row["seed"]}__{row["objective"]}'
    branchkey=key if prepare else key+f'__history{row["history"]}__permission{row["permission"]}'
    target=ROOT/('planning' if prepare else 'results')/branchkey
    prefix=ROOT/'prefixes'/f'{key}.json'
    table=STATE['prefixes' if prepare else 'branches']
    async with sem:
        if (target/'ka_result.json').exists():
            d=json.loads((target/'ka_result.json').read_text())
            table[branchkey]='reused' if d['status'] in ['completed','PLANNING_PREFIX_PREPARED'] else 'failed_preserved'
            save();return
        if not prepare and not prefix.exists():table[branchkey]='blocked_missing_prefix';save();return
        if target.exists():raise RuntimeError('Incomplete prior directory; preserve and review before recovery')
        args=[PY,'-u',str(ROOT/'context_experiment.py'),'--seed',str(row['seed']),'--objective',row['objective'],
              '--out',str(target),'--prefix',str(prefix)]
        if prepare:args+=['--prepare-prefix']
        else:args+=['--history',str(row['history']),'--permission',str(row['permission'])]
        work=ROOT/'work'/branchkey;work.mkdir(parents=True,exist_ok=True)
        for attempt in range(1,4):
            table[branchkey]='running';save()
            logpath=ROOT/'logs'/f'{branchkey}__attempt{attempt}.log'
            with logpath.open('x') as log:
                proc=await asyncio.create_subprocess_exec(*args,env=ENV,cwd=work,stdout=log,stderr=log)
                try:code=await asyncio.wait_for(proc.wait(),timeout=1860)
                except asyncio.TimeoutError:
                    proc.terminate();await proc.wait();code=124
            if code==0:
                d=json.loads((target/'ka_result.json').read_text())
                expected='PLANNING_PREFIX_PREPARED' if prepare else 'completed'
                if d['status']!=expected:raise RuntimeError('Unexpected successful runner status')
                table[branchkey]='completed';save();return
            text=logpath.read_text()
            transport=any(v in text for v in ['Missing Authentication header','RateLimitError','APITimeoutError','APIConnectionError']) or code==124
            if not transport or attempt==3 or (prepare and prefix.exists()):
                table[branchkey]='failed';save();return
            dest=ROOT/'preserved_attempts'/'context'/branchkey/f'attempt{attempt}'
            dest.parent.mkdir(parents=True,exist_ok=True);target.rename(dest)
        save()

async def main():
    if not (ROOT/'PREREGISTRATION_SHA256.json').exists():raise RuntimeError('Preregistration not frozen')
    design=manifest()
    if design['adapter_sha256']!=hashlib.sha256((ROOT/'context_experiment.py').read_bytes()).hexdigest():
        raise RuntimeError('Adapter changed after freeze')
    for p in ['prefixes','planning','results','logs','work']:(ROOT/p).mkdir(exist_ok=True)
    save();sem=asyncio.Semaphore(4)
    await asyncio.gather(*(one(p,True,sem) for p in design['prefixes']))
    STATE['stage']='execution';save()
    await asyncio.gather(*(one(b,False,sem) for b in design['branches']))
    STATE['status']='completed' if all(s in ['completed','reused'] for s in [*STATE['prefixes'].values(),*STATE['branches'].values()]) else 'finished_with_failures'
    save()

if __name__=='__main__':
    try:asyncio.run(main())
    except Exception as exc:STATE.update(status='failed',error=str(exc));save();raise
