#!/usr/bin/env python3
"""Run the frozen post-behavior evidence pipeline once; explicit paid release.

Waits for the already-started fixed main cohort; never retries or resumes a
failed phase. Research annotations use the same predeclared spending cap.
"""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import time
ROOT=Path(__file__).resolve().parent.parent

def finish():
    while not (ROOT/'main_completion.json').exists():
        if (ROOT/'TRANSPORT_HALT.json').exists():raise RuntimeError('Main dispatch halted; no dependent calls')
        time.sleep(5)
    if json.loads((ROOT/'main_completion.json').read_text()).get('complete') is not True:raise RuntimeError('Main incomplete')
    commands=[('behavior_audit',[ROOT/'independent_verify.py','--phase','behavior','--release']),
        ('initial_annotations',[ROOT/'review.py','initial','--release']),
        ('intent_seal',[ROOT/'review.py','seal','--release']),
        ('public_annotations',[ROOT/'review.py','disclosure','--release']),
        ('all_raw_audit',[ROOT/'independent_verify.py','--phase','all','--release']),
        ('annotation_integrity',[ROOT/'release/verify_annotations.py']),
        ('fixed_analysis',[ROOT/'analyze.py','--release'])]
    for label,args in commands:
        print(json.dumps({'starting':label}),flush=True)
        result=subprocess.run([sys.executable,*map(str,args)],cwd=ROOT.parents[2],text=True,capture_output=True)
        for name,text in (('stdout',result.stdout),('stderr',result.stderr)):
            path=ROOT/'release'/(label+'.'+name+'.log')
            with path.open('x') as f:f.write(text)
        print(json.dumps({'finished':label,'returncode':result.returncode}),flush=True)
        if result.returncode:raise RuntimeError(label+' failed; inspect retained logs. No automatic retry.')
    print(json.dumps({'complete':True,'analysis':str(ROOT/'ANALYSIS.json')}),flush=True)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--release',action='store_true');a=p.parse_args()
    if not a.release:p.error('Explicit --release required; research calls are paid')
    finish()
