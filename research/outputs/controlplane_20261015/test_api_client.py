"""Canned HTTP transport tests: no external network or paid calls."""
from copy import deepcopy
import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import urllib.error

import api_client as api

SCHEMA = {'type': 'object', 'properties': {'units': {'type': 'integer'}, 'note': {'type': 'string'}},
          'required': ['units', 'note'], 'additionalProperties': False}
MESSAGES = [{'role': 'user', 'content': 'Synthetic fixture; return an action.'}]


class Response:
    status = 200

    def __init__(self, content='{"units":2,"note":"fixture"}', model='openai/gpt-4.1-mini'):
        self.data = api.canonical({'id': 'canned-provider-id', 'model': model,
            'choices': [{'message': {'content': content}}],
            'usage': {'prompt_tokens': 12, 'completion_tokens': 7, 'total_tokens': 19, 'cost': .0001}})

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return self.data


class ClientTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(dir='/tmp', prefix='controlplane-api-canned-')
        self.root = Path(self.tmp.name)
        self.key = 'FAKE_CANNED_KEY_NEVER_TRANSMITTED'
        self.env = patch.dict(api.os.environ, {'OPENROUTER_API_KEY': self.key})
        self.env.start()

    def tearDown(self):
        self.env.stop()
        self.tmp.cleanup()

    def call(self, **kwargs):
        return api.call(MESSAGES, SCHEMA, 'openai/gpt-4.1-mini', self.root, **kwargs)

    def test_exact_wire_profile_hash_usage_and_no_secret(self):
        def fake(request, timeout):
            self.assertEqual(request.headers['Authorization'], 'Bearer '+self.key)
            self.assertEqual(timeout, 120)
            self.assertEqual(request.data, (self.root/'request.json').read_bytes())
            return Response()
        with patch.object(api.urllib.request, 'urlopen', side_effect=fake) as network:
            record = self.call()
        self.assertEqual(network.call_count, 1)
        payload = json.loads((self.root/'request.json').read_text())
        self.assertEqual(payload['provider'], {'require_parameters': True})
        self.assertEqual(payload['response_format']['json_schema']['name'], 'agent_action')
        self.assertTrue(payload['response_format']['json_schema']['strict'])
        self.assertEqual((payload['temperature'], payload['max_tokens']), (.7, 1500))
        self.assertEqual(record['input_sha256'], hashlib.sha256((self.root/'request.json').read_bytes()).hexdigest())
        self.assertTrue(record['action_valid'])
        self.assertEqual(record['usage']['total_tokens'], 19)
        self.assertEqual(record['provider_response_id'], 'canned-provider-id')
        for path in self.root.iterdir():
            self.assertNotIn(self.key, path.read_text())
            self.assertNotIn('Authorization', path.read_text())

    def test_resume_immutable_without_key_and_changed_request_refused(self):
        with patch.object(api.urllib.request, 'urlopen', return_value=Response()):
            first = self.call()
        before = {p.name: p.read_bytes() for p in self.root.iterdir()}
        with patch.dict(api.os.environ, {}, clear=True), patch.object(api.urllib.request, 'urlopen', side_effect=AssertionError('NO NETWORK')):
            self.assertEqual(self.call(), first)
            with self.assertRaises(ValueError):
                api.call(MESSAGES, SCHEMA, 'openai/gpt-4.1', self.root)
        self.assertEqual(before, {p.name: p.read_bytes() for p in self.root.iterdir()})

    def test_transport_status_retry_and_raw_attempt_preservation(self):
        error = urllib.error.HTTPError(api.ENDPOINT, 429, 'canned', {}, io.BytesIO(b'{"error":"rate limited"}'))
        with patch.object(api.urllib.request, 'urlopen', side_effect=[error, Response()]) as network:
            result = self.call()
        self.assertEqual(network.call_count, 2)
        self.assertEqual(result['attempt'], 2)
        one, two = api._read(self.root/'attempt_1.json'), api._read(self.root/'attempt_2.json')
        self.assertTrue(one['retryable'])
        self.assertEqual(one['provider_response'], {'error': 'rate limited'})
        self.assertEqual(one['input_sha256'], two['input_sha256'])

    def test_retry_status_set_bound_and_bad_request_no_retry(self):
        for status in [401, 408, 429, 500, 503, 599, 400, 403, 422]:
            path = self.root/str(status)
            def error(*args, **kwargs):
                raise urllib.error.HTTPError(api.ENDPOINT, status, 'canned', {}, io.BytesIO(b'{}'))
            with patch.object(api.urllib.request, 'urlopen', side_effect=error) as network:
                result = api.call(MESSAGES, SCHEMA, 'openai/gpt-4.1-mini', path)
            self.assertEqual(network.call_count, 3 if status in [401, 408, 429, 500, 503, 599] else 1)
            self.assertEqual(result['status'], 'failed')

    def test_malformed_and_schema_violating_success_never_retries(self):
        bad = ['{"units":1,"units":2,"note":"x"}', '{"units":NaN,"note":"x"}',
               '{"units":1e999,"note":"x"}', '{"units":true,"note":"x"}',
               '{"units":1.0,"note":"x"}', '{"units":1,"note":"x","extra":0}',
               '{"units":1}', '[]', 'not JSON']
        for index, content in enumerate(bad):
            with patch.object(api.urllib.request, 'urlopen', return_value=Response(content)) as network:
                result = api.call(MESSAGES, SCHEMA, 'openai/gpt-4.1-mini', self.root/str(index))
            self.assertEqual(network.call_count, 1)
            self.assertEqual(result['status'], 'completed')
            self.assertFalse(result['action_valid'])
            self.assertEqual(result['parsed_action'], {})

    def test_full_model_and_optional_nested_schema_enforcement(self):
        schema = {'type': 'object', 'properties': {'nested': {'type': 'object', 'properties': {'x': {'type': 'integer'}}, 'required': ['x']}}, 'required': ['nested']}
        original = deepcopy(schema)
        with patch.object(api.urllib.request, 'urlopen', return_value=Response('{"nested":{"x":2}}', model='openai/gpt-4.1')):
            result = api.call(MESSAGES, schema, 'openai/gpt-4.1', self.root, enforce_additional_properties=True)
        self.assertTrue(result['action_valid'])
        self.assertEqual(schema, original)
        sent = api._read(self.root/'request.json')['response_format']['json_schema']['schema']
        self.assertFalse(sent['additionalProperties'])
        self.assertFalse(sent['properties']['nested']['additionalProperties'])

    def test_interrupted_attempt_is_not_replayed(self):
        with patch.object(api.urllib.request, 'urlopen', side_effect=KeyboardInterrupt):
            with self.assertRaises(KeyboardInterrupt):
                self.call()
        with patch.object(api.urllib.request, 'urlopen', side_effect=AssertionError('NO NETWORK')) as network:
            resumed = self.call()
        self.assertEqual(network.call_count, 0)
        self.assertEqual(resumed['status'], 'indeterminate')
        self.assertFalse(resumed['retryable'])

    def test_remote_schema_ref_rejected_without_network(self):
        with patch.object(api.urllib.request, 'urlopen', side_effect=AssertionError('NO NETWORK')) as network:
            for ref_key in ('$ref', '$dynamicRef', '$recursiveRef'):
                with self.assertRaises(ValueError):
                    api.call(MESSAGES, {ref_key: 'https://invalid.example/schema'}, 'openai/gpt-4.1-mini', self.root)
        self.assertEqual(network.call_count, 0)

    def test_bare_transport_failures_retry_but_remain_bounded(self):
        for index, error in enumerate((urllib.error.URLError('canned connection failure'), TimeoutError())):
            with patch.object(api.urllib.request, 'urlopen', side_effect=error) as network:
                result = api.call(MESSAGES, SCHEMA, 'openai/gpt-4.1-mini', self.root/str(index))
            self.assertEqual(network.call_count, 3)
            self.assertEqual(result['status'], 'failed')

    def test_http_error_secret_echo_is_redacted(self):
        body = api.canonical({'error': self.key})
        error = urllib.error.HTTPError(api.ENDPOINT, 400, 'canned', {}, io.BytesIO(body))
        with patch.object(api.urllib.request, 'urlopen', side_effect=error):
            result = self.call()
        self.assertTrue(result['secret_redacted'])
        for path in self.root.iterdir():
            self.assertNotIn(self.key, path.read_text())

    def test_credential_in_payload_rejected_before_persistence(self):
        with patch.object(api.urllib.request, 'urlopen', side_effect=AssertionError('NO NETWORK')):
            with self.assertRaises(ValueError):
                api.call([{'role': 'user', 'content': self.key}], SCHEMA,
                         'openai/gpt-4.1-mini', self.root)
        self.assertFalse((self.root/'request.json').exists())


if __name__ == '__main__':
    unittest.main()
