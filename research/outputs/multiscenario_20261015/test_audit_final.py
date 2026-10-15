"""Auditor helper checks with cached canned responses; never audits live data."""
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

import audit_final
import run_scenarios


class AuditHelperTests(unittest.TestCase):
    def test_request_reconstruction_matches_frozen_builder_without_network(self):
        # Existing cached call.json makes the actual frozen builder return
        # before provider access; the network method also fails closed here.
        with TemporaryDirectory(dir='/tmp', prefix='audit-request-test-') as directory:
            root = Path(directory)
            with patch('urllib.request.urlopen', side_effect=AssertionError('Network forbidden')):
                index = 0
                for name, domain in run_scenarios.DOMAINS.items():
                    world = run_scenarios.world_for(name, 6001)
                    for objective in run_scenarios.OBJECTIVES:
                        for round_index, policy in [(0, 'baseline'), (1, 'baseline'),
                                                    (1, 'information_guard'), (1, 'action_guard')]:
                            for agent in world['agents']:
                                location = root / str(index)
                                location.mkdir()
                                (location / 'call.json').write_text('{"status":"CANNED_CACHED_NO_API"}')
                                assigned = 'adaptive_controller' if round_index else None
                                run_scenarios.call_model(domain, world, agent, objective,
                                    round_index, [], policy, location, assigned_policy=assigned)
                                observed = json.loads((location / 'request.json').read_text())
                                reconstructed = audit_final.payload_for(run_scenarios, domain, world,
                                    agent, objective, round_index, [], policy, assigned_policy=assigned)
                                self.assertEqual(observed, reconstructed)
                                index += 1
                self.assertEqual(index, 128)

    def test_decimal_usage_aggregation_and_strict_input(self):
        self.assertEqual(audit_final.usage_total([
            {'prompt_tokens': 2, 'completion_tokens': 1, 'total_tokens': 3, 'cost': .1},
            {'prompt_tokens': 3, 'completion_tokens': 2, 'total_tokens': 5, 'cost': .2}]),
            {'prompt_tokens': 5, 'completion_tokens': 3, 'total_tokens': 8, 'cost': .3})
        with self.assertRaises(ValueError):
            audit_final.usage_total([{'cost': float('inf')}])
        with TemporaryDirectory(dir='/tmp', prefix='audit-json-test-') as directory:
            path = Path(directory) / 'record.json'
            path.write_text('{"value":1,"value":2}')
            with self.assertRaises(ValueError):
                audit_final.read(path)
            path.write_text('{"value":NaN}')
            with self.assertRaises(ValueError):
                audit_final.read(path)


if __name__ == '__main__':
    unittest.main()
