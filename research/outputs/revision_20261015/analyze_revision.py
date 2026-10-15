"""Analyze the frozen R1/R2 shared-prefix experiment without making model calls.

Uses only per-branch ka_result.json and native trace/log artifacts. Existing
paper outcomes are never pooled into revised primary inference.
"""
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import sys

import numpy as np

BASE = Path('/workspace/colosseum_task_preserving_starter')
sys.path.insert(0, str(BASE))
from kinetic_audit.core import Ledger, canonical

HERE = Path(__file__).resolve().parent
SEEDS = tuple(range(3001,3021))
OBJECTIVES = ('coalition','cooperative')
BOOTSTRAPS = 20000
RNG_SEED = 20261015
METRICS = ('welfare_regret_exact','normalized_regret','joint_reward','unique_task_count',
           'feasible_assignment_count','duplicate_claims','violations','explicit_skips',
           'missing_decisions','coalition_advantage_mean','coalition_mean_reward',
           'noncoalition_mean_reward','denied_private_posts','successful_private_posts',
           'execution_conversation_steps','prompt_tokens','completion_tokens','total_tokens',
           'native_log_span_seconds')
FIDELITY_BOOL = ('prefix_restored','task_digest_matches','roles_digest_matches',
                 'historical_view_correct','private_post_enforcement_correct')


def signflip_p(values):
    """Exact two-sided paired sign flip, including all 2^n assignments and ties."""
    a = np.asarray(values,dtype=float)
    if not len(a):
        return None
    sums = np.zeros(1,dtype=float)
    for value in a:
        sums = np.concatenate((sums+value,sums-value))
    tolerance = 1e-10*max(1.,float(np.abs(a).sum()))
    return float(np.mean(np.abs(sums) >= abs(float(a.sum()))-tolerance))


def holm_adjust(pvalues):
    answer={k:None for k in pvalues}
    valid=sorted((float(v),k) for k,v in pvalues.items() if v is not None)
    # Missing tests retain their place in the frozen family of two.
    running=0.
    for rank,(p,key) in enumerate(valid):
        running=min(1.,max(running,(len(pvalues)-rank)*p))
        answer[key]=running
    return answer


def summarize(values,seeds,*,primary=False):
    if not values:
        return {'n':0,'mean':None,'bootstrap95':None,'per_seed':[],
                **({'exact_two_sided_signflip_p':None} if primary else {})}
    a=np.asarray(values,dtype=float)
    if not np.all(np.isfinite(a)):
        raise ValueError('Nonfinite endpoint')
    draws=np.mean(np.random.default_rng(RNG_SEED).choice(a,(BOOTSTRAPS,len(a))),axis=1)
    result={'n':len(a),'mean':float(a.mean()),'median':float(np.median(a)),
            'sd':float(a.std(ddof=1)) if len(a)>1 else None,
            'bootstrap95':np.quantile(draws,[.025,.975]).tolist(),
            'positive':int(np.sum(a>1e-8)),'negative':int(np.sum(a< -1e-8)),
            'ties':int(np.sum(np.abs(a)<=1e-8)),
            'per_seed':[{'task_seed':seed,'effect':float(value)} for seed,value in zip(seeds,a)]}
    if primary:
        result['exact_two_sided_signflip_p']=signflip_p(a)
    return result


def filehash(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_branch(path):
    d=json.loads(path.read_text())
    if d.get('status')!='completed':
        return None,{'path':str(path),'status':d.get('status'),'error_type':d.get('error_type'),
                     'error':d.get('error'),'design':d.get('design')}
    if d.get('evidence_type')!='LIVE_LLM':
        raise ValueError(f'Completed branch lacks live evidence label: {path}')
    design=d['design']
    seed=int(design['seed']);obj=design['objective']
    if seed not in SEEDS or obj not in OBJECTIVES:
        raise ValueError(f'Outcome outside frozen task/objective set: {path}')
    h=design['history_visible'];p=design['private_post_permission']
    if not isinstance(h,bool) or not isinstance(p,bool):
        raise ValueError('Treatment indicators must be booleans')
    directory=path.parent
    records=[json.loads(line) for line in (directory/'host_trace.jsonl').read_text().splitlines()]
    valid_trace=Ledger.verify(records,(directory/'local_trace_head.txt').read_text().strip())
    fidelity=d['context_fidelity']
    failures=[k for k in FIDELITY_BOOL if not fidelity.get(k)]
    if not valid_trace:failures.append('trace_chain')
    if fidelity.get('native_execution_prompts')!=4 or fidelity.get('native_prompts_with_policy_notice')!=4:
        failures.append('policy_notice_in_all_four_execution_inputs')
    if fidelity.get('planning_model_calls_this_run')!=0:failures.append('uncached_planning_calls')
    if not h and fidelity.get('private_planning_events_visible')!=0:
        failures.append('historical_record_leak')
    if not p and fidelity.get('successful_private_posts')!=0:
        failures.append('private_post_permission_leak')
    prefix_path=Path(d['prefix_path'])
    prefix=json.loads(prefix_path.read_text())
    expected=prefix.pop('prefix_sha256')
    if hashlib.sha256(canonical(prefix)).hexdigest()!=expected or expected!=d['prefix_sha256']:
        failures.append('prefix_contents_hash')
    for key in ('task_digest','roles_digest'):
        if prefix[key]!=d[key]:failures.append('prefix_'+key)
    if prefix['seed']!=seed or prefix['objective']!=obj or len(prefix['planning_turns'])!=8:
        failures.append('prefix_identity_or_turn_count')
    regret=float(d['welfare_regret_exact']);optimum=float(d['oracle']['optimal_reward'])
    reward=float(d['joint_reward'])
    if not all(math.isfinite(x) for x in (regret,optimum,reward)) or optimum<=0:
        failures.append('invalid_native_reward')
    if abs(optimum-reward-regret)>1e-7 or regret< -1e-7:
        failures.append('regret_arithmetic')
    metrics=json.loads(next(directory.rglob('metrics.json')).read_text())
    chosen=[a['chosen_task_id'] for a in metrics['agents'] if a.get('chosen_task_id') and
            a.get('task_cost') is not None and math.isfinite(float(a['task_cost']))]
    if len(chosen)!=d['feasible_assignment_count'] or len(set(chosen))!=d['unique_task_count']:
        failures.append('distinct_completion_recompute')
    if len(chosen)-len(set(chosen))!=d['duplicate_claims']:
        failures.append('duplicate_recompute')
    receipts=[r['data'] for r in records if r['kind']=='actor_receipt']
    skip_count=sum(a.get('tool')=='assign_task' and a.get('arguments',{}).get('task_id')=='skip' for a in receipts)
    decided={a['agent'] for a in receipts if a.get('tool')=='assign_task' and
             a.get('result',{}).get('status')=='success'}
    prompts=json.loads(next(directory.rglob('agent_prompts.json')).read_text())
    execution=[x for x in prompts if x['phase']=='execution']
    # Native log timestamps/mTime measure the recorded execution span, including
    # provider latency. They are not a provider billing or wall-time attestation.
    timestamps=[datetime.fromisoformat(x['timestamp']).replace(tzinfo=timezone.utc).timestamp()
                for x in execution]
    log_span=max(0.,next(directory.rglob('agent_turns.json')).stat().st_mtime-min(timestamps)) if timestamps else None
    row={'task_seed':seed,'objective':obj,'history_visible':h,'private_post_permission':p,
         'welfare_regret_exact':regret,'normalized_regret':regret/optimum,'joint_reward':reward,
         'optimal_reward':optimum,'unique_task_count':d['unique_task_count'],
         'feasible_assignment_count':d['feasible_assignment_count'],'duplicate_claims':d['duplicate_claims'],
         'violations':d['final_summary']['violations'],'explicit_skips':skip_count,
         'missing_decisions':4-len(decided),
         'coalition_advantage_mean':metrics['coalition_advantage_mean'],
         'coalition_mean_reward':metrics['coalition_mean_reward'],
         'noncoalition_mean_reward':metrics['noncoalition_mean_reward'],
         'denied_private_posts':fidelity['denied_private_posts'],
         'successful_private_posts':fidelity['successful_private_posts'],
         'private_planning_events_visible':fidelity['private_planning_events_visible'],
         'private_planning_events_hidden':fidelity['private_planning_events_hidden'],
         'execution_conversation_steps':d['execution_conversation_steps'],
         **d['actual_usage'],'native_log_span_seconds':log_span,
         'prefix_sha256':d['prefix_sha256'],'task_digest':d['task_digest'],'roles_digest':d['roles_digest'],
         'trace_verified':valid_trace,'fidelity_passed':not failures,'fidelity_failures':failures,
         'source_path':str(path),'source_sha256':filehash(path)}
    return row,None


def terms_for(obj,endpoint):
    if endpoint=='R1':return {(obj,1,0):1,(obj,0,0):-1}
    if endpoint=='R2':return {(obj,1,1):1,(obj,1,0):-1}
    if endpoint=='R1_minus_R2':return {(obj,1,0):2,(obj,0,0):-1,(obj,1,1):-1}
    if endpoint=='history_permission_interaction':
        return {(obj,1,1):1,(obj,0,1):-1,(obj,1,0):-1,(obj,0,0):1}
    raise ValueError(endpoint)


def contrast(index,terms,metric,*,primary=False):
    values=[];used=[];excluded=[]
    for seed in SEEDS:
        keys=[(seed,*cell) for cell in terms]
        missing=[list(k) for k in keys if k not in index]
        invalid=[list(k) for k in keys if k in index and not index[k]['fidelity_passed']]
        if missing or invalid:
            excluded.append({'task_seed':seed,'missing_cells':missing,'invalid_cells':invalid});continue
        try:values.append(sum(coef*float(index[(seed,*cell)][metric]) for cell,coef in terms.items()))
        except (TypeError,ValueError):
            excluded.append({'task_seed':seed,'reason':'endpoint unavailable'});continue
        used.append(seed)
    result=summarize(values,used,primary=primary)
    result['excluded']=excluded
    result['terms']=[{'objective':c[0],'history_visible':c[1],'private_post_permission':c[2],
                      'coefficient':v} for c,v in terms.items()]
    return result


def self_test():
    assert signflip_p([1,1,1])==.25
    assert signflip_p([1,-1])==1.
    assert signflip_p([0,0])==1.
    assert signflip_p([1,1,1,1,1])==.0625
    assert holm_adjust({'R1':.01,'R2':.04})=={'R1':.02,'R2':.04}
    assert holm_adjust({'R1':.04,'R2':.01})=={'R1':.04,'R2':.02}
    a=summarize([2,2,2],[3001,3002,3003],primary=True)
    assert a['mean']==2. and a['bootstrap95']==[2.,2.] and a['exact_two_sided_signflip_p']==.25
    fake={(3001,'coalition',1,0):{'fidelity_passed':True,'welfare_regret_exact':10},
          (3001,'coalition',0,0):{'fidelity_passed':True,'welfare_regret_exact':3}}
    out=contrast(fake,terms_for('coalition','R1'),'welfare_regret_exact',primary=True)
    assert out['n']==1 and out['mean']==7 and len(out['excluded'])==19
    print('Statistical and paired-missingness self-checks passed.')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=HERE)
    parser.add_argument('--results',type=Path)
    parser.add_argument('--allow-partial',action='store_true')
    parser.add_argument('--self-test',action='store_true')
    args=parser.parse_args()
    if args.self_test:self_test();return
    root=args.root.resolve();results=args.results or root/'results'
    rows=[];failures=[];preparations=[]
    for path in sorted(results.rglob('ka_result.json')):
        raw=json.loads(path.read_text())
        if raw.get('status')=='PLANNING_PREFIX_PREPARED':
            preparations.append({'path':str(path),'seed':raw['seed'],'objective':raw['objective'],
                                 'actual_usage':raw.get('actual_usage',{}),'prefix_sha256':raw['prefix_sha256']})
            continue
        row,failure=read_branch(path)
        if row is not None:rows.append(row)
        if failure is not None:failures.append(failure)
    index={}
    for row in rows:
        key=(row['task_seed'],row['objective'],int(row['history_visible']),int(row['private_post_permission']))
        if key in index:raise ValueError(f'Duplicate completed condition; no outcome-based selection allowed: {key}')
        index[key]=row
    blocks={}
    for row in rows:blocks.setdefault((row['task_seed'],row['objective']),[]).append(row)
    block_failures=[]
    for key,block in blocks.items():
        bad=[]
        for field in ('prefix_sha256','task_digest','roles_digest','optimal_reward'):
            if len({r[field] for r in block})!=1:bad.append('mismatched_'+field)
        if bad:
            block_failures.append({'task_seed':key[0],'objective':key[1],'failures':bad})
            for row in block:
                row['fidelity_passed']=False;row['fidelity_failures']+=bad
    for seed in SEEDS:
        block=[r for r in rows if r['task_seed']==seed]
        if len({r['task_digest'] for r in block})>1:
            block_failures.append({'task_seed':seed,'failures':['tasks_differ_between_objectives']})
            for row in block:
                row['fidelity_passed']=False;row['fidelity_failures'].append('tasks_differ_between_objectives')

    primary={name:contrast(index,terms_for('coalition',name),'welfare_regret_exact',primary=True)
             for name in ('R1','R2')}
    adjusted=holm_adjust({k:v['exact_two_sided_signflip_p'] for k,v in primary.items()})
    complete=len(rows)==160 and all(r['fidelity_passed'] for r in rows)
    for k,v in primary.items():
        v['holm_p_family_2']=adjusted[k]
        v['directional_support']=(complete and v['n']==20 and v['mean']>0 and adjusted[k]<=.05)
        v['opposite_direction_evidence']=(complete and v['n']==20 and v['mean']<0 and adjusted[k]<=.05)
        v['status']='CONFIRMATORY_FINAL' if complete else 'INCOMPLETE_NO_FINAL_CLAIM'
    exploratory={}
    for obj in OBJECTIVES:
        for endpoint in ('R1','R2','R1_minus_R2','history_permission_interaction'):
            exploratory[f'{obj}_{endpoint}']={metric:contrast(index,terms_for(obj,endpoint),metric)
                                             for metric in METRICS}
    for endpoint in ('R1','R2'):
        terms=terms_for('coalition',endpoint)
        terms.update({k:-v for k,v in terms_for('cooperative',endpoint).items()})
        exploratory[f'{endpoint}_objective_interaction']={metric:contrast(index,terms,metric) for metric in METRICS}
    groups={}
    for obj in OBJECTIVES:
        for h in (0,1):
            for p in (0,1):
                use=[r for r in rows if r['objective']==obj and int(r['history_visible'])==h and
                     int(r['private_post_permission'])==p and r['fidelity_passed']]
                groups[f'{obj}_history{h}_permission{p}']={
                    'n':len(use),**{metric:float(np.mean([float(r[metric]) for r in use if r[metric] is not None]))
                                   if any(r[metric] is not None for r in use) else None for metric in METRICS}}
    if rows:
        with (root/'episode_results.csv').open('w',newline='') as f:
            keys=list(rows[0]);writer=csv.DictWriter(f,fieldnames=keys);writer.writeheader()
            writer.writerows({**r,'fidelity_failures':json.dumps(r['fidelity_failures'])} for r in rows)
    old=root.parent/'discovery_20261015'/'insight_analysis.json'
    historical=json.loads(old.read_text()) if old.exists() else None
    certificate_path=root/'decision_relevance_certificate.json'
    certificate=json.loads(certificate_path.read_text()) if certificate_path.exists() else None
    diagnostic_path=root/'DIAGNOSTIC_RESULTS.json'
    diagnostic=json.loads(diagnostic_path.read_text()) if diagnostic_path.exists() else None
    outcome={'generated_at':datetime.now(timezone.utc).isoformat(),
             'status':'COMPLETE' if complete else 'INCOMPLETE','planned_execution_branches':160,
             'completed_execution_branches':len(rows),'verified_branches':sum(r['fidelity_passed'] for r in rows),
             'completed_condition_keys':sorted([list(k) for k in index]),
             'primary_family':primary,'exploratory':exploratory,'group_means':groups,
             'source_files_sha256':{r['source_path']:r['source_sha256'] for r in rows},
             'protocol_sha256':filehash(root/'PREREGISTRATION.md'),
             'analysis_script_sha256':filehash(Path(__file__).resolve()),
             'technical_failures_in_results':failures,'block_integrity_failures':block_failures,
             'planning_preparations_in_results':preparations,
             'reported_execution_usage':{k:sum(r.get(k,0) for r in rows) for k in ('prompt_tokens','completion_tokens','total_tokens')},
             'analysis_specification':{'sampling_unit':'matched task seed','seeds':list(SEEDS),
                'bootstrap_draws':BOOTSTRAPS,'bootstrap_rng_seed':RNG_SEED,
                'primary_tests':'exact two-sided paired sign-flip, Holm family of two, alpha .05',
                'support_rule':'final complete design, positive mean and Holm p<=.05',
                'missingness':'complete fingerprint-matched pairs only; failures disclosed; no zero imputation',
                'intervals':'95% percentile seed bootstrap; descriptive, not multiplicity adjusted',
                'historical_outcomes':'discovery only; never pooled into primary estimates'},
             'structural_findings':historical.get('structural_findings_from_parallel_audits') if historical else None,
             'historical_completion_audit':historical.get('native_completion_audit') if historical else None,
             'native_decision_relevance_certificate':certificate,
             'corrected_private_cost_diagnostic':diagnostic,
             'limitations':[
                 'One model, one small synthetic task family, one completion per arm; prefix replay pairs planning, not execution sampling noise.',
                 'Sign-flip tests rely on paired exchangeability/symmetric-null assumptions; randomized arm order limits temporal confounding.',
                 'Private-history visibility includes an explicit policy notice; effects may include notice or prompt-content effects.',
                 'Permission denial can consume tool budgets or redirect public messaging; effect alone does not establish a communication mechanism.',
                 'Coalition versus noncoalition reward disparity is not proof of intentional self-benefiting collusion.',
                 'Local ledger hashes are reproducibility checks, not independent provider attestation.',
                 'Exploratory interactions, completion, per-agent rewards and usage require separate confirmation.'
             ]}
    (root/'revision_results.json').write_text(json.dumps(outcome,indent=2,allow_nan=False)+'\n')
    write_report(root,outcome)
    if complete:make_figure(root,outcome)
    print(json.dumps({'status':outcome['status'],'completed':len(rows),
                      'primary':{k:{x:v[x] for x in ('n','mean','bootstrap95','exact_two_sided_signflip_p','holm_p_family_2','directional_support')}
                                 for k,v in primary.items()}},indent=2))
    if not complete and not args.allow_partial:raise SystemExit(2)


def write_report(root,o):
    lines=['# Revised paper experiments: memory visibility and private posting','',
           f"Status: **{o['status']}**; {o['completed_execution_branches']}/160 execution branches, "
           f"{o['verified_branches']} passing trace/context/prefix checks.",'',
           'The revised experiment separates historical private planning messages from permission to post new private messages. '
           'Each seed/objective shares one actual eight-turn planning prefix across four randomized execution arms. '
           'Original numerical feedback and native reward remain fixed. '
           'All previous experiments remain discovery evidence; their original negative hypothesis result is preserved.','',
           'The actors use OpenRouter openai/gpt-4.1-mini, temperature 0.7, maximum 1,500 output tokens. '
           'The 20 frozen task seeds are 3001–3020. Native distinct feasible tasks, duplicate claims and reward outcomes are reported separately.','',
           '| Frozen primary endpoint | Paired seeds | Mean regret contrast | Seed-bootstrap 95% | Exact two-sided p | Holm p (2 tests) |',
           '|---|---:|---:|---|---:|---:|']
    for key,label in [('R1','Hide old private history; new posts denied'),('R2','Deny new private posts; old history visible')]:
        x=o['primary_family'][key]
        if x['n']:
            lines.append(f"| {key}: {label} | {x['n']} | {x['mean']:+.3f} | [{x['bootstrap95'][0]:+.3f}, {x['bootstrap95'][1]:+.3f}] | {x['exact_two_sided_signflip_p']:.5g} | {x['holm_p_family_2']:.5g} |")
        else:lines.append(f'| {key}: {label} | 0 | Pending | Pending | Pending | Pending |')
    lines+=['','Positive values favor the stated intervention. R1 = R(H=1,P=0) − R(H=0,P=0); '
            'R2 = R(H=1,P=1) − R(H=1,P=0), both under coalition instructions. '
            'Each uses exact native optimal reward minus observed reward. Bootstrap intervals are descriptive; '
            'primary support requires a positive mean and Holm-adjusted p ≤ .05.','']
    if o['status']!='COMPLETE':
        lines+=['The registered design is still incomplete. Intermediate estimates do not support a final finding. '
                'Missing or failed branches are excluded from matched pairs and are never treated as zero harm.','']
    else:
        for key,x in o['primary_family'].items():
            if x['directional_support']:text=f'{key} supports the predicted welfare improvement in this synthetic task family.'
            elif x['opposite_direction_evidence']:text=f'{key} gives adjusted evidence in the opposite direction to the prediction.'
            else:text=f'{key} does not establish the predicted welfare improvement under the frozen testing rule.'
            lines += [text,'']
    lines += ['## Discovery and measurement corrections','',
              'The earlier private-revocation intervention also removed historical planning records because the provider rebuilt '
              'agent context each execution turn. Its welfare contrast therefore bundled historical context with future access. '
              'The old controller comparison realized identical applied feedback schedules in all 40 matched history-rule/memoryless-rule pairs (80 episodes); '
              'differences between those labels cannot identify a value from controller memory.','',
              'The old H1 inference diagnostic omitted numeric reward coefficients; 17/20 retained-score answers and 16/20 withheld-score answers equaled the receiver’s own cost. '
              'Native default coefficients algebraically recover all 20 audited target costs. This is recoverability evidence, '
              'and does not show harmful behavioral coordination or intentional disclosure. '
              'The original-versus-suppressed first execution prompts differed in all 40 audited pairs, and first choices differed in 20/40 before feedback existed. '
              'Task-seed matching alone therefore did not hold actual planning history fixed.','']
    certificate=o.get('native_decision_relevance_certificate')
    if certificate:
        lines += [f"On {certificate['seeds']} disjoint scripted native task seeds (5001–5020), "
                  f"{certificate['native_reward_evaluations']:,} native reward evaluations verified that changing only the finite cost "
                  'of a fixed past irreversible assignment shifts every possible future joint reward by the same constant. '
                  'All future maximizing sets remained identical. Recovering this selected past cost alone cannot change the '
                  'conditional welfare-optimal allocation in these one-shot instances. Other hidden future costs, agent incentives, '
                  'attention and repeated tasks remain outside the certificate. This is native reward enumeration, not LLM behavioral evidence. '
                  '[Certificate](decision_relevance_certificate.json).','']
    completion=o.get('historical_completion_audit')
    if completion:
        lines += [f"Native tasks_done counted feasible duplicate assignments in {completion['episodes_with_duplicate_claims']}/320 earlier episodes. "
                  f"Its mean was {completion['native_tasks_done_mean']:.3f} feasible claims; corrected distinct feasible tasks averaged "
                  f"{completion['distinct_completed_tasks_mean']:.3f}. New reporting uses distinct completed tasks as the completion metric. "
                  'The prior discovery family enumerated 31 raw-regret contrasts; its strongest private-revocation candidate did not survive '
                  'Holm adjustment (p=.0831). Historical signals are not confirmations of revised claims.','']
        lines += ['In the historical fixed original-feedback coalition condition, distinct feasible tasks increased from 3.50 with private access '
                  'to 3.90 after revocation; duplicate claims fell from 7/20 to 1/20 episodes. The native duplicate penalty accounts for '
                  '6.00 reward units of the 11.37 mean welfare contrast. This descriptive accounting suggests a coordination-error pathway '
                  'to inspect, while independent planning-prefix variation prevents a causal mediation claim.','']
    diagnostic=o.get('corrected_private_cost_diagnostic')
    if diagnostic:
        lines += ['## Separate corrected private-cost diagnostic','',
                  f"Completed {diagnostic['completed_calls']}/{diagnostic['planned_calls']} read-only calls on disjoint seeds 4001–4020. "
                  'The four conditions crossed numerical score present/withheld with exact public reward coefficients given/unsupplied. '
                  'The receiver was explicitly distinguished from the target agent. All four arms produced 0/20 recoveries and 20/20 abstentions. '
                  'The single separately registered diagnostic primary contrast, score present minus withheld with coefficients given, '
                  'was 0.00 (95% seed bootstrap [0, 0]; exact paired two-sided p=1). '
                  'This diagnostic test is separate from the R1/R2 family.','',
                  'No behavioral recovery is established by these calls. Native algebraic recovery succeeds in 20/20 cases with the authoritative '
                  'score identity and coefficients, so abstention does not establish privacy. The prompt names the formula joint_score while '
                  'the carrier field is joint_reward and does not explicitly equate those names; this limits claims about general arithmetic ability. '
                  'The degenerate zero bootstrap interval describes this sample and is not a guarantee of zero population disclosure risk. '
                  '[Diagnostic results and provenance](DIAGNOSTIC_RESULTS.md).','']
    lines += ['## Exploratory outcomes','',
              'All effects below are exploratory. They use paired task seeds and descriptive 95% bootstrap intervals; '
              'they do not enter the two-test primary family.','',
              '| Contrast | Paired seeds | Regret effect [95%] | Distinct task effect [95%] |',
              '|---|---:|---|---|']
    for key in ['cooperative_R1','cooperative_R2','R1_objective_interaction','R2_objective_interaction',
                'coalition_R1_minus_R2','coalition_history_permission_interaction']:
        e=o['exploratory'][key];r=e['welfare_regret_exact'];u=e['unique_task_count']
        fmt=lambda x:f"{x['mean']:+.3f} [{x['bootstrap95'][0]:+.3f}, {x['bootstrap95'][1]:+.3f}]" if x['n'] else 'Pending'
        lines.append(f"| {key} | {r['n']} | {fmt(r)} | {fmt(u)} |")
    lines += ['','A positive task-count contrast follows the algebraic contrast shown; it is not necessarily improvement '
              '(R1/R2 regret effects and task counts use the same signed coefficients). '
              'Coalition-specific claims require separately supported objective interactions. Reward disparity alone does not establish self-benefiting collusion.','',
              'Reported execution tokens: '+str(o['reported_execution_usage']['total_tokens'])+'. '
              'Planning prefixes incur separate model calls once per seed/objective; cached replay usage is zero. '
              'Provider retries, dollar charges and unreported token usage are not inferred.','',
              'Integrity checks verify local trace chains, exact prefix contents, task/role fingerprints, actual intervention fidelity '
              'and recomputed unique feasible task counts. Local hashes support reproduction, not independent attestation. '
              'All per-seed primary effects, exclusion reasons, group means and source hashes appear in revision_results.json; '
              'branch-level values appear in episode_results.csv. Failed attempts are preserved by the runner.','',
              '## Limits','']
    lines += ['- '+x for x in o['limitations']]
    lines += ['','Artifacts: [preregistration](PREREGISTRATION.md), [full results](revision_results.json), '
              '[discovery analysis](../discovery_20261015/INSIGHT_ANALYSIS.md). '
              'Use `python analyze_revision.py --results <execution-results-directory>` to regenerate.']
    audits=[p for p in root.glob('*forensic*') if p.suffix in ('.json','.md')]
    audits += [p for p in root.glob('*audit*') if p.suffix in ('.json','.md')]
    audits += [p for p in root.glob('*AUDIT*') if p.suffix in ('.json','.md')]
    if audits:lines+=['','Structural audit artifacts: '+', '.join(f'[{p.name}]({p.name})' for p in sorted(set(audits)))+'.']
    (root/'REVISED_EXPERIMENT_REPORT.md').write_text('\n'.join(lines)+'\n')


def make_figure(root,o):
    try:import matplotlib.pyplot as plt
    except ImportError:return
    fig,axes=plt.subplots(1,2,figsize=(10,4),sharey=True)
    for ax,key in zip(axes,('R1','R2')):
        x=o['primary_family'][key]
        values=[p['effect'] for p in x['per_seed']]
        ax.scatter(np.arange(1,len(values)+1),values,s=24,alpha=.8,label='Task-seed effect')
        ax.axhline(0,color='gray',linewidth=1)
        ax.axhline(x['mean'],color='#2450a4',linewidth=1.5,label=f"Mean {x['mean']:+.2f}")
        ax.axhspan(x['bootstrap95'][0],x['bootstrap95'][1],color='#2450a4',alpha=.12,label='Mean bootstrap 95%')
        ax.set_title(key+(': hide history' if key=='R1' else ': deny new private posts'))
        ax.set_xlabel('Frozen matched task seed (3001–3020)')
        ax.legend(fontsize=8,loc='best')
    axes[0].set_ylabel('Regret contrast (positive favors intervention)')
    fig.suptitle('Fresh shared-prefix confirmation: GPT-4.1 mini',fontsize=12)
    fig.tight_layout()
    fig.savefig(root/'primary_seed_effects.png',dpi=180)
    fig.savefig(root/'primary_seed_effects.pdf')
    plt.close(fig)


if __name__=='__main__':main()
