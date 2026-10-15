"""Wait for bounded batches, export reproducible report and archive all evidence."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time
import zipfile

ROOT=Path(__file__).resolve().parent
PY='/workspace/colosseum/.venv/bin/python'
ENV=os.environ.copy();ENV.update(MPLCONFIGDIR='/workspace/.cache/matplotlib',XDG_CACHE_HOME='/workspace/.cache')
ENV['PYTHONPATH']=f'{ROOT.parent.parent}:/workspace/colosseum'
start=time.monotonic()
while True:
    main=json.loads((ROOT/'progress.json').read_text())
    follow=json.loads((ROOT/'followup_progress.json').read_text())
    recovery=json.loads((ROOT/'recovery_progress.json').read_text()) if (ROOT/'recovery_progress.json').exists() else {}
    if main['status']!='running' and follow['status']!='running' and recovery.get('status')!='running': break
    if time.monotonic()-start>7200: raise RuntimeError('Bounded wait expired')
    time.sleep(5)
for key,entry in main.get('runs',{}).items():
    result=ROOT/'results'/key/'ka_result.json'
    if result.exists() and json.loads(result.read_text()).get('status')=='completed' and 'failed' in entry['status']:
        entry['status']='recovered_isolated'
for key,status in list(follow.get('h5',{}).items()):
    result=ROOT/'h5_extension'/key/'extension_result.json'
    if result.exists() and json.loads(result.read_text()).get('status')=='completed' and 'failed' in status:
        follow['h5'][key]='recovered_isolated'
(ROOT/'progress.json').write_text(json.dumps(main,indent=2)+'\n')
(ROOT/'followup_progress.json').write_text(json.dumps(follow,indent=2)+'\n')
for name,manifest in [('development',ROOT/'development_peer_manifest.json'),
                      ('pilot_and_peer_ablation',ROOT/'research_overlay/configs/peer_ablation_manifest.json'),
                      ('heldout_controllers',ROOT/'heldout_full_manifest.json')]:
    with (ROOT/f'analysis_{name}.log').open('w') as log:
        subprocess.run([PY,'-m','kinetic_audit.analyze','--manifest',str(manifest),
            '--results',str(ROOT/'results'),'--out',str(ROOT/f'analysis_{name}.json')],
            env=ENV,stdout=log,stderr=log,check=True)
for script in ['report.py','make_figures.py']:
    subprocess.run([PY,str(ROOT/script)],env=ENV,check=True)

# Manifest excludes archives and its own file; never collects process environments.
manifest={}
for p in sorted(ROOT.rglob('*')):
    if p.is_file() and p.name not in ['ARTIFACT_SHA256.json','FINAL_STATUS.json'] and '__pycache__' not in p.parts and not (p.name.startswith('finalize') and p.suffix=='.log'):
        manifest[str(p.relative_to(ROOT))]=hashlib.sha256(p.read_bytes()).hexdigest()
for link in (ROOT/'results').iterdir():
    if link.is_symlink() and link.is_dir():
        for p in link.rglob('*'):
            if p.is_file(): manifest[str(p.relative_to(ROOT))]=hashlib.sha256(p.read_bytes()).hexdigest()
(ROOT/'ARTIFACT_SHA256.json').write_text(json.dumps(manifest,indent=2)+'\n')
bundle=ROOT.parent/'paper-experiments-20261015.zip'
with zipfile.ZipFile(bundle,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    for name in [*manifest,'ARTIFACT_SHA256.json']:
        z.write(ROOT/name,arcname='paper_20261015/'+name)
summary=json.loads((ROOT/'paper_results.json').read_text())
status={'status':'finished','main_completed':summary['completed_core_episodes'],
        'main_planned':320,'h5_completed':summary['h5']['completed'],'h5_planned':40,
        'h1_calls':summary['h1']['calls'],'h1_failures':summary['h1']['failed'],
        'bundle':str(bundle),'bundle_sha256':hashlib.sha256(bundle.read_bytes()).hexdigest()}
(ROOT/'FINAL_STATUS.json').write_text(json.dumps(status,indent=2)+'\n')
print(json.dumps(status),flush=True)
