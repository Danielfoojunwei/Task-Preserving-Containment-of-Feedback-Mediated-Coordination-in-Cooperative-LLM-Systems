"""Bounded retry of transport-only missing-header failures, retaining each attempt."""
import asyncio
from datetime import datetime,timezone
import json
from pathlib import Path
import urllib.request

ROOT=Path(__file__).resolve().parent

async def bounded_run(args,env,work,target,logdir,label):
    previous=sum(p.is_dir() for p in (ROOT/'preserved_attempts').glob(f'*/**/{target.name}'))
    for attempt in range(previous+1,4):
        stamp=datetime.now(timezone.utc).strftime('%H%M%S%f')
        logfile=logdir/f'{label}__{stamp}.log'
        with logfile.open('x') as log:
            proc=await asyncio.create_subprocess_exec(*args,env=env,cwd=work,stdout=log,stderr=log)
            code=await asyncio.wait_for(proc.wait(),timeout=1860)
        if code==0:return code
        text=logfile.read_text()
        if 'Missing Authentication header' not in text or attempt>=3:return code
        req=urllib.request.Request('https://openrouter.ai/api/v1/key',
               headers={'Authorization':'Bearer '+env['OPENROUTER_API_KEY']})
        try:
            status=await asyncio.to_thread(lambda:urllib.request.urlopen(req,timeout=30).status)
        except Exception:return code
        if status!=200:return code
        destination=ROOT/'preserved_attempts'/stamp/target.parent.name
        destination.mkdir(parents=True)
        target.rename(destination/target.name)
        (destination/'recovery.json').write_text(json.dumps({'reason':'Missing Authentication header',
             'auth_check_http':status,'attempt':attempt,'log':str(logfile),
             'policy':'Maximum three total attempts per cell; no outcome-dependent reruns'},indent=2)+'\n')
    return 1
