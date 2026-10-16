#!/usr/bin/env python3
"""Secret-scanned archive and fresh, network-disabled offline reproduction.

Includes the whole follow-through and transitive frozen dependency closure.
The prior $40.35259 closure is pinned audit/completion evidence, not a new audit
of every original paid call. No credentials or bytecode included. Unpinned runtime locks are excluded; pinned historical empty lockfiles remain to verify the source freeze.
"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys
import tempfile
import zipfile
ROOT=Path(__file__).resolve().parent.parent
REPO=ROOT.parents[2]
EXT=ROOT.relative_to(REPO)
sp=importlib.util.spec_from_file_location('ft_package_base',REPO/'research/outputs/covert_extension_20261016/release/package_extension.py')
B=importlib.util.module_from_spec(sp);sp.loader.exec_module(B)

def inventory():
    paths={p.resolve() for p in ROOT.rglob('*') if p.is_file() and not B.excluded(p.relative_to(ROOT))}
    queue=[ROOT/'FREEZE.json',ROOT/'release/correction/FREEZE.json'];seen=set();pins={}
    while queue:
        p=queue.pop()
        if p in seen:continue
        seen.add(p)
        for name,wanted in B.load(p)['sha256'].items():
            file=B.checked_path(REPO,p.parent.relative_to(REPO)/name)
            if B.sha(file)!=wanted:raise ValueError('Frozen dependency changed')
            paths.add(file);pins[file.relative_to(REPO).as_posix()]=wanted
            if file.name=='FREEZE.json':queue.append(file)
    # Package helper and PDF renderer are reuse dependencies outside the freeze.
    paths.add(REPO/'research/outputs/covert_extension_20261016/release/package_extension.py')
    paths.add(REPO/'research/outputs/overt_covert_release_20261016/render_report.py')
    files={}
    for p in sorted(paths):
        rel=p.relative_to(REPO).as_posix();data=p.read_bytes();B.check_export_content(rel,data)
        files[rel]={'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data)}
    return {'files':files,'pinned':pins,'scope':'Whole follow-through plus frozen source closure; prior cost closure uses certificates.'}

def extract_checked(archive,target):
    target=Path(target);target.mkdir(parents=True,exist_ok=False)
    with zipfile.ZipFile(archive) as z:
        if len(z.namelist())!=len(set(z.namelist())):raise ValueError('Duplicate ZIP entry')
        for entry in z.infolist():
            B.archive_name(entry.filename)
            if entry.is_dir() or not stat.S_ISREG(entry.external_attr>>16):raise ValueError('Nonregular ZIP entry')
            file=target/entry.filename;file.parent.mkdir(parents=True,exist_ok=True)
            with file.open('xb') as f:f.write(z.read(entry))
    manifest=B.load(target/'EXPORT_MANIFEST.json')
    actual={p.relative_to(target).as_posix() for p in target.rglob('*') if p.is_file()}
    if actual!=set(manifest['files'])|{'EXPORT_MANIFEST.json'}:raise ValueError('Unexpected archive file')
    for rel,wanted in manifest['files'].items():
        if B.sha(target/rel)!=wanted['sha256'] or (target/rel).stat().st_size!=wanted['bytes']:raise ValueError('Extracted bytes differ')
    return manifest

def worker(repo,out):
    if not getattr(sys,'_covert_offline_guard',False):raise RuntimeError('Offline network/source guard absent')
    repo=Path(repo);out=Path(out);out.mkdir(parents=True,exist_ok=False)
    study=repo/EXT;checks={}
    commands=[('tests',[sys.executable,'-m','unittest','discover','-s',str(study),'-p','test_*.py']),
        ('schema_tests',[sys.executable,'-m','unittest','discover','-s',str(study/'release'),'-p','test_review_v2.py']),
        ('raw',[sys.executable,str(study/'release/audit_corrected.py'),'--output-dir',str(study/'independent/fresh_offline')]),
        ('annotations',[sys.executable,str(study/'release/verify_corrected_labels.py')]),
        ('analysis',[sys.executable,str(study/'release/analyze_v2.py'),'--release','--output',str(out/'ANALYSIS_CORRECTED.json')]),
        ('independent_primary',[sys.executable,str(study/'release/verify_primary.py'),'--output',str(out/'INDEPENDENT_PRIMARY_CHECK.json')])]

    for name,cmd in commands:
        r=subprocess.run(cmd,cwd=repo,capture_output=True,text=True)
        (out/(name+'.stdout.log')).write_text(r.stdout);(out/(name+'.stderr.log')).write_text(r.stderr)
        if r.returncode:raise RuntimeError('Offline '+name+' failed; inspect retained logs')
        checks[name]=True
    if B.load(out/'ANALYSIS_CORRECTED.json')!=B.load(study/'ANALYSIS_CORRECTED.json'):raise ValueError('Fresh analysis differs')
    raw=B.load(study/'independent/fresh_offline/INDEPENDENT_VERIFICATION_CORRECTED.json')
    if raw.get('passed') is not True:raise ValueError('Fresh raw audit failed')
    result={'passed':True,'network_disabled':True,'all_checks':checks,'analysis_exactly_equal':True,'verified_calls':raw['inventory']['verified_requests']}
    B.write_new(out/'OFFLINE_VERIFICATION.json',result);return result

def build(archive):
    archive=Path(archive).resolve()
    if archive.exists():raise FileExistsError(archive)
    manifest=inventory();archive.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(archive,'x',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for rel,wanted in manifest['files'].items():
            data=(REPO/rel).read_bytes()
            if hashlib.sha256(data).hexdigest()!=wanted['sha256']:raise ValueError('Source changed')
            entry=zipfile.ZipInfo(rel,date_time=(2026,10,16,0,0,0));entry.external_attr=(stat.S_IFREG|0o644)<<16;entry.compress_type=zipfile.ZIP_DEFLATED
            z.writestr(entry,data,compresslevel=9)
        entry=zipfile.ZipInfo('EXPORT_MANIFEST.json',date_time=(2026,10,16,0,0,0));entry.external_attr=(stat.S_IFREG|0o644)<<16;entry.compress_type=zipfile.ZIP_DEFLATED
        z.writestr(entry,json.dumps(manifest,sort_keys=True,indent=2),compresslevel=9)
    if inventory()!=manifest:raise ValueError('Sources changed during archive')
    # Network is blocked by a startup guard; source workspace is forbidden too.
    with tempfile.TemporaryDirectory(prefix='followthrough-offline-') as tmp:
        extracted=Path(tmp)/'repo';extract_checked(archive,extracted)
        out=extracted/'.fresh_offline'
        helper=extracted/EXT/'release/package_followthrough.py'
        env={key:os.environ[key] for key in ('PATH','LANG','LC_ALL','TZ') if key in os.environ}
        env['PYTHONNOUSERSITE']='1';env['PYTHONDONTWRITEBYTECODE']='1';env['COVERT_EXTRACTED_ROOT']=str(extracted)
        guard=Path(tmp)/'guard';guard.mkdir();(guard/'sitecustomize.py').write_text(B.GUARD)
        env['PYTHONPATH']=str(guard);env['COVERT_FORBIDDEN_SOURCE_ROOT']=str(REPO)
        result=subprocess.run([sys.executable,str(helper),'_worker','--repo',str(extracted),'--output',str(out)],cwd=extracted,env=env,capture_output=True,text=True)
        evidence=archive.with_suffix('.zip.offline-verification')
        if evidence.exists():raise FileExistsError(evidence)
        if out.exists():shutil.copytree(out,evidence)
        else:evidence.mkdir()
        (evidence/'worker.stdout.log').write_text(result.stdout);(evidence/'worker.stderr.log').write_text(result.stderr)
        if result.returncode:raise RuntimeError('Fresh extracted reproduction failed')
        verification=B.load(out/'OFFLINE_VERIFICATION.json')
    receipt={'archive':archive.name,'bytes':archive.stat().st_size,'sha256':B.sha(archive),'files':len(manifest['files']),
        'offline_verification':verification}
    B.write_new(archive.with_suffix('.zip.receipt.json'),receipt)
    archive.with_suffix('.zip.sha256').write_text(receipt['sha256']+'  '+archive.name+'\n')
    return receipt
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=('build','_worker'));p.add_argument('--repo',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    print(json.dumps(build(a.output) if a.command=='build' else worker(a.repo,a.output)))
