"""Reproduce saved primary inference on a copy, with no model calls."""
import argparse
import hashlib
import json
from pathlib import Path
import runpy
import shutil
import socket
import sys
import urllib.request


NETWORK_ATTEMPTS = 0


def blocked(*args, **kwargs):
    global NETWORK_ATTEMPTS
    NETWORK_ATTEMPTS += 1
    raise RuntimeError('Network access is disabled during offline analysis')


def snapshot(root):
    return {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in root.rglob('*') if p.is_file() and '__pycache__' not in p.parts}


def run(script, arguments):
    previous = sys.argv
    try:
        sys.argv = [str(script), *arguments]
        runpy.run_path(str(script), run_name='__main__')
    finally:
        sys.argv = previous


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    adjacent = Path(__file__).resolve().parent
    if not (adjacent/'controlplane_20261015').exists():
        adjacent = adjacent.parent
    parser.add_argument('--dataset', type=Path, default=adjacent/'controlplane_20261015')
    parser.add_argument('--followup', type=Path, default=adjacent/'hostmask_20261015')
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    dataset, followup, output = args.dataset.resolve(), args.followup.resolve(), args.out.resolve()
    originals = {str(root): snapshot(root) for root in (dataset, followup)}
    output.mkdir(parents=True, exist_ok=False)
    for root in (dataset, followup):
        shutil.copytree(root, output/root.name,
                        ignore=shutil.ignore_patterns('__pycache__', '*.pyc', '*.lock', 'matplotlib_cache'))
    copied_main, copied_followup = output/dataset.name, output/followup.name
    sys.dont_write_bytecode = True
    urllib.request.urlopen = blocked
    socket.create_connection = blocked
    run(copied_main/'analyze_controlplane.py', ['--root', str(copied_main)])
    run(copied_followup/'run_hostmask.py', ['--analyze'])
    original = json.loads((dataset/'controlplane_results.json').read_text())
    regenerated = json.loads((copied_main/'controlplane_results.json').read_text())
    if original['primary_family'] != regenerated['primary_family']:
        raise RuntimeError('Primary results differ in the offline copy')
    original_followup = json.loads((followup/'analysis.json').read_text())
    regenerated_followup = json.loads((copied_followup/'analysis.json').read_text())
    if original_followup['primary'] != regenerated_followup['primary']:
        raise RuntimeError('Follow-up primary results differ in the offline copy')
    unchanged = all(snapshot(root) == originals[str(root)] for root in (dataset, followup))
    if not unchanged or NETWORK_ATTEMPTS:
        raise RuntimeError('Original evidence changed or offline analysis attempted network access')
    result = {'status': 'PASSED', 'network_attempts': NETWORK_ATTEMPTS,
              'main_primary_results_identical': True, 'followup_primary_results_identical': True,
              'regenerated_analysis_status': regenerated['status'],
              'regenerated_followup_status': regenerated_followup['status'],
              'source_datasets_unchanged': unchanged}
    (output/'OFFLINE_REPRODUCTION.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result))


if __name__ == '__main__':
    main()
