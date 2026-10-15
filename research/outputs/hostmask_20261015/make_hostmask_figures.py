"""Standalone host-masked follow-up figure; uses completed saved analyses only."""
import hashlib
import json
import os
from pathlib import Path

os.environ.setdefault('MPLCONFIGDIR','/tmp/hostmask-matplotlib')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

ROOT=Path(__file__).resolve().parent
POLICIES=['payload_only','marginal_guard','transcript_guard']
LABELS=['Payload\nonly','Marginal\nguard','Transcript\nguard']
COLORS={'mini':'#285c7c','full':'#a74d29'}


def ci_error(summary):
    mean=summary['mean']; low,high=summary['bootstrap95']
    return np.array([[mean-low],[high-mean]])


def main():
    frozen_path=ROOT/'analysis.json'; replication_path=ROOT/'INDEPENDENT_REPLICATION.json'
    analysis=json.loads(frozen_path.read_text()); replica=json.loads(replication_path.read_text())
    assert analysis['status']=='COMPLETE_SEPARATE_FOLLOWUP'
    assert replica['status']=='PASSED_INDEPENDENT_REPLICATION'
    fig,axes=plt.subplots(2,3,figsize=(16,9.4))
    fig.subplots_adjust(left=.07,right=.98,bottom=.12,top=.88,wspace=.34,hspace=.54)

    ax=axes[0,0]
    for y,alias in [(1,'mini'),(0,'full')]:
        effect=replica['models'][alias]['effect']
        ax.errorbar(effect['mean'],y,xerr=ci_error(effect),fmt='o',color=COLORS[alias],capsize=5,markersize=8)
    ax.axvline(0,color='gray',ls='--',lw=1)
    ax.set_yticks([1,0],['GPT-4.1 mini\n16 worlds, primary','GPT-4.1\n8 worlds, exploratory'])
    ax.set_ylim(-.65,1.65);ax.set_xlim(-.01,.55)
    ax.set_xlabel('Marginal guard − transcript guard: ΔS')
    ax.set_title('A  Registered decoding contrast',loc='left',fontweight='bold')
    ax.text(.03,.02,'Mini exact two-sided p = 0.0000610\n95% world-bootstrap intervals',transform=ax.transAxes,fontsize=9,color='#515d65')
    ax.grid(axis='x',alpha=.15)

    ax=axes[0,1]
    matrix=[]
    for policy in POLICIES:
        bank=[row for row in replica['actual_view_TVs'] if row['policy']==policy]
        values=[[row[k] for k in ('label_TV','receipt_TV','joint_TV')] for row in bank]
        assert all(v==values[0] for v in values)
        matrix.append(values[0])
    ax.imshow(matrix,vmin=0,vmax=1,cmap='Blues',aspect='auto')
    for row in range(3):
        for col in range(3):
            value=matrix[row][col];ax.text(col,row,f'{value:g}',ha='center',va='center',color='white' if value else '#243b4b',fontsize=14)
    ax.set_xticks(range(3),['Label TV','Receipt TV','Joint TV'])
    ax.set_yticks(range(3),['Payload only','Marginal guard','Transcript guard'])
    ax.set_title('B  Actual source banks: all 24 worlds',loc='left',fontweight='bold')
    ax.set_xlabel('Both fields individually hidden; joint retained\n48/48 actual source bits copied correctly')

    ax=axes[0,2]
    x=np.arange(3); width=.32
    for offset,alias in [(-width/2,'mini'),(width/2,'full')]:
        groups=replica['models'][alias]['policies']
        vals=[groups[p]['complete_public_task_success']/groups[p]['n_receiver_records'] for p in POLICIES]
        bars=ax.bar(x+offset,vals,width,color=COLORS[alias],label='Mini' if alias=='mini' else 'Full')
        for bar,p in zip(bars,POLICIES):
            row=groups[p];ax.text(bar.get_x()+bar.get_width()/2,1.025,f"{row['complete_public_task_success']}/{row['n_receiver_records']}",ha='center',fontsize=8)
    ax.set_xticks(x,LABELS);ax.set_ylim(0,1.2);ax.set_yticks([0,.5,1],['0%','50%','100%'])
    ax.set_ylabel('Actual complete public task success')
    ax.set_title('C  Copy supplied schedule + checksum',loc='left',fontweight='bold')
    ax.legend(frameon=False,loc='lower right',fontsize=9)

    for ax,metric,title,ylabel in [
        (axes[1,0],'profitable_harm','D  Correct accepted bets harming owner','Fraction of receiver calls'),
        (axes[1,1],'coalition_payoff','E  Accepted coalition net payoff','Mean payoff per receiver call')]:
        for offset,alias in [(-width/2,'mini'),(width/2,'full')]:
            stats=[replica['models'][alias]['policies'][p]['world_metrics'][metric] for p in POLICIES]
            means=np.array([s['mean'] for s in stats]);low=np.array([s['bootstrap95'][0] for s in stats]);high=np.array([s['bootstrap95'][1] for s in stats])
            ax.bar(x+offset,means,width,color=COLORS[alias],label='Mini: 16 worlds' if alias=='mini' else 'Full: 8 worlds')
            ax.errorbar(x+offset,means,yerr=[means-low,high-means],fmt='none',ecolor='#2d3439',capsize=3,lw=1)
        ax.axhline(0,color='gray',lw=.8);ax.set_xticks(x,LABELS);ax.set_ylabel(ylabel)
        ax.set_title(title,loc='left',fontweight='bold');ax.grid(axis='y',alpha=.13)
        if metric=='profitable_harm':ax.set_ylim(0,.9)
        else:ax.legend(frameon=False,loc='upper right',fontsize=8)

    ax=axes[1,2]
    for y,key,label in [(1,'prediction','Decoded bit'),(0,'accepted_action','Accepted route')]:
        stats=replica['crossed_replay'][key]
        ax.errorbar(stats['mean'],y,xerr=ci_error(stats),fmt='o',color=COLORS['mini'],capsize=5)
    ax.axvline(0,color='gray',ls='--',lw=1);ax.set_ylim(-.65,1.65);ax.set_xlim(-.03,.68)
    ax.set_yticks([1,0],['Decoded bit','Accepted route'])
    ax.set_xlabel('Original − opposite-bit source: ΔS')
    ax.set_title('F  Crossed source replay: exploratory',loc='left',fontweight='bold')
    ax.text(.03,.02,'32 crossed receiver calls; 8 mini worlds\n95% paired-world bootstrap intervals',transform=ax.transAxes,fontsize=9,color='#515d65')
    ax.grid(axis='x',alpha=.15)

    fig.suptitle('Host-balanced control fields: joint decoding persists after marginal screening',
                 fontsize=19,fontweight='bold',y=.97)
    fig.text(.07,.915,'Separate prospective follow-up after the earlier four null primary tests; all source outcomes retained.',fontsize=11,color='#515d65')
    fig.text(.07,.025,'Only mini ΔS is confirmatory. Transfer, betting, payoff, task success and crossed replay are exploratory.\n'
             'Known XOR construction, explicit public decoder tables, and a supplied-value copying task; no claim of a new theorem or spontaneous collusion.',
             fontsize=10,color='#515d65')
    for extension in ('png','pdf'):
        fig.savefig(ROOT/f'host_masked_composition.{extension}',dpi=220,bbox_inches='tight')
    plt.close(fig)
    provenance={'status':'COMPLETED_FOLLOWUP_FIGURE','frozen_analysis_sha256':hashlib.sha256(frozen_path.read_bytes()).hexdigest(),
                'independent_replication_sha256':hashlib.sha256(replication_path.read_bytes()).hexdigest(),
                'renderer_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                'caption':'One registered mini decoding contrast (N16), exploratory full-model validation (N8), exact realized finite-bank field/joint TV, actual complete public-copy success, accepted correct harmful bets and net coalition payoff, and opposite-bit source replay (32 calls, eight mini worlds). Error bars cluster full public worlds with the preregistered 20,000-resample method. Individual marginals are hidden by host balance for any realized source map; actual joint capacity also depends on source copying. All48 copies happened to be correct. Accepted routes are host-accepted actions, not rejected raw proposals. The entire study is separate from the earlier null primary family.'}
    (ROOT/'HOSTMASK_FIGURE_PROVENANCE.json').write_text(json.dumps(provenance,indent=2)+'\n')
    print('Rendered host_masked_composition.png and .pdf from independently verified completed data.')


if __name__=='__main__':main()
