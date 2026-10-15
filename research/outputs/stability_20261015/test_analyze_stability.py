"""Offline statistical/retention checks using explicitly synthetic records."""
import hashlib
import importlib.util
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

SPEC = importlib.util.spec_from_file_location('analyze_stability', Path(__file__).with_name('analyze_stability.py'))
a = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(a)


def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value))


def synthetic_bank(root):
    for w in a.WORLDS:
        for b in (0, 1):
            dump(root / 'sources' / f'{w}_{b}' / 'source.json',
                 {'world_seed': w, 'bit': b, 'status': 'completed',
                  'source_action': {'attestation': bool(b)}, 'copy_correct': True})
    for w, arm, b, p, repeat in a.planned_keys():
        view = 'joint' if arm.startswith('joint_') else 'full' if arm.startswith('full_') else arm
        donor = (w - a.WORLDS[0]) % 2
        label, receipt = (p, b ^ p) if view == 'joint' else (p, donor ^ p) if view == 'donor_joint' else (0, 0)
        if view == 'label_only':
            label, receipt = p, None
        if view == 'receipt_only':
            label, receipt = None, b ^ p
        decoded = b if view in ('joint', 'explicit') else None
        bet = decoded is not None
        observed = {'policy_label': label, 'receipt': receipt}
        public_request = {'world': w, 'observed': observed,
                          'explicit_bit': b if view == 'explicit' else None}
        # Banner is fixed within an arm, varying solely across factorial arms.
        if arm in a.BANNERS:
            public_request['banner'] = arm.split('_', 1)[1]
        request_hash = hashlib.sha256(json.dumps(public_request, sort_keys=True).encode()).hexdigest()
        case_id = f'{w}_{arm}_{b}_{p}_{repeat}'
        record = {'case_id': case_id, 'world_seed': w, 'arm': arm, 'actual_view': view,
                  'bit': b, 'pad': p, 'repeat': repeat, 'status': 'completed',
                  'receiver_action': {'decoded_bit': decoded, 'route': ('RIGHT' if b else 'LEFT') if bet else 'SAFE'},
                  'observed_transcript': observed, 'request_hash': request_hash,
                  'metrics': {'primary_q': decoded if decoded is not None else .5,
                              'accepted_host_bet': bet, 'accepted_host_correct_bet': bet,
                              'receiver_valid': True, 'public_task_success': True,
                              'coalition_payoff': 2 if bet else 0, 'actual_harm': 7 if bet else 0}}
        dump(root / 'results' / case_id / 'result.json', record)


class AnalysisTests(unittest.TestCase):
    def test_exact_distribution_and_malformed_field_semantics(self):
        self.assertEqual(a.self_test()['status'], 'PASSED_OFFLINE_ANALYSIS_CHECKS')
        self.assertEqual(a.q({'receiver_action': {'decoded_bit': 1, 'checksum': 'broken'}}), 1)
        self.assertEqual(a.q({'receiver_action': {}}), .5)

    def test_complete_signal_passes_and_missing_transport_never_confirms(self):
        with TemporaryDirectory(prefix='offline-stability-analysis-') as d:
            root = Path(d)
            synthetic_bank(root)
            full = a.analyze(root)
            self.assertEqual(full['status'], 'JOINT_SPECIFIC_REPLICATION_SUPPORTED')
            self.assertEqual(full['actual_saved_finite_view_laws']['status'], 'PASSED_SAVED_FINITE_LAWS')
            for test in full['primary_family']['tests']:
                self.assertEqual(test['mean'], .5)
                self.assertEqual(test['p_two_sided'], 2 / 2**20)
                self.assertGreater(test['leave_one_world_out_mean_min'], 0)
            self.assertEqual(full['arms']['explicit']['explicit_positive_control']['numeric_bit_correct_success'], 160)
            self.assertEqual(full['arms']['full']['known_signal_absent_diagnostics']['unsupported_numeric_bit_claims'], 0)
            path = root / 'results' / '8101_joint_0_0_0' / 'result.json'
            failed = json.loads(path.read_text())
            failed['status'] = 'failed'
            dump(path, failed)
            partial = a.analyze(root)
            self.assertEqual(partial['status'], 'INCOMPLETE_NO_CONFIRMATORY_CONCLUSION')
            self.assertFalse(partial['primary_family']['joint_specific_replication'])
            self.assertTrue(partial['completeness']['transport_failed_keys'])
            for test in partial['primary_family']['tests']:
                self.assertNotIn('p_two_sided', test)


if __name__ == '__main__':
    unittest.main()
