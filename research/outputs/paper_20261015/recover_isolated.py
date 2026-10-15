"""One explicitly scheduled final isolated attempt for retained auth-only failures."""
from datetime import datetime,timezone
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parent
BASE=Path('/workspace/colosseum_task_preserving_starter')
PY='/workspace/colosseum/.venv/bin/python'
sys.path[:0]=[str(ROOT),str(BASE)]
from extension_h5 import design
from kinetic_audit.core import Cell
ENV=os.environ.copy();ENV.update(OPENAI_API_KEY=ENV['OPENROUTER_API_KEY'],
    OPENAI_BASE_URL='https://openrouter.ai/api/v1',PYTHONPATH=f'{BASE}:/workspace/colosseum',
    MPLCONFIGDIR='/workspace/.cache/matplotlib',XDG_CACHE_HOME='/workspace/.cache')
STATE={'status':'running','runs':{}}
def save():
    temp=ROOT/'recovery_progress.tmp';temp.write_text(json.dumps(STATE,indent=2)+'\n');temp.replace(ROOT/'recovery_progress.json')

def main():
    save();jobs=[]
    manifests=[ROOT/'development_peer_manifest.json',BASE/'configs/peer_ablation_manifest.json']
    for manifest in manifests:
        for index,row in enumerate(json.loads(manifest.read_text())['cells']):
            cell=Cell(**row);target=ROOT/'results'/cell.key;p=target/'ka_result.json'
            if p.exists() and json.loads(p.read_text()).get('status')!='completed':
                if 'Missing Authentication header' not in json.loads(p.read_text()).get('error',''):
                    raise RuntimeError('Recovery is restricted to missing-header infrastructure errors')
                args=[PY,'-u','-m','kinetic_audit.run','--upstream','/workspace/colosseum',
                      '--manifest',str(manifest),'--index',str(index),'--model-config',str(ROOT/'model.json'),
                      '--runtime-gate',str(BASE/'outputs/runtime_probe_live_20261015_fixed/runtime_gate.json'),
                      '--out',str(ROOT/'results'),'--timeout-seconds','1800','--execute-live','--acknowledge-provider-billing']
                jobs.append((target,args))
    for index,row in enumerate(design()):
        c=Cell(row['seed'],row['objective'],True,row['feedback'],split='heldout')
        target=ROOT/'h5_extension'/f'{c.key}__public{int(row["public_enabled"])}'
        p=target/'extension_result.json'
        if p.exists() and json.loads(p.read_text()).get('status')!='completed':
            if 'Missing Authentication header' not in json.loads(p.read_text()).get('error',''):
                raise RuntimeError('Recovery is restricted to missing-header infrastructure errors')
            jobs.append((target,[PY,'-u',str(ROOT/'extension_h5.py'),'--index',str(index)]))
    if len(jobs)>5:raise RuntimeError('Expected at most five retained failed cells')
    STATE['planned']=len(jobs);save()
    for target,args in jobs:
        stamp=datetime.now(timezone.utc).strftime('%H%M%S%f')
        dest=ROOT/'preserved_attempts'/stamp/target.parent.name;dest.mkdir(parents=True)
        target.rename(dest/target.name)
        work=ROOT/'isolated_work'/target.name;work.mkdir(parents=True,exist_ok=True)
        STATE['runs'][target.name]='running';save()
        with (ROOT/f'isolated_{target.name}.log').open('x') as log:
            completed=subprocess.run(args,env=ENV,cwd=work,stdout=log,stderr=log,timeout=1860)
        STATE['runs'][target.name]='completed' if completed.returncode==0 else 'failed'
        save()
    STATE['status']='finished';save()

if __name__=='__main__':
    try:main()
    except Exception as exc:STATE.update(status='failed',error=str(exc));save();raise
