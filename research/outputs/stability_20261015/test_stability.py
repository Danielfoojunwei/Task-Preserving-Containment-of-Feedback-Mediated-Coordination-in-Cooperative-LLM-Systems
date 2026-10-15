"""Finite interface and scoring tests; never calls a provider."""
import importlib.util
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('stability_runner_under_test', HERE / 'run_stability.py')
s = importlib.util.module_from_spec(spec)
spec.loader.exec_module(s)


class StabilityTests(unittest.TestCase):
    def test_registered_design_counts_and_donor_independence(self):
        cases = s.make_cases()
        self.assertEqual(len(cases), 1280)
        self.assertEqual(len({c['case_id'] for c in cases}), 1280)
        self.assertEqual({c['world_seed'] for c in cases}, set(range(8101, 8121)))
        for seed in s.SEEDS:
            self.assertEqual(sum(c['world_seed'] == seed for c in cases), 64)
            for arm in s.NEUTRAL_ARMS:
                rows = [c for c in cases if c['world_seed'] == seed and c['arm'] == arm]
                self.assertEqual(len(rows), 8)
                self.assertEqual({r['repeat'] for r in rows}, {0, 1})
            donors = [c for c in cases if c['world_seed'] == seed and c['arm'] == 'donor_joint']
            self.assertEqual(len({c['delivered_source_bit'] for c in donors}), 1)
            self.assertEqual({c['bit'] for c in donors}, {0, 1})

    def test_all_realized_source_maps_have_registered_information_laws(self):
        with patch.object(s.api_client, 'call', side_effect=AssertionError('No network in certificate')):
            cert = s.certificate()
        self.assertEqual(cert['status'], 'PASSED_OFFLINE')
        self.assertEqual(cert['enumerated_cells'], 80)
        self.assertTrue(all(c['label_TV'] == c['receipt_TV'] == 0 for c in cert['cells']))

    def test_neutral_only_delivered_view_and_explicit_value_vary(self):
        rows = [c for c in s.make_cases() if c['world_seed'] == 8101 and c['bit'] == 1 and c['pad'] == 0]
        cores, systems = [], []
        for c in rows:
            if c['arm'] not in s.NEUTRAL_ARMS:
                continue
            _, _, prompt = s.delivered_case(c, {'attestation': bool(c['delivered_source_bit'])})
            body = json.loads(prompt['user'])
            self.assertNotIn('assigned_policy', body)
            self.assertNotIn('mandatory_contract', body)
            self.assertEqual(body['explicit_bit'], 1 if c['arm'] == 'explicit' else None)
            for name in ('world_seed', 'arm', 'repeat', 'pad', 'source_id', 'bit'):
                self.assertNotIn(name, body)
            cores.append({k: v for k, v in body.items() if k not in ('observed_transcript', 'explicit_bit')})
            systems.append(prompt['system'])
        self.assertTrue(all(c == cores[0] for c in cores))
        self.assertEqual(len(set(systems)), 1)

    def test_identical_repeats_and_full_input_invariance(self):
        cases = s.make_cases()
        by = {(c['bit'], c['pad'], c['arm'], c['repeat']): c
              for c in cases if c['world_seed'] == 8101}
        full_requests = set()
        for c in by.values():
            _, _, prompt = s.delivered_case(c, {'attestation': bool(c['delivered_source_bit'])})
            if c['arm'] == 'full':
                full_requests.add(s.digest(s.request_payload(prompt, s.RECEIVER_SCHEMA)))
            if c['arm'] in s.NEUTRAL_ARMS and c['repeat'] == 0:
                twin = by[c['bit'], c['pad'], c['arm'], 1]
                _, _, repeated = s.delivered_case(twin, {'attestation': bool(twin['delivered_source_bit'])})
                self.assertEqual(prompt, repeated)
        self.assertEqual(len(full_requests), 1)

    def test_banner_cross_keeps_exact_old_bundle_and_view(self):
        for c in s.make_cases()[:64]:
            if c['arm'] not in s.BANNER_ARMS:
                continue
            world, mediation, prompt = s.delivered_case(c, {'attestation': bool(c['bit'])})
            body = json.loads(prompt['user'])
            prior = json.loads(s.old.receiver_prompt(world, mediation['transcript'], c['banner'])['user'])
            for key in ('assigned_policy', 'mandatory_contract'):
                self.assertEqual(body[key], prior[key])
            neutral = s.receiver_prompt(world, mediation['transcript'])
            self.assertEqual({k: v for k, v in body.items() if k not in ('assigned_policy', 'mandatory_contract')},
                             json.loads(neutral['user']))

    def test_schema_invalid_field_preserves_raw_bit_but_not_accepted_action(self):
        world = s.m.make_world(8101, 'joint_xor', 1, 0)
        mediation = s.mediate(world, {'attestation': True}, 0, 'joint')
        good = {'decoded_bit': 1, 'route': s.m.required_route(world),
                'schedule': s.m.required_schedule(world), 'checksum': s.m.required_checksum(world)}
        score = s.old.evaluate(world, {'attestation': True}, mediation, good, 1)['metrics']
        self.assertEqual(score['primary_q'], 1)
        self.assertTrue(score['accepted_host_bet'])
        self.assertEqual(score['coalition_payoff'], 2)
        malformed = dict(good, schedule=['J1'])
        call = {'raw_content': json.dumps(malformed), 'parsed_action': {}, 'action_valid': False}
        raw = s.raw_action(call)
        score = s.old.evaluate(world, {'attestation': True}, mediation, raw, 1)['metrics']
        self.assertEqual(score['primary_q'], 1)
        self.assertTrue(score['raw_bit_valid'])
        self.assertFalse(score['receiver_valid'])
        self.assertFalse(score['accepted_host_bet'])
        self.assertEqual(score['coalition_payoff'], 0)

    def test_invalid_bit_types_and_duplicate_keys_cannot_create_a_recovery(self):
        for raw in ('{"decoded_bit":true}', '{"decoded_bit":1,"decoded_bit":0}',
                    '{"decoded_bit":1.0}', '{"decoded_bit":2}', 'not json'):
            action = s.raw_action({'raw_content': raw})
            self.assertIsNone(s.old.field_bit(action))
        self.assertEqual(s.old.field_bit(s.raw_action({'raw_content': '{"decoded_bit":1}'})), 1)
        for action in ({}, {'attestation': 1}, {'attestation': True, 'extra': 0}):
            value, valid = s.old.source_value(action)
            self.assertFalse(valid)
            self.assertFalse(value)

    def test_positive_exposure_and_single_field_controls(self):
        cases = [c for c in s.make_cases() if c['world_seed'] == 8101 and c['bit'] == 1 and c['pad'] == 0]
        for c in cases:
            world, mediation, prompt = s.delivered_case(c, {'attestation': True})
            body = json.loads(prompt['user'])
            if c['arm'] == 'explicit':
                self.assertEqual(body['explicit_bit'], 1)
                self.assertEqual(mediation['transcript']['policy_label'], s.m.FIXED_TAG)
            if c['arm'] == 'label_only':
                self.assertIsNone(mediation['transcript']['receipt'])
            if c['arm'] == 'receipt_only':
                self.assertIsNone(mediation['transcript']['policy_label'])

    def test_immutable_artifact_and_freeze_mismatch_are_refused(self):
        with TemporaryDirectory() as temporary, patch.object(s, 'ROOT', Path(temporary)):
            path = Path(temporary) / 'one.json'
            s.write(path, {'value': 1}, immutable=True)
            s.write(path, {'value': 1}, immutable=True)
            with self.assertRaises(RuntimeError):
                s.write(path, {'value': 2}, immutable=True)
            s.write(Path(temporary) / 'FREEZE.json', {'files': [
                {'path': 'one.json', 'sha256': s.digest({'value': 1})}]})
            s.verify_freeze()
            path.write_text('{}')
            with self.assertRaises(RuntimeError):
                s.verify_freeze()

    def test_failed_first_transport_probe_does_not_dispatch_remaining_study(self):
        with TemporaryDirectory() as temporary, patch.object(s, 'ROOT', Path(temporary)), \
                patch.object(s, 'verify_freeze'), patch.object(s, 'progress'), \
                patch.object(s, 'make_source', return_value={
                    'source_id': 'mini__s8101__b0', 'status': 'failed'}) as first, \
                patch.object(s, 'stage') as later:
            with self.assertRaises(RuntimeError):
                s.run()
            first.assert_called_once_with(8101, 0)
            later.assert_not_called()

    def test_cost_cap_prevents_dispatch_before_provider_call(self):
        with TemporaryDirectory() as temporary, patch.object(s, 'ROOT', Path(temporary)), \
                patch.object(s, 'COST_CAP', 0), patch.object(s, 'COSTS', {}), \
                patch.object(s, 'RESERVATIONS', {}), patch.object(s.api_client, 'call') as provider:
            with self.assertRaises(RuntimeError):
                s.dispatch(s.old.source_prompt(0), s.SOURCE_SCHEMA, Path(temporary) / 'calls' / 'one')
            provider.assert_not_called()


if __name__ == '__main__':
    unittest.main()
