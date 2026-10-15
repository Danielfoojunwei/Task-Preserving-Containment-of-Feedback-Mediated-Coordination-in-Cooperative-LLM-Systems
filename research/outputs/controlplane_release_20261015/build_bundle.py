"""Release only a complete, audited control-plane dataset; verify archived bytes."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import zipfile

HERE = Path(__file__).resolve().parent
DATASET = HERE.parent/'controlplane_20261015'
TARGET = Path('/workspace/Task-Preserving-Containment-of-Feedback-Mediated-Coordination-in-Cooperative-LLM-Systems/outputs/bundles/task-preserving-research-20261015-controlplane.zip')
PREFIX = 'controlplane_research_20261015/'


def eligible(path):
    return (path.is_file() and not any(x in path.parts for x in ('__pycache__', 'matplotlib_cache', '.pytest_cache'))
            and path.suffix not in ('.pyc', '.tmp', '.lock'))


def main():
    if json.loads((DATASET/'progress.json').read_text())['status'] != 'completed':
        raise RuntimeError('Research is not complete')
    if json.loads((DATASET/'controlplane_results.json').read_text())['status'] != 'COMPLETE':
        raise RuntimeError('Analysis is not complete')
    if json.loads((DATASET/'FINAL_AUDIT.json').read_text())['status'] not in ('PASSED', 'PASSED_COMPLETE'):
        raise RuntimeError('Independent audit has not passed')
    sources = {'controlplane_20261015/'+str(p.relative_to(DATASET)): p
               for p in DATASET.rglob('*') if eligible(p)}
    followup = DATASET.parent/'hostmask_20261015'
    if followup.exists():
        if json.loads((followup/'progress.json').read_text())['status'] != 'completed':
            raise RuntimeError('Host-masked follow-up is not complete')
        if json.loads((followup/'analysis.json').read_text())['status'] != 'COMPLETE_SEPARATE_FOLLOWUP':
            raise RuntimeError('Follow-up analysis is not complete')
        if json.loads((followup/'FINAL_AUDIT.json').read_text())['status'] != 'PASSED_COMPLETE':
            raise RuntimeError('Independent follow-up audit has not passed')
        for path in followup.rglob('*'):
            if eligible(path):
                sources['hostmask_20261015/'+str(path.relative_to(followup))] = path
    for path in HERE.iterdir():
        if eligible(path) and path.name not in ('ARTIFACT_SHA256.json', 'BUNDLE_VERIFICATION.json'):
            sources[path.name] = path
    secret = os.environ.get('OPENROUTER_API_KEY', '').encode()
    records = {}
    for name, path in sorted(sources.items()):
        data = path.read_bytes()
        if secret and secret in data:
            raise RuntimeError('Credential literal found in artifact: '+name)
        records[name] = {'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data)}
    manifest = {'created_at': datetime.now(timezone.utc).isoformat(), 'files': records,
                'manifest_self_hash_excluded': True}
    manifest_path = HERE/'ARTIFACT_SHA256.json'
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True)+'\n')
    if TARGET.exists():
        raise FileExistsError('Refusing to replace a released research archive')
    TARGET.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(TARGET, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for name, path in sorted(sources.items()):
            archive.write(path, PREFIX+name)
        archive.write(manifest_path, PREFIX+'ARTIFACT_SHA256.json')
    with zipfile.ZipFile(TARGET) as archive:
        for name, record in records.items():
            data = archive.read(PREFIX+name)
            if len(data) != record['bytes'] or hashlib.sha256(data).hexdigest() != record['sha256']:
                raise RuntimeError('Archive byte verification failed: '+name)
    value = hashlib.sha256(TARGET.read_bytes()).hexdigest()
    TARGET.with_suffix('.zip.sha256').write_text(value+'  '+TARGET.name+'\n')
    report = {'status': 'VERIFIED', 'archive': str(TARGET), 'archive_sha256': value,
              'verified_files': len(records), 'archive_bytes': TARGET.stat().st_size,
              'current_credential_literal_matches': 0}
    (HERE/'BUNDLE_VERIFICATION.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report))


if __name__ == '__main__':
    main()
