"""Bounded follow-up scheduler, no retries and no outcome-based tuning."""
import asyncio
from datetime import datetime,timezone
import json
import os
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parent
PY='/workspace/colosseum/.venv/bin/python'
ENV=os.environ.copy()
ENV.update(OPENAI_API_KEY=ENV['OPENROUTER_API_KEY'],OPENAI_BASE_URL='https://openrouter.ai/api/v1',
           MPLCONFIGDIR='/workspace/.cache/matplotlib',XDG_CACHE_HOME='/workspace/.cache')
sys.path.insert(0,str(ROOT))
from extension_h5 import design
from auth_recovery import bounded_run
STATE={'status':'running','h1':'waiting_for_pilot','h5':{}}
STOP=asyncio.Event()

def save():
    STATE['updated_at']=datetime.now(timezone.utc).isoformat()
    tmp=ROOT/'followup_progress.tmp';tmp.write_text(json.dumps(STATE,indent=2)+'\n');tmp.replace(ROOT/'followup_progress.json')

async def h1():
    design_path=ROOT/'h1_diagnostic'/'design.json'
    if design_path.exists():
        expected=json.loads(design_path.read_text())['planned_calls']
        found=list((ROOT/'h1_diagnostic').glob('*__*.json'))
        if len(found)==expected:
            STATE['h1']='completed';save();return
    while True:
        state=json.loads((ROOT/'progress.json').read_text())
        if state.get('stages',{}).get('pilot_and_peer_ablation',{}).get('status')=='completed': break
        if state['status'] not in ['running','completed_available_manifests']:
            STATE['h1']='blocked_by_main_failure';save();return
        await asyncio.sleep(5)
    STATE['h1']='running';save()
    with (ROOT/f'h1_{datetime.now(timezone.utc).strftime("%H%M%S%f")}.log').open('x') as log:
        p=await asyncio.create_subprocess_exec(PY,str(ROOT/'diagnostic_h1.py'),env=ENV,stdout=log,stderr=log)
        STATE['h1']='completed' if await p.wait()==0 else 'failed'
    save()

async def cell(index,row,sem):
    from kinetic_audit.core import Cell
    c=Cell(row['seed'],row['objective'],True,row['feedback'],split='heldout')
    name=f'{c.key}__public{int(row["public_enabled"])}'
    async with sem:
        if STOP.is_set(): return
        existing=ROOT/'h5_extension'/name/'extension_result.json'
        if existing.exists():
            d=json.loads(existing.read_text())
            if d['status']!='completed':
                if 'Missing Authentication header' in d.get('error',''):
                    STATE['h5'][name]='failed_auth_preserved';save();return
                raise RuntimeError('Failed extension attempt exists')
            STATE['h5'][name]='reused';save();return
        if (ROOT/'h5_extension'/name).exists(): raise RuntimeError('Unfinished extension attempt exists')
        work=ROOT/'h5_work'/str(index);work.mkdir(parents=True,exist_ok=True)
        STATE['h5'][name]='running';save()
        try:
            code=await bounded_run([PY,'-u',str(ROOT/'extension_h5.py'),'--index',str(index)],
                       ENV,work,ROOT/'h5_extension'/name,ROOT/'h5_logs',str(index))
            if code: raise RuntimeError(f'Runner exit {code}')
            STATE['h5'][name]='completed'
        except Exception as exc:
            STATE['h5'][name]='failed';STATE['error']=str(exc)
            detail=json.loads(existing.read_text()) if existing.exists() else {}
            if 'Missing Authentication header' not in detail.get('error',''): STOP.set()
        save()

async def main():
    (ROOT/'h5_logs').mkdir(exist_ok=True);save()
    sem=asyncio.Semaphore(2)
    await asyncio.gather(h1(),*(cell(i,r,sem) for i,r in enumerate(design())))
    STATE['status']='stopped_on_failure' if STOP.is_set() or STATE['h1']!='completed' else 'completed';save()

if __name__=='__main__':
    try: asyncio.run(main())
    except Exception as exc: STATE.update(status='failed',error=str(exc));save();raise
