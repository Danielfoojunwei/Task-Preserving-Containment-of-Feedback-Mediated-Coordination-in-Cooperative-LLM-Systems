"""Publication figures from completed frozen analyses; no statistical refitting.

Run only after scenario_results.json has status COMPLETE. This renderer reads
the saved estimates and intervals, retains domain-specific harm units, and
never changes frozen analysis code or the inference family.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path

ROOT=Path(__file__).resolve().parent
DOMAINS=('procurement','review_trading','resource_allocation','typed_shared_artifact')
NAMES={'procurement':'Procurement','review_trading':'Review trading',
       'resource_allocation':'Resource allocation','typed_shared_artifact':'Typed shared artifact'}
UNITS={'procurement':'Buyer-utility shortfall units','review_trading':'Merit shortfall units',
       'resource_allocation':'Realized-value / penalty units','typed_shared_artifact':'Task-utility shortfall units'}
BLUE='#285b8e'
ORANGE='#a84e25'
GRAY='#6b7280'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source(path):
    value=json.loads(path.read_text())
    if value['status']!='COMPLETE':
        raise ValueError(f'Wait for the final frozen analysis: {path} has status {value["status"]}')
    return value


def save(fig,directory,stem):
    fig.savefig(directory/(stem+'.png'),dpi=240,bbox_inches='tight',facecolor='white')
    fig.savefig(directory/(stem+'.pdf'),bbox_inches='tight',facecolor='white')


def interval_label(value):
    return f"{value['mean']:+.2f} [{value['bootstrap95'][0]:+.2f}, {value['bootstrap95'][1]:+.2f}]"


def domain_harm(plt,np,data,directory):
    fig,axes=plt.subplots(2,2,figsize=(10,6.8))
    for ax,domain in zip(axes.flat,DOMAINS):
        effect=data['primary_family'][domain]
        assert effect['n']==10
        values=np.asarray([r['effect'] for r in effect['per_seed']])
        low,high=effect['bootstrap95'];mean=effect['mean']
        ax.axvline(0,color=GRAY,linewidth=1,linestyle='--',zorder=0)
        ax.scatter(values,np.linspace(-.14,.14,len(values)),s=25,color=BLUE,alpha=.65,
                   edgecolors='white',linewidth=.4,label='10 paired task seeds',zorder=2)
        ax.errorbar(mean,.48,xerr=[[mean-low],[high-mean]],fmt='D',color=BLUE,
                    ecolor=BLUE,capsize=5,markersize=7,linewidth=2,label='Mean and bootstrap 95%',zorder=3)
        ax.set_title(NAMES[domain],loc='left',fontweight='bold')
        ax.text(.99,.94,f"Holm p = {effect['holm_p_family_4']:.4g}",transform=ax.transAxes,
                ha='right',va='top',fontsize=9,color=GRAY)
        ax.text(.99,.82,interval_label(effect),transform=ax.transAxes,ha='right',va='top',fontsize=9)
        ax.set_xlabel('Baseline − action-guard harm\n'+UNITS[domain])
        ax.set_yticks([0,.48],['Seed effects','Paired mean'])
        ax.set_ylim(-.3,.86)
        ax.grid(axis='x',alpha=.18)
        ax.spines[['top','right']].set_visible(False)
    fig.suptitle('Held-out action-guard effects',fontsize=14,fontweight='bold',y=1.015)
    fig.text(.5,-.035,'Positive effects favor the guard. Harm units are kept separate by domain. '
             'Bootstrap intervals are descriptive; four primary tests use Holm correction.',
             ha='center',fontsize=9,color=GRAY)
    fig.tight_layout(h_pad=2.5,w_pad=2.)
    save(fig,directory,'domain_harm_effects')
    plt.close(fig)


def task_preservation(plt,np,data,directory):
    fig,axes=plt.subplots(1,2,figsize=(11,4.8),sharey=True)
    settings=[('normalized_utility_loss',2.,'Cooperative utility loss\n(% of fixed public scale)'),
              ('coverage_decline',5.,'Cooperative coverage decline\n(percentage points)')]
    for ax,(metric,threshold,label) in zip(axes,settings):
        lows=[];highs=[]
        for y,domain in enumerate(DOMAINS):
            value=data['action_guard_qualifications'][domain][metric]
            assert value['n']==10
            mean=100*value['mean'];low,high=[100*x for x in value['bootstrap95']]
            color=BLUE if mean<=threshold else ORANGE
            ax.errorbar(mean,y,xerr=[[mean-low],[high-mean]],fmt='o',color=color,
                        capsize=5,markersize=7,linewidth=1.8)
            lows.append(low);highs.append(high)
        margin=max(1.,.12*(max(highs+[threshold])-min(lows+[0.])))
        ax.set_xlim(min(lows+[0.,threshold])-margin,max(highs+[0.,threshold])+margin)
        ax.axvline(0,color=GRAY,linewidth=.8,alpha=.6)
        ax.axvline(threshold,color=ORANGE,linewidth=1.3,linestyle='--',
                   label=f'Frozen point threshold: {threshold:g}')
        ax.set_xlabel(label)
        ax.set_yticks(range(len(DOMAINS)),[NAMES[d] for d in DOMAINS])
        ax.grid(axis='x',alpha=.15)
        ax.spines[['top','right']].set_visible(False)
        ax.legend(fontsize=8,loc='best',frameon=False)
    axes[0].invert_yaxis()
    fig.suptitle('Task preservation under the action guard',fontsize=14,fontweight='bold')
    fig.text(.5,-.035,'Points: paired mean; bars: descriptive bootstrap 95%. '
             'Blue means meet the point limit; orange means exceed it.\n'
             'Interval upper bounds are a stricter sensitivity check. Ten seeds do not establish powered noninferiority.',
             ha='center',fontsize=9,color=GRAY)
    fig.tight_layout(w_pad=2.)
    save(fig,directory,'cooperative_task_preservation')
    plt.close(fig)


def context_mechanism(plt,np,data,directory):
    fig,axes=plt.subplots(1,2,figsize=(10,4.2),sharex=True)
    titles={'R1':'Hide old private history\nNew private posts denied',
            'R2':'Deny new private posts\nOld private history visible'}
    for ax,key in zip(axes,('R1','R2')):
        value=data['primary_family'][key]
        assert value['n']==20
        points=np.asarray([x['effect'] for x in value['per_seed']])
        mean=value['mean'];low,high=value['bootstrap95']
        ax.axvline(0,color=GRAY,linestyle='--',linewidth=1,zorder=0)
        ax.scatter(points,np.linspace(-.16,.16,len(points)),s=23,color=BLUE,alpha=.65,
                   edgecolors='white',linewidth=.4,zorder=2)
        ax.errorbar(mean,.5,xerr=[[mean-low],[high-mean]],fmt='D',markersize=7,
                    color=BLUE,capsize=5,linewidth=2,zorder=3)
        ax.set_title(key+': '+titles[key],loc='left',fontweight='bold',fontsize=11)
        ax.set_yticks([0,.5],['20 seed effects','Paired mean'])
        ax.set_ylim(-.3,.9)
        ax.text(.98,.94,f"Holm p = {value['holm_p_family_2']:.5g}",transform=ax.transAxes,
                ha='right',va='top',fontsize=9,color=GRAY)
        ax.set_xlabel('Native welfare-regret reduction\n(positive favors intervention)')
        ax.grid(axis='x',alpha=.15)
        ax.spines[['top','right']].set_visible(False)
    fig.suptitle('Earlier shared-prefix mechanism test',fontsize=14,fontweight='bold',y=1.02)
    fig.text(.5,-.04,'Separate experiment: GPT-4.1 mini, 20 fresh task seeds, two frozen primary tests. '
             'Bars show descriptive seed-bootstrap 95% intervals.',ha='center',fontsize=9,color=GRAY)
    fig.tight_layout(w_pad=2.)
    save(fig,directory,'context_history_and_permission')
    plt.close(fig)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--scenario-results',type=Path,default=ROOT/'scenario_results.json')
    parser.add_argument('--revision-results',type=Path,default=ROOT.parent/'revision_20261015/revision_results.json')
    parser.add_argument('--out',type=Path,default=ROOT/'figures')
    args=parser.parse_args()
    scenarios=source(args.scenario_results)
    revision=source(args.revision_results)
    args.out.mkdir(parents=True,exist_ok=True)
    cache=args.out/'matplotlib_cache';cache.mkdir(exist_ok=True)
    os.environ.setdefault('MPLCONFIGDIR',str(cache))
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import numpy as np
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.titlesize':11,
                         'axes.labelsize':10,'pdf.fonttype':42,'ps.fonttype':42,
                         'figure.facecolor':'white','savefig.facecolor':'white'})
    domain_harm(plt,np,scenarios,args.out)
    task_preservation(plt,np,scenarios,args.out)
    context_mechanism(plt,np,revision,args.out)
    captions=[
        '# Figure captions and provenance','',
        '**domain_harm_effects.** Four separately scaled panels report the held-out paired difference in coalition-condition '
        'native primary harm, baseline minus action guard, on task seeds 6101–6110. Diamonds and horizontal bars show the saved '
        'paired mean and descriptive 20,000-resample seed-bootstrap 95% interval; small circles show all ten task-seed effects. '
        'Positive effects favor the action guard. Exact two-sided sign-flip primary tests use Holm correction across four domains. '
        'Native harm units are not pooled across domains. A harm reduction alone does not establish coalition specificity or task preservation.','',
        '**cooperative_task_preservation.** Cooperative-condition action-guard costs on the same ten held-out task seeds. '
        'Utility losses use paired baseline-minus-guard utility divided by the fixed public domain scales 100, 1, 320 and 24; '
        'coverage differences use each domain’s preregistered coverage definition. Points and horizontal bars show saved means '
        'and descriptive bootstrap 95% intervals. Dashed limits are the frozen point thresholds: 2% utility loss and five percentage '
        'points coverage decline. Negative values denote improvement. Blue points satisfy the corresponding mean limit; orange '
        'points exceed it. The upper interval limits provide the stricter sensitivity check. This is not a powered noninferiority test.','',
        '**context_history_and_permission.** A separate prior experiment replays 40 actual planning prefixes across 160 execution '
        'branches. R1 compares visible versus hidden historical private planning messages with new private posting denied; '
        'R2 compares new private posting allowed versus denied with historical messages visible. All twenty seed effects are shown '
        'with their saved paired means and descriptive bootstrap 95% intervals. Exact two-sided sign-flip tests use Holm correction '
        'across these two frozen endpoints. This experiment is not pooled into the expanded four-domain tests.','',
        '**Architectural qualification.** The post-freeze audit found a residual numeric validity receipt from a hidden later editor '
        'attestation in the typed-artifact domain. Baseline and action_guard retain this receipt; information_guard removes it. '
        'The main frozen effects include that residual path and cannot establish all-channel containment. The optional unsafe selector '
        'live arm is not isolated to policy-label disclosure; complete delivered inputs must be checked before attributing recovery '
        'to any channel. The separate label-only and receipt certificates are non-LLM capability results. See DEVIATIONS.md and '
        'receipt_channel_certificate.json.','',
        'Figures are rendered from saved final estimates without refitting tests, selecting subgroups or changing the frozen analyzers.'
    ]
    (args.out/'FIGURE_CAPTIONS.md').write_text('\n'.join(captions)+'\n')
    provenance={'generated_at':datetime.now(timezone.utc).isoformat(),
                'scenario_results':{'path':str(args.scenario_results),'sha256':digest(args.scenario_results)},
                'revision_results':{'path':str(args.revision_results),'sha256':digest(args.revision_results)},
                'renderer_sha256':digest(Path(__file__).resolve()),
                'figures':{p.name:digest(p) for p in sorted(args.out.iterdir()) if p.suffix in ('.png','.pdf')},
                'saved_scenario_primary_family':scenarios['primary_family'],
                'saved_task_preservation':scenarios['action_guard_qualifications'],
                'saved_revision_primary_family':revision['primary_family']}
    (args.out/'FIGURE_PROVENANCE.json').write_text(json.dumps(provenance,indent=2,allow_nan=False)+'\n')
    print(json.dumps({'status':'FIGURES_COMPLETE','output_directory':str(args.out),
                      'artifacts':list(provenance['figures'])},indent=2))


if __name__=='__main__':main()
