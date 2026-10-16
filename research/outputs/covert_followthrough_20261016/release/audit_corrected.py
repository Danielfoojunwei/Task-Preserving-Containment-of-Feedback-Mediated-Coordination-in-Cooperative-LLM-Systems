#!/usr/bin/env python3
"""Independent raw-wire audit including the retained failed review phase.

Reuses only the frozen stdlib independent checker, not runner/transport/analyzer.
Exactly 648 behavior +96 intent +3 rejected public +32 corrected public calls.
Unknown rejected-call bills retain reservations. Correction is annotation-only.
"""
from collections import Counter
import importlib.util
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
sp=importlib.util.spec_from_file_location('ft_corrected_audit_math',ROOT/'independent_verify.py');V=importlib.util.module_from_spec(sp);sp.loader.exec_module(V)
NEW=ROOT/'release/correction'
def inventory():
 files=V.source_inventory(ROOT)
 for name,pin in V.source_inventory(NEW).items():files['release/correction/'+name]=pin
 return files

def run(output=None):
 output=Path(output) if output else ROOT/'independent/corrected'
 if output.exists():raise FileExistsError(output)
 output.mkdir(parents=True);before=inventory()
 audit=V.Audit(ROOT,'all')
 for base in (ROOT,NEW):
  for name,wanted in V.load(base/'FREEZE.json')['sha256'].items():audit.same(V.file_hash(base/name),wanted,'frozen_dependency',name)
 for phase in ('controls','pilot','main'):
  for spec in audit.plan[phase]:
   state=audit.initial(spec)
   for case in audit.plan['cases'][str(spec['seed'])]:state=audit.round(phase,spec,state,case)
  audit.same(V.load(ROOT/(phase+'_completion.json'))['complete'],True,'financial_phase_complete',phase)
 audit.same(len(audit.calls),648,'all_behavior_calls')
 audit.check(all(c['completed'] for c in audit.calls),'all_behavior_completed')
 manifest=V.load(ROOT/'reviews/MANIFEST.json');material=V.load(ROOT/'annotation_material.json');rubric=(ROOT/'EVIDENCE_RUBRIC.md').read_text()
 for job in manifest['initial']+manifest['third']:
  packet=V.load(ROOT/job['packet_path']);messages=[{'role':'system','content':material['system']},{'role':'user','content':V.canonical({'rubric':rubric,'packet':packet}).decode()}]
  result=audit.call(job['call_path'],messages,'reviewer');audit.check(result['completed'],'intent_annotation_completed',job['review_id'])
 failed=[]
 for job in manifest['disclosure']:
  if not (ROOT/'calls'/job['call_path']/'call.json').exists():continue
  packet=V.load(ROOT/job['packet_path']);messages=[{'role':'system','content':material['disclosure_system']},{'role':'user','content':V.canonical({'rubric':rubric,'packet':packet}).decode()}]
  result=audit.call(job['call_path'],messages,'reviewer');failed.append(result)
  audit.same(result['record']['http_status'],400,'retained_json_mode_rejection')
  audit.same(result['completed'],False,'failed_phase_not_relabelled')
 audit.same(len(failed),3,'exactly_three_retained_rejections')
 audit.same({p.parent for p in (ROOT/'calls').glob('**/call.json')},audit.seen_paths,'all_original_calls_inventoried')
 # Call checker uses only fields initialized here; no production runtime imported.
 supplement=object.__new__(V.Audit);supplement.root=NEW;supplement.checks=Counter();supplement.failures=[];supplement.calls=[];supplement.seen_paths=set()
 plan=V.load(NEW/'plan.json')
 for job in plan['jobs']:
  packet=V.load(NEW/job['packet_path']);messages=[{'role':'system','content':plan['system']},{'role':'user','content':V.canonical({'packet':packet}).decode()}]
  result=supplement.call(job['call_path'],messages,'reviewer');supplement.check(result['completed'],'supplement_completed',job['review_id'])
  supplement.check(result['row']['started_at']>=V.load(NEW/'FREEZE.json')['frozen_at'],'supplement_freeze_before_dispatch')
 supplement.same(len(supplement.calls),32,'all_corrected_public_calls')
 supplement.same({p.parent for p in (NEW/'calls').glob('**/call.json')},supplement.seen_paths,'all_supplement_calls_inventoried')
 audit.failures+=supplement.failures;audit.checks.update(supplement.checks)
 calls=audit.calls+supplement.calls
 for c in calls:c['section']='followthrough_and_annotation_correction'
 budget=V.budget_events(calls,8.5);concurrency=V.concurrency_check(calls)
 audit.same(budget['failures'],[],'all_phase_budget_events')
 audit.check(V.PRIOR_CLOSED+budget['accounted_including_unknown_cost_usd']<=V.AGGREGATE_CAP,'original_total_cap')
 audit.check(concurrency['peak_observed_inflight_calls']<=3,'three_global_workers')
 ids=[c['response_id'] for c in calls if c['completed']]
 audit.same(len(ids),776,'completed_calls_count');audit.same(len(set(ids)),776,'unique_completed_provider_ids')
 audit.same(len(calls),779,'all_requests_including_failed')
 after=inventory();audit.same(before,after,'source_stability')
 report={'passed':not audit.failures,'protocol_deviation_disclosed':True,'financial_design_unchanged':True,
  'checks':dict(audit.checks),'failures':audit.failures,'inventory':{'verified_requests':779,'completed':776,'rejected':3,'behavior_completed':648,
    'intent_completed':96,'corrected_public_completed':32,**budget,**concurrency,'aggregate_accounted_usd':V.PRIOR_CLOSED+budget['accounted_including_unknown_cost_usd']},
  'freeze_sha256':V.file_hash(ROOT/'FREEZE.json'),'correction_freeze_sha256':V.file_hash(NEW/'FREEZE.json'),'verifier_sha256':V.file_hash(__file__)}
 path=output/'INDEPENDENT_VERIFICATION_CORRECTED.json';V.exclusive_json(path,report)
 V.exclusive_json(output/'SOURCE_BINDINGS.json',{'passed':report['passed'],'before_after_equal':before==after,'raw_verification_sha256':V.file_hash(path),'files':before})
 print(json.dumps({'passed':report['passed'],'failures':len(audit.failures),'inventory':V.jsonable(report['inventory'])}))
 if audit.failures:raise RuntimeError('Independent corrected audit failed')
 return report
if __name__=='__main__':
 import argparse
 p=argparse.ArgumentParser();p.add_argument('--output-dir',type=Path);a=p.parse_args();run(a.output_dir)
