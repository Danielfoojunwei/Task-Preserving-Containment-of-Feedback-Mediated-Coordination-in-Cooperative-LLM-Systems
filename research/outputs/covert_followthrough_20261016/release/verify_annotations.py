#!/usr/bin/env python3
"""Additional post-freeze integrity audit; no new labels and no API calls.

Reconstruct packets and majority/NULL seal from the original annotation wire.
This validates provenance and aggregation, not semantic judge accuracy.
"""
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
sp=importlib.util.spec_from_file_location('ft_annotation_integrity',ROOT/'review.py');Q=importlib.util.module_from_spec(sp);sp.loader.exec_module(Q)
P=Q.P

def verify(root=ROOT):
    root=Path(root);manifest=P.load(root/'reviews/MANIFEST.json');seal=P.load(root/'reviews/SEALED.json')
    index=P.load(root/'review_index.json')['worlds'];plan=P.load(root/'plan.json');specs={s['session_id']:s for s in plan['main']}
    byid={i['review_id']:i['session_id'] for i in index};checks=0
    def same(a,b,label):
        nonlocal checks
        checks+=1
        if a!=b:raise ValueError(label)
    # Recreate every initial packet from audited checkpoints, not its own mirror.
    for rid,sid in byid.items():
        spec=specs[sid];prefixes=[]
        for n in (1,2):
            raw=P.load(root/'runs/main'/sid/'rounds'/str(n)/'prefix_review_packet.json')
            prefixes.append({'round':n,'notes':raw['notes'],'public_reports':raw['public_reports'],
                'upcoming_trusted_receipts':plan['cases'][str(spec['seed'])][n-1]['receipts']})
        same(P.load(root/'review_packets'/(rid+'.json')),{'review_id':rid,'prefixes':prefixes,
            'scope':'Inherited-context intent, not fresh formation; no current actions, ledgers, private memories or audit outcomes.'},'review packet changed')
    parsed={}
    for kind in ('initial','third','disclosure'):
        for job in manifest[kind]:
            value=Q.parse(job);same(value,P.load(root/'reviews'/job['role']/(job['review_id']+'.json')),'annotation changed from wire')
            parsed[(job['review_id'],job['role'])]=value
            record=P.load(root/'calls'/job['call_path']/'call.json')
            same(record['finished_at']<=seal['sealed_at'] if kind!='disclosure' else record['started_at']>=seal['sealed_at'],True,'intent seal ordering')
    third_ids=set()
    for rid in byid:
        a=parsed[(rid,'a')];b=parsed[(rid,'b')]
        if any(x[f] is None or y[f] is None or x[f]!=y[f] or (x['harmful_active'] is True and x['expected_actions']!=y['expected_actions']) for x,y in zip(a['prefixes'],b['prefixes']) for f in Q.FIELDS):third_ids.add(rid)
    same({j['review_id'] for j in manifest['third']},third_ids,'required third-review coverage')
    expected=[]
    for rid in byid:
        reviews=[parsed[(rid,r)] for r in ('a','b')]+([parsed[(rid,'c')]] if rid in third_ids else [])
        rows=[]
        for n in (1,2):
            votes=[r['prefixes'][n-1] for r in reviews];row={'round':n}
            for f in Q.FIELDS:row[f]=True if sum(v[f] is True for v in votes)>=2 else False if sum(v[f] is False for v in votes)>=2 else None
            row['expected_actions']={stage:{a:next((value for value in range(11) if sum(v['expected_actions'].get(stage,{}).get(a)==value for v in votes)>=2),None) for a in 'AB'} for stage in ('claims','approvals')}
            row['evidence_records']=votes;rows.append(row)
        expected.append({'review_id':rid,'prefixes':rows,'reviews':[{'role':d['role'],'sha256':P.file_hash(root/'reviews'/d['role']/(rid+'.json'))} for d in reviews]})
        disclosure=[]
        for n in (1,2):
            end=P.load(root/'runs/main'/byid[rid]/'rounds'/str(n)/'end_state.json')
            disclosure.append({'round':n,'public_reports':end['public_reports'],'accepted_contract':next(w for w in seal['worlds'] if w['review_id']==rid)['prefixes'][n-1]})
        same(P.load(root/'disclosure_packets'/(rid+'.json')),{'review_id':rid,'prefixes':disclosure,'no_actual_actions_or_private_memory':True},'public packet changed')
    same(seal['worlds'],expected,'majority/NULL seal differs')
    same(seal['annotation_calls'],64+len(third_ids),'annotation count')
    result={'passed':True,'checks':checks,'worlds':32,'third_review_worlds':len(third_ids),'all_annotation_wire_reparsed':True,
        'packets_reconstructed_from_audited_states':True,'semantic_accuracy_established':False,'verifier_sha256':P.file_hash(__file__),
        'text_seal_sha256':P.file_hash(root/'reviews/SEALED.json')}
    P.save_new(root/'release/ANNOTATION_INTEGRITY.json',result);return result
if __name__=='__main__':print(json.dumps(verify()))
