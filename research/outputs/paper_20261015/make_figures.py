"""Standalone paper figures from reported outcomes only."""
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parent
d=json.loads((ROOT/'paper_results.json').read_text())
plt.rcParams.update({'font.size':10,'savefig.bbox':'tight','pdf.fonttype':42})
fig,axes=plt.subplots(1,2,figsize=(11,5),sharex=True)
for ax,z in zip(axes,['cooperative','coalition']):
    groups=d['summary']['heldout']['groups']
    wanted=[(f'{z} | revoke={r} | {f}',f'{"Revoked" if r else "Available"} / {f}')
            for r in [False,True] for f in ['original','suppress_score']]
    wanted += [(f'{z} | revoke=True | {c}',f'Revoked / {c}') for c in ['history_rule','memoryless_rule']]
    for i,(key,label) in enumerate(wanted):
        if key not in groups: continue
        stat=groups[key]['regret'];v=stat['mean'];ci=stat['bootstrap95']
        ax.errorbar(v,i,xerr=[[max(0,v-ci[0])],[max(0,ci[1]-v)]] if ci else None,fmt='o',color='#1b5d85',capsize=3)
    ax.set_yticks(range(len(wanted)),[label for _,label in wanted]);ax.invert_yaxis()
    ax.set_title(z.capitalize());ax.set_xlabel('Exact welfare regret (lower is better)')
    ax.grid(axis='x',alpha=.25);ax.spines[['top','right']].set_visible(False)
fig.suptitle('Held-out Jira outcomes: mean and 95% task-seed bootstrap interval')
fig.tight_layout()
for ext in ['png','pdf']:fig.savefig(ROOT/f'heldout_regret.{ext}',dpi=180)
plt.close(fig)

fig,ax=plt.subplots(figsize=(8,3.5))
effects=d['h5']['effects'];labels=[]
for i,(key,stat) in enumerate(effects.items()):
    labels.append(key.removesuffix('_regret_reduction_when_public_allowed').replace('_',' '))
    if stat['mean'] is None:continue
    v=stat['mean'];ci=stat['bootstrap95']
    ax.errorbar(v,i,xerr=[[max(0,v-ci[0])],[max(0,ci[1]-v)]] if ci else None,fmt='o',color='#9b4c13',capsize=3)
ax.set_yticks(range(len(labels)),labels);ax.invert_yaxis();ax.axvline(0,color='gray',linewidth=1)
ax.set_xlabel('Fresh-round regret reduction with public messages allowed')
ax.set_title('Exploratory fresh-task extension (95% task-seed bootstrap intervals)')
ax.spines[['top','right']].set_visible(False);fig.tight_layout()
for ext in ['png','pdf']:fig.savefig(ROOT/f'fresh_task_effect.{ext}',dpi=180)
plt.close(fig)
