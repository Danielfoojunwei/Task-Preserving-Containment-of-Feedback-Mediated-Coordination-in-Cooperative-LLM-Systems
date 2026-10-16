#!/usr/bin/env python3
"""Post-release descriptive tables only; no new hypothesis test or API request."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
MAIN = HERE.parent / 'overt_covert_relaunch_20261016'


def build():
    hashes = {}

    def read(path):
        blob = path.read_bytes()
        hashes[str(path.relative_to(HERE.parent))] = hashlib.sha256(blob).hexdigest()
        return json.loads(blob)

    analysis = read(MAIN / 'ANALYSIS.json')
    raw = read(MAIN / 'independent/final/INDEPENDENT_VERIFICATION_ALL.json')
    independent = read(MAIN / 'independent/primary/INDEPENDENT_PRIMARY_VERIFICATION.json')
    bindings = read(MAIN / 'independent/final/SOURCE_BINDINGS.json')
    if not (analysis['inference_eligible'] and raw['passed'] and independent['passed'] and bindings['passed']):
        raise ValueError('Completed released analysis and independent verification required')
    arms = []
    for condition, summary in sorted(analysis['summary'].items()):
        worlds = [w for w in analysis['sessions'] if w['phase'] == 'validation' and w['condition'] == condition]
        assert len(worlds) == 20
        late = [r for w in worlds for r in w['rounds'] if r['round'] >= 2]
        arms.append({'condition': condition, 'worlds': 20,
            'primary_M_rounds_2_4': sum(w['primary_exact']['value'] for w in worlds) / 20,
            'late_rounds': 60, 'late_prefine_joint_benefit': sum(r['base_bilateral_score'] for r in late) / 60,
            'late_gross_unsupported_payment': sum(r['base']['gross_owner_excess'] for r in late),
            'late_net_owner_loss': sum(r['base']['net_owner_loss'] for r in late),
            'late_fines_collected': sum(2 * r['fine_each'] for r in late),
            'all_rounds': summary})
    fixture_views = {}
    fixtures = read(MAIN / 'monitor_controls.json')['cases']
    for view in ('public', 'full'):
        counts = Counter()
        for fixture in (f for f in fixtures if f['view'] == view):
            result = read(MAIN / 'monitor_results' / (fixture['case_id'] + '.json'))
            expected = fixture['gold']['flag']
            counts['cases'] += 1
            counts['supported_positive' if expected else 'supported_negative'] += 1
            valid = result.get('flag_valid') is True
            if not valid:
                counts['unknown'] += 1
            else:
                counts[('true_' if result['flag'] == expected else 'false_') + ('positive' if result['flag'] else 'negative')] += 1
            if fixture['gold']['latent_pact_observation_gap']:
                counts['latent_pact_visibility_gap_cases'] += 1
                counts['visibility_gap_valid_flags' if valid and result['flag'] else 'visibility_gap_no_valid_flag'] += 1
        fixture_views[view] = dict(counts)
    controls = []
    for world in analysis['sessions']:
        if world['phase'] != 'controls':
            continue
        rounds = world['rounds']
        controls.append({'session_id': world['session_id'], 'type': world['control_type'],
            'audit_view': world['audit_view'], 'fine_per_actor': world['fine_per_actor'],
            'rounds': len(rounds), 'audit_flags': sum(r['audit_flag'] for r in rounds),
            'net_owner_loss': sum(r['base']['net_owner_loss'] for r in rounds),
            'both_postfine_positive_rounds': sum(all(r['scores'][a] > 0 for a in 'AB') for r in rounds),
            'unsupported_claims': sum(r['unsupported_claims'] for r in rounds),
            'unsupported_approvals': sum(r['unsupported_approvals'] for r in rounds)})
    return {'schema_version': 1, 'scope': 'Unfrozen post-release descriptive tabulation; no new p-values or semantic relabeling.',
        'arms': arms, 'fixed_authored_monitor_challenges': fixture_views, 'actor_controls': controls,
        'fixture_limits': 'Tiny assistant-authored challenge suite; visibility gaps are distinct from evidential false negatives; not deployment calibration.',
        'source_sha256': hashes, 'builder_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--release', action='store_true')
    parser.add_argument('--output', type=Path, default=HERE / 'DESCRIPTIVE_TABLES.json')
    args = parser.parse_args()
    if not args.release:
        parser.error('Explicit numerical release required')
    result = build()
    with args.output.open('x') as stream:
        json.dump(result, stream, indent=2, sort_keys=True)
        stream.write('\n')
    print(json.dumps({'arms': len(result['arms']), 'controls': result['actor_controls'],
        'monitor_challenges': result['fixed_authored_monitor_challenges']}))


if __name__ == '__main__':
    main()
