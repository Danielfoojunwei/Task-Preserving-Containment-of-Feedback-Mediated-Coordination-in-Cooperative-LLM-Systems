"""Check imported evidence bytes and relocated pilot-result symlinks offline."""
import hashlib
import json
from pathlib import Path


def main():
    root = Path(__file__).resolve().parents[1] / 'research'
    manifest = json.loads((root / 'IMPORT_MANIFEST.json').read_text())
    for name, record in manifest['files'].items():
        path = root / name
        if path.stat().st_size != record['bytes'] or hashlib.sha256(path.read_bytes()).hexdigest() != record['sha256']:
            raise RuntimeError('Imported source/evidence differs: ' + name)
    for record in manifest['relocated_symlinks']:
        path = root / record['path']
        if not path.is_symlink() or not path.exists() or str(path.readlink()) != record['published_target']:
            raise RuntimeError('Relocated link differs: ' + record['path'])
    print(json.dumps({'status': 'PASSED', 'files_verified': len(manifest['files']),
                      'portable_symlinks_verified': len(manifest['relocated_symlinks']),
                      'provider_calls': 0}))


if __name__ == '__main__':
    main()
