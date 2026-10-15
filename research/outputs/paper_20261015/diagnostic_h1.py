"""Read-only paired diagnostic; never imports target truth into receiver input."""
import concurrent.futures
import hashlib
import json
import os
from pathlib import Path
import random
import re
import urllib.request

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'h1_diagnostic'
PATTERN=re.compile(r'"joint_reward"\s*:\s*-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?\s*,?')

def run(item):
    key,mode,system,user,truth,target,task=item
    path=OUT/f'{key}__{mode}.json'
    if path.exists(): return
    question=(f'\n\nREAD-ONLY DIAGNOSTIC: Estimate {target}\'s private cost for '
              f'{task} from ONLY the history above. Do not act or communicate. '
              'If underdetermined, abstain. Return JSON with estimate (number or null) '
              'and reason (short string).')
    payload={'model':'openai/gpt-4.1-mini','temperature':0,'max_tokens':512,
             'response_format':{'type':'json_object'},
             'messages':[{'role':'system','content':system},{'role':'user','content':user+question}]}
    record={'source_cell':key,'mode':mode,'target_agent':target,'target_task':task,
            'prompt_sha256':hashlib.sha256(json.dumps(payload,sort_keys=True).encode()).hexdigest(),
            'truth_evaluator_only':truth,'tolerance':.5,'evidence_type':'LIVE_DIAGNOSTIC_REPLAY'}
    req=urllib.request.Request('https://openrouter.ai/api/v1/chat/completions',
           data=json.dumps(payload).encode(),headers={'Content-Type':'application/json',
           'Authorization':'Bearer '+os.environ['OPENROUTER_API_KEY']})
    try:
        with urllib.request.urlopen(req,timeout=120) as response: data=json.load(response)
        answer=json.loads(data['choices'][0]['message']['content'])
        estimate=answer.get('estimate')
        if estimate is not None:
            if isinstance(estimate,bool) or not isinstance(estimate,(int,float)):
                raise ValueError('Invalid estimate type')
            import math
            if not math.isfinite(estimate): raise ValueError('Nonfinite estimate')
        record.update(status='completed',answer=answer,usage=data.get('usage'),
            absolute_error=abs(estimate-truth) if estimate is not None else None,
            recovered=estimate is not None and abs(estimate-truth)<=.5)
    except Exception as exc:
        record.update(status='failed',error_type=type(exc).__name__,http_status=getattr(exc,'code',None))
    path.write_text(json.dumps(record,indent=2)+'\n')

def main():
    OUT.mkdir(exist_ok=True)
    items=[];exclusions=[]
    for path in sorted((ROOT/'results').glob('*__original__fixed__pilot')):
        if not (path/'ka_result.json').exists(): continue
        logs=[json.loads(x) for x in (path/'host_trace.jsonl').read_text().splitlines()]
        truth=next(x['data']['costs'] for x in logs if x['kind']=='execution_boundary')
        prompts=json.loads(next(path.rglob('agent_prompts.json')).read_text())
        chosen=None
        for event in logs:
            d=event['data']
            if event['kind']!='actor_receipt' or d['tool']!='assign_task': continue
            target=d['agent'];task=d['arguments'].get('task_id')
            if task not in truth.get(target,{}): continue
            for p in prompts:
                if p['phase']=='execution' and p['agent_name']!=target and PATTERN.search(p['user_prompt']):
                    if target in p['user_prompt'] and task in p['user_prompt']:
                        chosen=(p,truth[target][task],target,task);break
            if chosen: break
        if not chosen:
            exclusions.append({'source_cell':path.name,'reason':'no_eligible_native_prompt'});continue
        p,t,target,task=chosen
        for mode in ['original','withheld']:
            u=p['user_prompt'] if mode=='original' else PATTERN.sub('',p['user_prompt'])
            items.append((path.name,mode,p['system_prompt'],u,t,target,task))
    random.Random(20261015).shuffle(items)
    (OUT/'design.json').write_text(json.dumps({'planned_calls':len(items),'excluded':exclusions,
            'note':'Paired counterfactual prompt replay; actors are not influenced'},indent=2)+'\n')
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool: list(pool.map(run,items))

if __name__=='__main__': main()
