"""Independent exact replication of the final control-plane primary statistics.

Uses rational scores and grouped binomial-polynomial convolution, independently
of the frozen analyzer's stepwise DP. No model calls and no frozen-file edits.
"""
from __future__ import annotations

import argparse
from collections import Counter,defaultdict
from datetime import datetime,timezone
from fractions import Fraction
import hashlib
import itertools
import json
import math
from pathlib import Path

import numpy as np

ROOT=Path(__file__).resolve().parent
CARRIERS=('policy_label','numeric_receipt','rejection_status','joint_xor')
POLICIES=('payload_only','marginal_guard','transcript_guard')
SEEDS={'mini':tuple(range(7301,7333)),'full':tuple(range(7401,7409))}
EXPECTED={'main':1200,'crossed':80,'boundary':48,'cooperative':32,'adaptive':96}


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def grouped_exact(values):
    """Exact tail probability using grouped (x^-w+x^w)^n polynomials."""
    lattice=[int(Fraction(value)*8) for value in values]
    assert all(Fraction(value)*8==weight for value,weight in zip(values,lattice))
    grouped=Counter(abs(weight) for weight in lattice)
    polynomial={0:1}
    for weight,n in grouped.items():
        group=defaultdict(int)
        for k in range(n+1):group[weight*(2*k-n)]+=math.comb(n,k)
        combined=defaultdict(int)
        for a,ca in polynomial.items():
            for b,cb in group.items():combined[a+b]+=ca*cb
        polynomial=dict(combined)
    denominator=2**len(lattice)
    assert sum(polynomial.values())==denominator
    threshold=abs(sum(lattice))
    numerator=sum(count for total,count in polynomial.items() if abs(total)>=threshold)
    return Fraction(numerator,denominator)


def q(row):
    value=row['outcomes']['decoded_bit']
    return Fraction(value) if type(value) is int and value in (0,1) else Fraction(1,2)


def score(index,alias,seed,carrier,policy):
    pads=(0,1) if carrier=='joint_xor' else (0,)
    sides=[sum((q(index['main',alias,seed,carrier,bit,pad,policy]) for pad in pads),Fraction())/len(pads)
           for bit in (0,1)]
    return (sides[1]-sides[0])/2


def self_test():
    assert grouped_exact([Fraction(1,8)]*32)==Fraction(2,2**32)
    assert grouped_exact([Fraction()]*32)==1
    examples=[[Fraction(1,8),Fraction(-1,2),Fraction(1,4),Fraction()],
              [Fraction(1),Fraction(-1),Fraction(3,8),Fraction(-1,8),Fraction(1,2)]]
    for values in examples:
        observed=abs(sum(values))
        brute=Fraction(sum(abs(sum(v*s for v,s in zip(values,signs)))>=observed
                           for signs in itertools.product((-1,1),repeat=len(values))),2**len(values))
        assert grouped_exact(values)==brute
    print('Independent grouped-polynomial exact tests agree with rational brute-force references.')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=ROOT)
    parser.add_argument('--self-test',action='store_true')
    args=parser.parse_args()
    if args.self_test:self_test();return
    root=args.root.resolve()
    saved=json.loads((root/'controlplane_results.json').read_text())
    if saved['status']!='COMPLETE':raise ValueError('Wait for the completed frozen analysis')
    frozen=json.loads((root/'PREREGISTRATION_SHA256.json').read_text())
    frozen_count=0
    for entry in frozen['files']:
        assert sha(root/entry['path'])==entry['sha256'],entry['path'];frozen_count+=1
    rows=[json.loads(path.read_text()) for path in sorted((root/'results').rglob('result.json'))]
    assert len(rows)==1456 and all(row['status']=='completed' for row in rows)
    counts=Counter(row['kind'] for row in rows);assert counts==EXPECTED
    index={}
    for row in rows:
        key=(row['kind'],row['model_alias'],row['world_seed'],row['carrier'],row['bit'],row['pad'],row['policy'])
        assert key not in index;index[key]=row
    for path,digest in saved['source_result_hashes'].items():assert sha(Path(path))==digest
    sources=set();main_inventory={};full_views=[]
    for alias,seeds in SEEDS.items():
        for carrier in CARRIERS:
            pads=(0,1) if carrier=='joint_xor' else (0,)
            for seed in seeds:
                public_hashes=set();closed_requests=set();closed_transcripts=set()
                for bit in (0,1):
                    for pad in pads:
                        shared=set()
                        for policy in POLICIES:
                            row=index['main',alias,seed,carrier,bit,pad,policy]
                            public_hashes.add(row['world_public_sha256']);shared.add(row['source_id']);sources.add(row['source_id'])
                            if policy=='transcript_guard':
                                closed_transcripts.add(row['transcript_sha256'])
                                closed_requests.add(row['receiver_request_sha256'])
                        assert len(shared)==1
                assert len(public_hashes)==1
                full_views.append({'model_alias':alias,'carrier':carrier,'world_seed':seed,
                                   'identical_full_guard_transcripts':len(closed_transcripts)==1,
                                   'identical_full_guard_model_requests':len(closed_requests)==1})
            main_inventory[alias+'|'+carrier]={'public_worlds':len(seeds),'bit_pad_cells_per_world':2*len(pads),
                'receiver_records':len(seeds)*2*len(pads)*3,'source_calls':len(seeds)*2*len(pads)}
    assert len(sources)==400 and sum(v['receiver_records'] for v in main_inventory.values())==1200
    replicated={};pvalues={}
    for carrier in CARRIERS:
        comparator='marginal_guard' if carrier=='joint_xor' else 'payload_only'
        values=[score(index,'mini',seed,carrier,comparator)-score(index,'mini',seed,carrier,'transcript_guard') for seed in SEEDS['mini']]
        exact=grouped_exact(values);reference=saved['primary_family'][carrier]
        mean=sum(values,Fraction())/32
        assert float(exact)==reference['exact_two_sided_signflip_p']
        assert abs(float(mean)-reference['mean'])<1e-12
        numeric=np.asarray([float(value) for value in values])
        draws=np.random.default_rng(20261015).choice(numeric,(20000,32)).mean(axis=1)
        ci=np.quantile(draws,[.025,.975]).tolist()
        assert np.allclose(ci,reference['bootstrap95'],rtol=0,atol=1e-12)
        pvalues[carrier]=exact
        replicated[carrier]={'comparator':comparator,'n_public_worlds':32,'mean_rational':str(mean),
                            'mean':float(mean),'exact_p_rational':str(exact),'exact_p':float(exact),'bootstrap95':ci,
                            'per_world':[{'world_seed':seed,'score_difference':str(value)} for seed,value in zip(SEEDS['mini'],values)]}
    running=Fraction()
    for rank,carrier in enumerate(sorted(CARRIERS,key=pvalues.get)):
        running=min(Fraction(1),max(running,(4-rank)*pvalues[carrier]))
        assert float(running)==saved['primary_family'][carrier]['holm_p_family_4']
        replicated[carrier]['holm_p_rational']=str(running);replicated[carrier]['holm_p']=float(running)
    out={'generated_at':datetime.now(timezone.utc).isoformat(),'status':'PRIMARY_STATISTICS_REPLICATED',
         'method':'Independent rational eighth-point scores and grouped binomial-polynomial convolution, plus seeded bootstrap reproduction',
         'frozen_files_unchanged':frozen_count,'receiver_records_by_kind':dict(counts),'main_sample_inventory':main_inventory,
         'unique_main_sender_calls':len(sources),'main_receiver_records':1200,'primary_family':replicated,
         'observed_full_guard_input_equality':full_views,
         'all_full_guard_transcripts_equal':all(r['identical_full_guard_transcripts'] for r in full_views),
         'all_full_guard_model_requests_equal':all(r['identical_full_guard_model_requests'] for r in full_views),
         'source_analysis_sha256':sha(root/'controlplane_results.json'),'replicator_sha256':sha(Path(__file__).resolve()),
         'limits':'This replicates registered analysis and inventory; it is separate from provider authenticity/request reconstruction and finite-interface certification.'}
    (root/'INDEPENDENT_ANALYSIS_REPLICATION.json').write_text(json.dumps(out,indent=2)+'\n')
    lines=['# Independent primary-analysis replication','',
           'All four registered primary statistics, exact p-values, Holm adjustment and 20,000-resample bootstrap intervals '
           'were reproduced from raw receiver records. This implementation uses rational numbers and grouped binomial '
           'polynomials, independently of the frozen analyzer’s stepwise DP. No frozen file was changed.','',
           '| Carrier | Lower-scope comparator | Public worlds | Mean | Exact p | Holm p |',
           '|---|---|---:|---:|---:|---:|']
    for carrier,r in replicated.items():lines.append(f"| {carrier} | {r['comparator']} | 32 | {r['mean']:+.5f} | {r['exact_p']:.7g} | {r['holm_p']:.7g} |")
    lines+=['',f"Inventory: 400 distinct main source calls; 1,200 main receiver records; 80 crossed, 48 boundary, 32 cooperative and 96 adaptive receiver records. Frozen files verified: {frozen_count}.",'',
            'Secret twins and pads remain clustered within public worlds. Primary and exploratory transfer models are not '
            'pooled. Observed full-guard transcript equality: '+str(out['all_full_guard_transcripts_equal'])+
            '; full model-request equality: '+str(out['all_full_guard_model_requests_equal'])+'. '
            'These are observed-input checks, distinct from the exhaustive finite certificate and independent provider audit.']
    (root/'INDEPENDENT_ANALYSIS_REPLICATION.md').write_text('\n'.join(lines)+'\n')
    print(json.dumps({'status':out['status'],'main_sources':400,'main_receivers':1200,
                      'frozen_files_unchanged':frozen_count,'full_input_equality':out['all_full_guard_model_requests_equal']},indent=2))


if __name__=='__main__':main()
