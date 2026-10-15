"""Evidence-type-aware analysis. Missing/failed episodes are never coded as zero."""
from __future__ import annotations
import argparse
import json
import random
from pathlib import Path
from statistics import mean
from .core import Cell, finite_number
from .design import validate_manifest


def paired_feedback_effect(records, *, objective, revoke, bootstrap_draws=5000, seed=42):
    groups={}
    for r in records:
        c=Cell(**r["cell"])
        if c.objective!=objective or c.revoke!=revoke or c.controller!="fixed":continue
        if r.get("status")!="completed" or r.get("evidence_type")!="LIVE_LLM":continue
        groups.setdefault(c.task_seed,{})[c.feedback]=r
    pairs=[];excluded=[]
    for seed_id,g in sorted(groups.items()):
        if not {"original","suppress_score"}.issubset(g):
            excluded.append({"seed":seed_id,"reason":"missing_or_failed_pair"});continue
        a,b=g["original"],g["suppress_score"]
        if not a.get("task_digest") or a["task_digest"]!=b.get("task_digest"):
            raise ValueError("Paired task truth differs; cannot interpret comparison")
        effect=finite_number(a["welfare_regret_exact"])-finite_number(b["welfare_regret_exact"])
        pairs.append((seed_id,effect))
    if not pairs:return {"status":"NO_VALID_LIVE_PAIRS","paired_seeds":0,"excluded":excluded}
    values=[p[1] for p in pairs];rng=random.Random(seed);n=len(values)
    samples=sorted(mean(rng.choices(values,k=n)) for _ in range(bootstrap_draws)) if n>=2 else []
    ci=[samples[int(.025*(bootstrap_draws-1))],samples[int(.975*(bootstrap_draws-1))]] if samples else None
    return {"status":"EXPLORATORY_PAIRED_RESULT","paired_seeds":n,"mean_regret_reduction":mean(values),
            "bootstrap95":ci,"per_seed":pairs,"excluded":excluded,
            "warning":"Seed-cluster bootstrap; tiny pilot is not a safety certificate or proof of intent."}

def main():
    p=argparse.ArgumentParser();p.add_argument("--manifest",type=Path,required=True)
    p.add_argument("--results",type=Path,required=True);p.add_argument("--out",type=Path,required=True)
    a=p.parse_args();cells=validate_manifest(json.loads(a.manifest.read_text()));records=[];missing=[]
    for c in cells:
        path=a.results/c.key/"ka_result.json"
        if path.exists():records.append(json.loads(path.read_text()))
        else:missing.append(c.key)
    result={"planned":len(cells),"records_found":len(records),"missing":missing,
            "failed":sum(r.get("status")!="completed" for r in records),
            "live_completed":sum(r.get("evidence_type")=="LIVE_LLM" and r.get("status")=="completed" for r in records),
            "comparisons":{f"{z}_revoke{int(c)}":paired_feedback_effect(records,objective=z,revoke=c)
                           for z in ["cooperative","coalition"] for c in [False,True]}}
    result["objective_interaction_after_revocation"] = paired_objective_interaction(records)
    a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps(result,indent=2))


def paired_objective_interaction(records, *, revoke=True, bootstrap_draws=5000, rng_seed=43):
    """Difference of feedback effects within the same task-seed block.

    No mediator/intent claim: this is a randomized assigned-objective interaction.
    """
    blocks={}
    for r in records:
        c=Cell(**r['cell'])
        if c.revoke!=revoke or c.controller!='fixed' or c.feedback not in {'original','suppress_score'}:continue
        if r.get('status')!='completed' or r.get('evidence_type')!='LIVE_LLM':continue
        blocks.setdefault(c.task_seed,{})[(c.objective,c.feedback)]=r
    expected={('cooperative','original'),('cooperative','suppress_score'),
              ('coalition','original'),('coalition','suppress_score')}
    differences=[]
    for s,b in sorted(blocks.items()):
        if not expected.issubset(b):continue
        digests={r.get('task_digest') for r in b.values()}
        if len(digests)!=1 or None in digests:raise ValueError('Task blocks differ across objectives')
        d={z:finite_number(b[(z,'original')]['welfare_regret_exact'])-
             finite_number(b[(z,'suppress_score')]['welfare_regret_exact'])
           for z in ['cooperative','coalition']}
        differences.append((s,d['coalition']-d['cooperative']))
    if not differences:return {'status':'NO_VALID_LIVE_BLOCKS','task_blocks':0}
    vals=[v for _,v in differences];n=len(vals);rng=random.Random(rng_seed)
    boots=sorted(mean(rng.choices(vals,k=n)) for _ in range(bootstrap_draws)) if n>=2 else []
    return {'status':'EXPLORATORY_OBJECTIVE_INTERACTION','task_blocks':n,
            'mean_interaction':mean(vals),'per_seed':differences,
            'bootstrap95':([boots[int(.025*(bootstrap_draws-1))],boots[int(.975*(bootstrap_draws-1))]] if boots else None),
            'warning':'Assigned-objective interaction, not malicious intent or mediation proof.'}

if __name__=="__main__":main()
