"""Run all frozen diagnostic inputs with two workers and bounded transport recovery."""
import concurrent.futures
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
import diagnostic_identifiability as diagnostic
OUT=ROOT/'h1_identifiability'
STATE={'status':'running','planned':80,'results':{}}

def save():
    STATE['updated_at']=datetime.now(timezone.utc).isoformat()
    tmp=ROOT/'diagnostic_progress.tmp';tmp.write_text(json.dumps(STATE,indent=2)+'\n');tmp.replace(ROOT/'diagnostic_progress.json')

def worker(index):
    case=json.loads((OUT/'design.json').read_text())['cases'][index]
    answer=OUT/'answers'/f'{case["case_id"]}.json'
    if answer.exists(): return json.loads(answer.read_text())
    for attempt in range(1,4):
        diagnostic.run_index(OUT,index)
        record=json.loads(answer.read_text())
        if record['status']=='completed': return record
        transport=record.get('http_status') in [401,408,429,500,502,503,504] or record.get('error_type') in ['TimeoutError','URLError']
        if not transport or attempt==3:return record
        dest=ROOT/'preserved_attempts'/'diagnostic'/f'attempt{attempt}'
        dest.mkdir(parents=True,exist_ok=True)
        answer.rename(dest/answer.name)

def main():
    freeze=ROOT/'PREREGISTRATION_SHA256.json'
    if not freeze.exists():raise RuntimeError('Freeze preregistration before live calls')
    save()
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        futures=[pool.submit(worker,i) for i in range(80)]
        for future in concurrent.futures.as_completed(futures):
            d=future.result();STATE['results'][d['case_id']]=d['status'];save()
    STATE['status']='completed' if all(v=='completed' for v in STATE['results'].values()) else 'finished_with_failures';save()

if __name__=='__main__':
    try:main()
    except Exception as exc:STATE.update(status='failed',error=str(exc));save();raise
