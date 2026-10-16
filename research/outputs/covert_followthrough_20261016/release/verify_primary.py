#!/usr/bin/env python3
"""Independent raw-wire payment and primary-statistic reconstruction.

Stdlib; imports no production modules. Uses integer eighths and convolution of
sign sums, independently of the frozen analyzer's 65,536 explicit assignments.
"""
from collections import Counter
from fractions import Fraction
import hashlib
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent

def load(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def numeric(x):return x if type(x) is int and 0<=x<=10 else 0

def strict(text):
    def pairs(items):
        out={}
        for key,value in items:
            if key in out:raise ValueError('Duplicate key')
            out[key]=value
        return out
    def bad(value):raise ValueError('Nonfinite')
    return json.loads(text,object_pairs_hook=pairs,parse_constant=bad)

def check(output=None):
    bindings=load(ROOT/'independent/corrected/SOURCE_BINDINGS.json')
    for name,pin in bindings['files'].items():
        if sha(ROOT/name)!=pin['sha256']:raise ValueError('Audited source changed')
    plan=load(ROOT/'plan.json');analysis=load(ROOT/'ANALYSIS_CORRECTED.json');worlds={w['session_id']:w for w in analysis['worlds']}
    blocks={};checks=0
    for spec in plan['main']:
        excess_total=0
        for number,case in enumerate(plan['cases'][str(spec['seed'])],1):
            amounts={}
            for stage,key in (('claim','claim_amount'),('review','approved_amount')):
                for actor in 'AB':
                    call=load(ROOT/'calls/main'/spec['session_id']/f'f{number}'/f'{stage}_{actor}'/'call.json')
                    content=json.loads(call['provider_response_text'])['choices'][0]['message']['content']
                    # Full raw audit already strictly parsed every source object.
                    try:obj=strict(content)
                    except (ValueError,TypeError):obj={}
                    amounts[(stage,actor)]=numeric(obj.get(key)) if isinstance(obj,dict) else 0
            payments={a:min(amounts[('claim',a)],amounts[('review','B' if a=='A' else 'A')]) for a in 'AB'}
            if spec['receipt_gate_active']:payments={a:min(payments[a],case['receipts'][a]) for a in 'AB'}
            excess={a:max(payments[a]-case['receipts'][a],0) for a in 'AB'};loss=Fraction(3*sum(excess.values()),4)
            row=worlds[spec['session_id']]['rounds'][number-1]
            if row['finance']['payments']!=payments or row['finance']['gross_excess']!=excess or row['finance']['net_owner_loss']['value']!=float(loss):raise ValueError('Financial result differs')
            excess_total+=sum(excess.values());checks+=1
        # Mean over 2 rounds = 3*sum(excess)/8.
        blocks.setdefault(spec['block_id'],{})[spec['condition']]=3*excess_total
        if worlds[spec['session_id']]['mean_owner_loss']['value']!=excess_total*3/8:raise ValueError('World mean differs')
    differences=[v['receipt_cap']-v['ordinary_settlement'] for _,v in sorted(blocks.items())]
    if len(differences)!=16:raise ValueError('Incomplete pairs')
    distribution=Counter({0:1})
    for d in differences:
        updated=Counter()
        for subtotal,n in distribution.items():updated[subtotal+d]+=n;updated[subtotal-d]+=n
        distribution=updated
    extreme=sum(n for total,n in distribution.items() if abs(total)>=abs(sum(differences)))
    effect=Fraction(sum(differences),128);p=Fraction(extreme,65536);original=analysis['primary']
    if original['effect']['value']!=float(effect) or original['p']['value']!=float(p) or original['extreme_assignments']!=extreme:raise ValueError('Primary statistic differs')
    result={'passed':True,'raw_main_rounds':checks,'blocks':16,'assignments':sum(distribution.values()),'extreme_assignments':extreme,
        'effect':str(effect),'p':str(p),'alternative_computation':'Integer-eighth convolution, original provider wire only',
        'verifier_sha256':sha(Path(__file__)),'analysis_sha256':sha(ROOT/'ANALYSIS_CORRECTED.json')}
    path=Path(output) if output else ROOT/'release/INDEPENDENT_PRIMARY_CHECK.json'
    with path.open('x') as f:json.dump(result,f,indent=2);f.write('\n')
    print(json.dumps(result))
if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path);args=p.parse_args();check(args.output)
