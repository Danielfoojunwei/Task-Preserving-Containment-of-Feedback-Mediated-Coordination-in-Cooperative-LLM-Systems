"""OpenRouter transport with immutable requests, bounded retries and strict actions.

No calls occur at import. urllib's default proxy and CA handling is preserved.
The caller schedules concurrency; this module never starts workers.
"""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path
import urllib.error
import urllib.request

from jsonschema import Draft202012Validator, validators

ENDPOINT = 'https://openrouter.ai/api/v1/chat/completions'
MAX_ATTEMPTS = 3


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False,
                      allow_nan=False).encode('utf-8')


def sha256(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def _now():
    return datetime.now(timezone.utc).isoformat()


def strict_json(text):
    """Reject duplicate keys at every depth and all nonfinite JSON constants."""
    if not isinstance(text, str):
        raise ValueError('Expected JSON text')
    def pairs(items):
        value = {}
        for key, item in items:
            if key in value:
                raise ValueError('Duplicate JSON key')
            value[key] = item
        return value
    def nonfinite(value):
        raise ValueError('Nonfinite JSON constant')
    result = json.loads(text, object_pairs_hook=pairs, parse_constant=nonfinite)
    # JSON exponent overflow (1e999) is not handled by parse_constant.
    def finite(value):
        if isinstance(value, float) and not math.isfinite(value):
            raise ValueError('Nonfinite JSON number')
        if isinstance(value, dict):
            for item in value.values():
                finite(item)
        elif isinstance(value, list):
            for item in value:
                finite(item)
    finite(result)
    return result


def _integer(checker, value):
    return isinstance(value, int) and not isinstance(value, bool)


def _number(checker, value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


StrictValidator = validators.extend(Draft202012Validator, type_checker=(
    Draft202012Validator.TYPE_CHECKER.redefine('integer', _integer).redefine('number', _number)))


def _schema_copy(schema, enforce_additional_properties):
    if schema is None:
        return None
    if not isinstance(schema, dict):
        raise ValueError('Schema must be an object or None')
    result = deepcopy(schema)
    def visit(node):
        if isinstance(node, dict):
            kinds = node.get('type', [])
            if isinstance(kinds, str):
                kinds = [kinds]
            if enforce_additional_properties and ('object' in kinds or 'properties' in node):
                node['additionalProperties'] = False
            # Remote references are deliberately unavailable to local validation:
            # validation must not create a second, unrecorded network route.
            for ref_key in ('$ref', '$dynamicRef', '$recursiveRef'):
                ref = node.get(ref_key)
                if isinstance(ref, str) and not ref.startswith('#'):
                    raise ValueError('Only local schema references are supported')
            for child in node.values():
                visit(child)
        elif isinstance(node, list):
            for child in node:
                visit(child)
    visit(result)
    Draft202012Validator.check_schema(result)
    canonical(result)
    return result


def validate_action(raw_content, schema):
    try:
        action = strict_json(raw_content)
        if not isinstance(action, dict):
            return {}, False, 'action_must_be_object'
        if schema is not None and not StrictValidator(schema).is_valid(action):
            return {}, False, 'action_schema_violation'
        return action, True, None
    except (ValueError, TypeError, OverflowError, RecursionError):
        return {}, False, 'invalid_action_json'


def _redact(value, secret):
    if isinstance(value, str):
        return value.replace(secret, '[REDACTED_API_KEY]') if secret else value
    if isinstance(value, list):
        return [_redact(item, secret) for item in value]
    if isinstance(value, dict):
        return {_redact(key, secret): _redact(item, secret) for key, item in value.items()}
    return value


def _save_new(path, value, secret=None):
    redacted = _redact(value, secret)
    if redacted != value:
        redacted['secret_redacted'] = True
        if 'action_valid' in redacted:
            redacted.update(action_valid=False, parsed_action={}, parse_error='secret_echo_redacted')
    data = canonical(redacted)
    if path.exists():
        if path.read_bytes() != data:
            raise FileExistsError('Refusing to change a recorded call artifact')
    else:
        with path.open('xb') as handle:
            handle.write(data)
    return redacted


def _read(path):
    return strict_json(path.read_text())


def _provider_body(record, body):
    text = body.decode('utf-8', errors='replace')
    record['provider_response_text'] = text
    try:
        data = strict_json(text)
    except (ValueError, TypeError, OverflowError, RecursionError):
        record['provider_protocol_error'] = 'invalid_provider_json'
        return None
    record['provider_response'] = data
    if isinstance(data, dict):
        record['usage'] = data.get('usage') if isinstance(data.get('usage'), dict) else {}
        record['actual_provider_model'] = data.get('model')
        record['provider_response_id'] = data.get('id')
    return data


def call(messages, schema, model, directory, *, temperature=.7, max_tokens=1500,
         timeout=120, enforce_additional_properties=False):
    """One logical action; at most three HTTP attempts with an identical payload.

    Completed malformed actions never retry. HTTP401/408/429/5xx may retry.
    Bare URLError/TimeoutError transport failures may also retry. Other
    failures are preserved without automatic retry. Ambiguous interrupted
    attempts are never automatically replayed. Existing final records resume
    without a key, but any changed input is rejected before returning them.
    """
    if not isinstance(messages, list) or not messages:
        raise ValueError('messages must be a nonempty list')
    if not isinstance(model, str) or not model.strip():
        raise ValueError('An explicit model identifier is required')
    if (isinstance(temperature, bool) or not isinstance(temperature, (int, float))
            or not math.isfinite(temperature)):
        raise ValueError('temperature must be finite')
    if isinstance(max_tokens, bool) or not isinstance(max_tokens, int) or max_tokens <= 0:
        raise ValueError('max_tokens must be a positive integer')
    effective_schema = _schema_copy(schema, enforce_additional_properties)
    payload = {'model': model, 'temperature': temperature, 'max_tokens': max_tokens,
        'messages': deepcopy(messages), 'provider': {'require_parameters': True},
        'response_format': ({'type': 'json_object'} if effective_schema is None else
            {'type': 'json_schema', 'json_schema': {'name': 'agent_action', 'strict': True,
                                                   'schema': effective_schema}})}
    wire = canonical(payload)
    input_hash = hashlib.sha256(wire).hexdigest()
    configured_key = os.environ.get('OPENROUTER_API_KEY')
    if configured_key and configured_key.encode('utf-8') in wire:
        raise ValueError('API credentials must not appear in a model payload')
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    # Cross-process locking prevents duplicate charges for the same logical
    # call if two schedulers accidentally target one directory concurrently.
    with (directory/'.call.lock').open('a+b') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        request_path = directory/'request.json'
        if request_path.exists():
            if request_path.read_bytes() != wire:
                raise ValueError('Changed request at an existing call location')
        else:
            with request_path.open('xb') as handle:
                handle.write(wire)
        hash_path = directory/'request_sha256.txt'
        if hash_path.exists():
            if hash_path.read_text() != input_hash:
                raise ValueError('Saved request hash does not match payload')
        else:
            with hash_path.open('x') as handle:
                handle.write(input_hash)
        final_path = directory/'call.json'
        if final_path.exists():
            final = _read(final_path)
            if final.get('input_sha256') != input_hash:
                raise ValueError('Existing call belongs to another input')
            return final
        key = configured_key
        # No secret, request headers or exception messages enter saved records.
        for attempt in range(1, MAX_ATTEMPTS+1):
            path = directory/f'attempt_{attempt}.json'
            started_path = directory/f'attempt_{attempt}.started.json'
            if path.exists():
                record = _read(path)
                if record.get('input_sha256') != input_hash:
                    raise ValueError('Preserved attempt belongs to another input')
                if record['status'] == 'completed' or not record.get('retryable') or attempt == MAX_ATTEMPTS:
                    return _save_new(final_path, record, key)
                continue
            if started_path.exists():
                record = {'status': 'indeterminate', 'action_valid': False, 'parsed_action': {},
                    'raw_content': None, 'usage': {}, 'model': model, 'input_sha256': input_hash,
                    'attempt': attempt, 'retryable': False,
                    'error_type': 'InterruptedAttemptOutcomeUnknown',
                    'started_at': _read(started_path)['started_at'], 'finished_at': _now()}
                return _save_new(final_path, record, key)
            if not key:
                raise RuntimeError('OPENROUTER_API_KEY is not configured')
            record = {'status': 'started', 'action_valid': False, 'parsed_action': {},
                'raw_content': None, 'usage': {}, 'model': model, 'input_sha256': input_hash,
                'schema_sha256': sha256(effective_schema) if effective_schema is not None else None,
                'attempt': attempt, 'started_at': _now()}
            _save_new(started_path, {key_: record[key_] for key_ in ('input_sha256', 'attempt', 'started_at')})
            request = urllib.request.Request(ENDPOINT, data=wire,
                headers={'Content-Type': 'application/json', 'Authorization': 'Bearer '+key})
            try:
                with urllib.request.urlopen(request, timeout=timeout) as response:
                    record['http_status'] = response.status
                    body = response.read()
                data = _provider_body(record, body)
                try:
                    message = data['choices'][0]['message']
                    if not isinstance(message, dict):
                        raise ValueError('Invalid message object')
                    content = message.get('content')
                except (KeyError, TypeError, IndexError, ValueError):
                    record.update(status='failed', retryable=False, error_type='InvalidProviderEnvelope')
                else:
                    parsed, valid, error = validate_action(content, effective_schema)
                    record.update(status='completed', raw_content=content, action_valid=valid,
                                  parsed_action=parsed, retryable=False)
                    if error:
                        record['parse_error'] = error
                    if message.get('refusal') is not None:
                        record['provider_refusal'] = message['refusal']
            except urllib.error.HTTPError as exc:
                try:
                    _provider_body(record, exc.read())
                except Exception:
                    record['provider_protocol_error'] = 'unreadable_error_body'
                record.update(status='failed', http_status=exc.code, error_type=type(exc).__name__,
                              retryable=exc.code in (401, 408, 429) or 500 <= exc.code <= 599)
            except Exception as exc:
                record.update(status='failed', error_type=type(exc).__name__,
                              retryable=isinstance(exc, (urllib.error.URLError, TimeoutError)))
            record['finished_at'] = _now()
            record = _save_new(path, record, key)
            if record['status'] == 'completed' or not record.get('retryable') or attempt == MAX_ATTEMPTS:
                return _save_new(final_path, record, key)
        raise AssertionError('Unreachable attempt loop')
