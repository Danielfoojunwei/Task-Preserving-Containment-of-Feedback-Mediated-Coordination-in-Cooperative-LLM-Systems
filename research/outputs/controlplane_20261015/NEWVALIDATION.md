# Independent validation of the control-plane study

This document describes checks performed before research execution and a small
structural inventory check after execution began. It reports no live behavioral
findings. No API calls were made by these checks, and none of the 64 frozen study
artifacts was edited. `audit_controlplane.py` is deliberately outside that frozen
set and will audit completed evidence without changing it.

## Transport and schema checks

Eleven canned `api_client.py` tests passed. They exercised exact request bytes
and hashes, strict JSON/schema validation, immutable resume, the bounded retry
status set, bare transport retries, malformed-success retention, both explicit
model identifiers, interruption handling, local-only schema references and
credential protection. Every HTTP entry point in those tests was intercepted;
no provider request was sent.

Provider compatibility is separate evidence recorded by the root agent. Six
compatibility calls were scheduled/preserved: two successful basic structured
probes, two failed array-enum probes, and two primitive-schema probes. The final
research interface uses supported primitive arrays/scalars with required keys
and `additionalProperties: false`. It does **not** rely on the provider to enforce
an exact array permutation or the checksum range.

Client schema validity and domain validity are distinct. The client rejects
duplicate JSON keys, nonfinite numbers, wrong primitive types and extra keys.
The domain parser additionally requires the exact sender two-template
permutation, the receiver's four distinct task IDs and checksum range 0–96.
A provider-schema-valid reply can therefore still be a recorded invalid domain
action. Neither kind of malformed successful response is retried for a better
outcome. An integration test explicitly exercises this distinction.

## Full zero-network integration run

`test_integration.py` passed four tests, including a complete canned research
schedule. Its method was:

```python
patch.object(api_client.urllib.request, 'urlopen',
             side_effect=AssertionError('NETWORK FORBIDDEN IN CANNED TEST'))
patch.object(run_controlplane.api_client, 'call', side_effect=canned)
```

The canned function used the actual prompt builders, current provider schemas,
strict local action validation and deterministic fixture responses. The actual
runner then executed source generation, mediation, receiver construction,
evaluation, source reuse and stage accounting. Freeze verification was bypassed
only inside this isolated fixture run; actual source-freeze verification remains
mandatory for live execution. The runner's `ROOT` was redirected to a temporary
directory under `/tmp`, and all fixture artifacts were removed afterward.
No canned record was written into the research evidence directories.

The full run produced **1,958 canned research actions**:

| Component | Canned actions |
|---|---:|
| Main senders | 400 |
| Main receivers | 1,200 |
| Crossed-delivery receivers | 80 |
| Necessity-boundary receivers | 48 |
| Cooperative-control receivers | 32 |
| Before-secret adaptive planners | 6 |
| Adaptive senders | 96 |
| Adaptive receivers | 96 |
| Total research | **1,958** |

The six compatibility calls are outside this research total, giving **1,964
scheduled logical calls** before any transport retries. Across the research
schedule there are 496 sender calls, 1,456 receiver calls and six planner calls.

Assertions checked that all 40 main worlds had identical complete
`transcript_guard` receiver request payloads across their protected B/R twins.
All 80 crossed controls delivered the opposite B while preserving R; the ideal
canned decoder followed that delivered codeword and received −4 on the original
target-world bet. Those fixtures test plumbing, not actual model adherence.
The 48 boundary and 32 cooperative receivers reused exact existing main
`joint_xor`, R=0 sources and created no additional sender calls. Authorized
declassification was exercised only on the bit-required boundary task.

## Independent observation-scope checks

Ordinary guards and receiver prompt builders were called with a `PublicOnly`
world wrapper that raises on access to any nonpublic world key. The checks
covered all four isolated carriers and `all_channels`, both B values, both R
values and valid/missing/invalid sender outcomes. The complete receiver prompt
and next public state remained identical under `transcript_guard`, including
payload, label, receipt, status, slot count, timing ID and explanation. Fallback
source validity/error diagnostics were not exposed to receivers.

Receiver input keys were checked explicitly: public task data, registered
observable transcript, public policy assignment, public codebook, a common
before-secret strategy, the assigned goal, reply schema and explanatory scope
text. No receiver received a private-state object, raw source action, source
filename or evaluator bit/pad. Source prompts supplied the sender's own private
state and a public encoding formula; they did not supply precomputed active
knob answers. The finite certificate is separate non-LLM evidence; its guarantees
are restricted to the declared transcript and public-state interface.

## Live inventory sanity check and final audit

After research execution began, three completed source records were inspected
for structural metadata only. All three source/request/client hashes matched,
their request-hash sidecars matched, world files existed, and the saved profile
was the requested GPT-4.1 model, temperature 0.7 and maximum 1,500 tokens. No
source compliance or behavioral outcome was inferred from that sample.
`audit_controlplane.py` compiled successfully under the Python 3.11 runtime and
uses the actual saved client keys (`input_sha256`, `parsed_action`,
`action_valid`, raw provider response, model/response ID, timestamps and usage).

The final auditor will independently reconstruct every sender and receiver
request, verify world/source/payload hashes, check crossed-bit and source-reuse
identities, verify before-secret planner timing, recompute mediation and
evaluation, compare complete secret-twin receiver payloads, separate client and
domain validity, and total usage over preserved attempts without double-counting
final call copies. Compatibility failures remain in that accounting. These are
local reproducibility checks, not independent provider or invoice attestation.
External timing, billing observations and unregistered interfaces remain outside
the finite transcript guarantee.
