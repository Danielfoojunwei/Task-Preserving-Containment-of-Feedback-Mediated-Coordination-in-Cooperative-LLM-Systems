"""Reassemble and verify an original evidence ZIP from its Git-sized parts."""
import argparse
import hashlib
import json
from pathlib import Path


def file_hash(path):
    value = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            value.update(chunk)
    return value.hexdigest()


def main():
    repo = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=Path, default=repo / 'outputs/bundles/task-preserving-research-20261015-expanded.zip.parts/manifest.json')
    parser.add_argument('--out', type=Path)
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text())
    output = args.out or args.manifest.parent.parent / manifest['original_filename']
    if output.exists():
        if output.stat().st_size == manifest['original_bytes'] and file_hash(output) == manifest['original_sha256']:
            print('VERIFIED existing archive: ' + str(output))
            return
        raise RuntimeError('Refusing to overwrite a different existing archive')
    temporary = output.with_name(output.name + '.partial')
    output.parent.mkdir(parents=True, exist_ok=True)
    with temporary.open('xb') as destination:
        for part in manifest['parts']:
            if Path(part['filename']).name != part['filename']:
                raise ValueError('Part filename must be a basename')
            path = args.manifest.parent / part['filename']
            if path.stat().st_size != part['bytes'] or file_hash(path) != part['sha256']:
                raise RuntimeError('Part verification failed: ' + part['filename'])
            with path.open('rb') as stream:
                for chunk in iter(lambda: stream.read(1024 * 1024), b''):
                    destination.write(chunk)
    if temporary.stat().st_size != manifest['original_bytes'] or file_hash(temporary) != manifest['original_sha256']:
        temporary.unlink()
        raise RuntimeError('Reassembled archive verification failed')
    temporary.replace(output)
    print('VERIFIED restored archive: ' + str(output))


if __name__ == '__main__':
    main()
