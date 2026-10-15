"""Package completed evidence and verify every archived source byte."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import zipfile

HERE = Path(__file__).resolve().parent
OUTPUTS = HERE.parent
OVERLAY = OUTPUTS.parent
TARGET = Path('/workspace/Task-Preserving-Containment-of-Feedback-Mediated-Coordination-in-Cooperative-LLM-Systems/outputs/bundles/task-preserving-research-20261015-expanded.zip')
PREFIX = 'research_extension_20261015/'


def eligible(path):
    return path.is_file() and '__pycache__' not in path.parts and path.suffix not in ('.pyc', '.tmp')


def main():
    for name in ('multiscenario_20261015', 'multiscenario_joint_20261015'):
        if json.loads((OUTPUTS/name/'progress.json').read_text())['status'] != 'completed':
            raise RuntimeError('Refusing to package an unfinished live study')
    files = {}
    for name in ('revision_20261015', 'multiscenario_20261015',
                 'multiscenario_joint_20261015', 'discovery_20261015'):
        for path in (OUTPUTS/name).rglob('*'):
            if eligible(path):
                files[str(Path(name)/path.relative_to(OUTPUTS/name))] = path
    for path in HERE.iterdir():
        if eligible(path) and path.name not in ('ARTIFACT_SHA256.json', 'BUNDLE_VERIFICATION.json'):
            files[path.name] = path
    for name in ('kinetic_audit', 'tests', 'configs'):
        for path in (OVERLAY/name).rglob('*'):
            if eligible(path):
                files[str(Path('research_overlay')/path.relative_to(OVERLAY))] = path
    for name in ('pyproject.toml', 'README.md'):
        files['research_overlay/'+name] = OVERLAY/name
    files['original_paper_experiments.zip'] = OUTPUTS/'paper-experiments-20261015.zip'
    records = {}
    secret = os.environ.get('OPENROUTER_API_KEY', '').encode()
    for name, path in sorted(files.items()):
        data = path.read_bytes()
        if secret and secret in data:
            raise RuntimeError('Credential material found in an artifact: '+name)
        records[name] = {'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data)}
    manifest = {'generated_at': datetime.now(timezone.utc).isoformat(),
        'scope': 'All listed files except this manifest and the external ZIP checksum', 'files': records}
    manifest_path = HERE/'ARTIFACT_SHA256.json'
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True)+'\n')
    TARGET.parent.mkdir(parents=True, exist_ok=True)
    if TARGET.exists():
        raise FileExistsError('Refusing to replace a previously released bundle')
    with zipfile.ZipFile(TARGET, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for name, path in sorted(files.items()):
            archive.write(path, PREFIX+name, compress_type=zipfile.ZIP_STORED if name.endswith('.zip') else None)
        archive.write(manifest_path, PREFIX+'ARTIFACT_SHA256.json')
    with zipfile.ZipFile(TARGET) as archive:
        for name, expected in records.items():
            data = archive.read(PREFIX+name)
            if len(data) != expected['bytes'] or hashlib.sha256(data).hexdigest() != expected['sha256']:
                raise RuntimeError('Archive verification failed: '+name)
    archive_hash = hashlib.sha256(TARGET.read_bytes()).hexdigest()
    TARGET.with_suffix('.zip.sha256').write_text(archive_hash+'  '+TARGET.name+'\n')
    report = {'status': 'VERIFIED', 'archive': str(TARGET), 'archive_sha256': archive_hash,
              'archive_bytes': TARGET.stat().st_size, 'verified_source_files': len(records),
              'current_credential_literal_matches': 0, 'manifest_self_hash_excluded': True}
    (HERE/'BUNDLE_VERIFICATION.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report))


if __name__ == '__main__':
    main()
