"""Regenerate frozen analyses on copied artifacts; never makes provider calls.

Original execution records intentionally retain their original absolute paths.
This wrapper remaps those path lookups in memory, without editing frozen files.
"""
from __future__ import annotations
import argparse
import importlib.util
import json
from pathlib import Path
import shutil
import sys
import urllib.request

ORIGINAL_OUTPUTS = Path('/workspace/colosseum_task_preserving_starter/outputs')
DATASETS = {'revision': ('revision_20261015', 'analyze_revision.py'),
            'scenarios': ('multiscenario_20261015', 'analyze_scenarios.py'),
            'joint': ('multiscenario_joint_20261015', 'run_joint.py')}


def no_network(*args, **kwargs):
    raise RuntimeError('Network calls are disabled during offline reproduction')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-root', type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--studies', nargs='+', choices=list(DATASETS), default=list(DATASETS))
    args = parser.parse_args()
    source = args.source_root.resolve()
    dest = args.out.resolve()
    dest.mkdir(parents=True, exist_ok=False)
    overlay = next((p for p in (source/'research_overlay', source.parent, source.parent.parent)
                    if (p/'kinetic_audit').exists()), None)
    if overlay is None:
        raise RuntimeError('The bundled research_overlay package is missing')
    sys.path.insert(0, str(overlay))
    urllib.request.urlopen = no_network

    def mapped_path(*parts):
        value = Path(*parts)
        if value.is_absolute() and value.is_relative_to(ORIGINAL_OUTPUTS):
            return dest/value.relative_to(ORIGINAL_OUTPUTS)
        return value

    results = {}
    for study in args.studies:
        name, script = DATASETS[study]
        directory = source/name
        if not directory.exists():
            directory = source.parent/name
        target = dest/name
        if not target.exists():
            shutil.copytree(directory, target, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
        if study == 'joint' and not (dest/DATASETS['scenarios'][0]).exists():
            dependency = source/DATASETS['scenarios'][0]
            if not dependency.exists():
                dependency = source.parent/DATASETS['scenarios'][0]
            shutil.copytree(dependency, dest/dependency.name,
                            ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
        spec = importlib.util.spec_from_file_location('offline_'+study, target/script)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        module.Path = mapped_path
        old_argv = sys.argv
        try:
            sys.argv = ([str(target/script), '--analyze'] if study == 'joint' else
                        [str(target/script), '--root', str(target)])
            module.main()
        finally:
            sys.argv = old_argv
        filename = {'revision': 'revision_results.json', 'scenarios': 'scenario_results.json',
                    'joint': 'JOINT_RESULTS.json'}[study]
        original = json.loads((directory/filename).read_text())
        regenerated = json.loads((target/filename).read_text())
        key = 'summaries' if study == 'joint' else 'primary_family'
        # Paths, report timestamps and log-file mtime observations may differ;
        # the registered primary estimates and tests must be identical.
        if original[key] != regenerated[key]:
            raise RuntimeError('Primary inference changed during offline reproduction: '+study)
        results[study] = {'primary_results_identical': True, 'status': regenerated['status']}
    (dest/'OFFLINE_REPRODUCTION.json').write_text(json.dumps(results, indent=2)+'\n')
    print(json.dumps({'network_calls': 0, 'results': results, 'output': str(dest)}))


if __name__ == '__main__':
    main()
