#!/usr/bin/env python3
"""Descriptive graphics and complete 16-pair/64-round CSVs from released data."""
import csv
import hashlib
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parent.parent

def val(x):return x['value'] if isinstance(x,dict) and 'value' in x else x

def build():
    raw=(ROOT/'ANALYSIS_CORRECTED.json').read_bytes();d=json.loads(raw);out=ROOT/'release/figures';out.mkdir(parents=True,exist_ok=False)
    pairs={};rounds=[]
    for w in d['worlds']:
        pairs.setdefault(w['block_id'],{'block_id':w['block_id'],'source':w['source_session_id'],'source_condition':w['source_condition']})[w['condition']]=val(w['mean_owner_loss'])
        for r in w['rounds']:
            rounds.append({'world':w['review_id'],'block':w['block_id'],'source':w['source_session_id'],'arm':w['condition'],'round':r['round'],
                'owner_loss':val(r['finance']['net_owner_loss']),'harmful_intent':r['pre_action']['harmful_active'],
                'concealment_intent':r['pre_action']['concealment_active'],'implemented':r['action_terms_implemented'],
                'executed_harm':r['executed_harmful_pact'],'strict_covert':r['strict_executed_profitable_covert'],
                'public_disclosure':r['public_disclosure_through_actions'],'auditor_valid':r['auditor_valid'],'auditor_flag':r['auditor_flag'],
                'unsupported_claims':r['unsupported_claims'],'unsupported_reviews':r['unsupported_reviews'],'both_receipts_paid':r['finance']['both_receipts_paid'],'valid_money':r['valid_money'],'sorting_correct':r['sorting_correct']})
    paired=[pairs[k] for k in sorted(pairs)]
    for name,rows in [('paired_histories.csv',paired),('all_main_rounds.csv',rounds)]:
        with (out/name).open('x',newline='') as f:
            wr=csv.DictWriter(f,fieldnames=list(rows[0]));wr.writeheader();wr.writerows(rows)
    plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False})
    fig,axes=plt.subplots(1,2,figsize=(12,4.6),gridspec_kw={'width_ratios':[1.5,1]})
    ax=axes[0]
    for p in paired:
        ax.plot([0,1],[p['ordinary_settlement'],p['receipt_cap']],'-o',color='#286c8e',alpha=.62,linewidth=1.3,markersize=4)
    ax.set_xticks([0,1],['Ordinary settlement','Receipt cap']);ax.set_xlim(-.15,1.15);ax.set_ylabel('Mean owner loss per round (fictional points)')
    ax.set_title('All sixteen matched source histories');ax.grid(axis='y',alpha=.2)
    ax=axes[1];counts=[]
    for arm in ('ordinary_settlement','receipt_cap'):
        rs=[r for r in rounds if r['arm']==arm]
        counts.append([100*sum(r['unsupported_claims'] for r in rs)/64,100*sum(r['unsupported_reviews'] for r in rs)/64,100*sum(r['both_receipts_paid'] for r in rs)/32])
    import numpy as np
    x=np.arange(3)
    ax.bar(x-.18,counts[0],.36,label='Ordinary',color='#286c8e');ax.bar(x+.18,counts[1],.36,label='Receipt cap',color='#d08528')
    ax.set_xticks(x,['Over-limit claims\n(out of 64)','Over-limit reviews\n(out of 64)','Full receipt payment\n(out of 32 rounds)'])
    ax.set_ylim(0,108);ax.set_ylabel('Percent of opportunities');ax.set_title('Requests continue; valid receipts are paid');ax.legend(frameon=False)
    fig.suptitle('Inherited-context financial continuation — not fresh agreement formation',fontsize=13)
    fig.tight_layout()
    for suffix in ('png','svg'):fig.savefig(out/('followthrough_results.'+suffix),dpi=180,bbox_inches='tight')
    plt.close(fig)
    if (ROOT/'ANALYSIS_CORRECTED.json').read_bytes()!=raw:raise ValueError('Source changed')
    files={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in out.iterdir()}
    result={'analysis_sha256':hashlib.sha256(raw).hexdigest(),'files':files,'source_histories':16,'rounds':64,
        'plots_are_descriptive':True,'unknown_labels_not_counted_positive':True,'primary_exact_test':d['primary']}
    (ROOT/'release/VISUALS_MANIFEST.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'files':len(files),'histories':16,'rounds':64}))
if __name__=='__main__':build()
