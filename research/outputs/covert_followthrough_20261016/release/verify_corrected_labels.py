#!/usr/bin/env python3
"""Offline derivation audit of corrected labels; not semantic gold validation."""
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
sp=importlib.util.spec_from_file_location('ft_label_check_v2',ROOT/'release/review_v2.py');V=importlib.util.module_from_spec(sp);sp.loader.exec_module(V)
Q,P=V.Q,V.P;NEW=ROOT/'release/correction'
def verify():
 manifest=P.load(ROOT/'reviews/MANIFEST.json');seal=P.load(NEW/'SEALED_V2.json');parsed={};checks=0
 def same(a,b,label):
  nonlocal checks
  checks+=1
  if a!=b:raise ValueError(label)
 plan=P.load(ROOT/'plan.json');specs={s['session_id']:s for s in plan['main']};index=P.load(ROOT/'review_index.json')['worlds']
 for i in index:
  sid=i['session_id'];spec=specs[sid];expected=[]
  for n in (1,2):
   prefix=P.load(ROOT/'runs/main'/sid/'rounds'/str(n)/'prefix_review_packet.json')
   expected.append({'round':n,'notes':prefix['notes'],'public_reports':prefix['public_reports'],'upcoming_trusted_receipts':plan['cases'][str(spec['seed'])][n-1]['receipts']})
  same(P.load(ROOT/'review_packets'/(i['review_id']+'.json'))['prefixes'],expected,'pre-action packet provenance')
 for j in manifest['initial']+manifest['third']:
  value=V.parse_v2(j);same(value,P.load(NEW/'normalized_reviews'/j['role']/(j['review_id']+'.json')),'normalized label differs from original wire')
  parsed[(j['review_id'],j['role'])]=value
 worlds=[]
 for i in index:
  rid=i['review_id'];a,b=parsed[(rid,'a')],parsed[(rid,'b')]
  needs=any(x[f] is None or y[f] is None or x[f]!=y[f] or(x['harmful_active'] is True and x['expected_actions']!=y['expected_actions']) for x,y in zip(a['prefixes'],b['prefixes']) for f in Q.FIELDS)
  reviews=[a,b]+([parsed[(rid,'c')]] if needs else []);rows=[]
  for n in (1,2):
   votes=[v['prefixes'][n-1] for v in reviews];row={'round':n}
   for f in Q.FIELDS:row[f]=True if sum(v[f] is True for v in votes)>=2 else False if sum(v[f] is False for v in votes)>=2 else None
   row['expected_actions']={stage:{a:next((value for value in range(11) if sum(v['expected_actions'][stage][a]==value for v in votes)>=2),None) for a in 'AB'} for stage in ('claims','approvals')}
   row['evidence_records']=votes;rows.append(row)
  worlds.append({'review_id':rid,'prefixes':rows,'third_required_after_correction':needs,'source_hashes':[P.file_hash(NEW/'normalized_reviews'/v['role']/(rid+'.json')) for v in reviews]})
 same(worlds,seal['worlds'],'majority/NULL seal integrity')
 supplement=P.load(NEW/'plan.json')
 for i,world in zip(index,worlds):
  prefixes=[]
  for n in (1,2):
   end=P.load(ROOT/'runs/main'/i['session_id']/'rounds'/str(n)/'end_state.json');row=world['prefixes'][n-1]
   contracts=[{k:v['evidence'].get(k) for k in ('financial_proposal','financial_acceptance')} for v in row['evidence_records'] if v['harmful_active'] is True]
   prefixes.append({'round':n,'public_reports':end['public_reports'],'contract_text_evidence':contracts})
  same(P.load(NEW/'packets'/(i['review_id']+'.json')),{'review_id':i['review_id'],'prefixes':prefixes,'no_actual_actions_ledger_private_memory_or_reviewer_labels':True},'corrected public-only packet')
 old=Q.HERE;Q.HERE=NEW
 try:
  for j in supplement['jobs']:
   same(Q.parse(j),P.load(NEW/'reviews'/(j['review_id']+'.json')),'public judgment changed from wire')
   record=P.load(NEW/'calls'/j['call_path']/'call.json');same(record['started_at']>=seal['sealed_at'],True,'intent seal precedes corrected public review')
 finally:Q.HERE=old
 result={'passed':True,'checks':checks,'original_intent_responses_reparsed':96,'new_public_responses_reparsed':32,'worlds':32,'semantic_accuracy_established':False,
  'seal_sha256':P.file_hash(NEW/'SEALED_V2.json'),'verifier_sha256':P.file_hash(__file__)}
 P.save_new(ROOT/'release/CORRECTED_LABEL_INTEGRITY.json',result);print(json.dumps(result))
if __name__=='__main__':verify()
