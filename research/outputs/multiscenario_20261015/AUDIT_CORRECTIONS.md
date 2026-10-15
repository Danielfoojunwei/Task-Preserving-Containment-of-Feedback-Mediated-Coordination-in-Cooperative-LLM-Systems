# Corrections to the independent final auditor

The final audit passes with zero errors. These corrections concern the new,
unfrozen audit program; no frozen study source, prompt, response, world, endpoint,
or experiment outcome was edited or rerun.

## Preserved first pass

[FINAL_AUDIT_FIRST_PASS.json](FINAL_AUDIT_FIRST_PASS.json) preserves the initial
49 audit flags. [audit_final_first_pass.py](audit_final_first_pass.py) preserves
the exact auditor source that produced them. The corrected auditor remains
[audit_final.py](audit_final.py).

The first pass already verified all 71 frozen-file hashes, all 2,520 saved
request-to-response/attempt hashes and generation settings, the complete
120-prefix/510-branch schedule, branch guard/ledger replay, and comparator timing.
Its additional reconstructed-prompt check flagged 48 resource requests, and its
analysis-annotation timing rule produced one further flag.

## Exact prompt replay needs the original numerical runtime

The first pass used host Python 3.12.14; the live study used Python 3.11.17 in
`/workspace/colosseum/.venv`. Python 3.12 changed floating-point `sum` behavior.
For two resource instances, this changes the literal representation of the
cumulative numeric preview; one example is `352.90299999999996` versus `352.903`.
That small difference is text inside a model prompt, so an exact audit correctly
cannot ignore it.

[AUDIT_FLOAT_DIAGNOSIS.json](AUDIT_FLOAT_DIAGNOSIS.json) checks all 48 first-pass
request discrepancies. Their only parsed differences are finite `joint_reward`
preview values separated by less than 1e-10. Regenerated and JSON-reloaded worlds
produce the same replay within each runtime; object serialization order was
excluded as the cause. This diagnosis does not relax the final acceptance rule.

Rerunning the auditor in the original Python 3.11 runtime reproduces **all 2,520
provider requests exactly**, including every numeric character. No tolerance or
unexplained mismatch is accepted. Every actual request's SHA-256 also matches its
saved response and attempt record. The auditor now requires the original runtime
and records its version and executable.

## Authoritative source freeze versus redundant annotation

The authoritative `PREREGISTRATION_SHA256.json` already included the final
analysis script and preregistration before any model call:

- Source/hash freeze: `2026-10-15T11:44:17.243636+00:00`.
- First sealed planning-prefix attempt: `2026-10-15T11:44:17.331349+00:00`.
- Redundant `ANALYSIS_FREEZE.json` annotation: `2026-10-15T11:44:34.194393+00:00`.
- First consequential continuation call: `2026-10-15T11:45:04.442409+00:00`.

The initial auditor incorrectly required the later annotation to precede sealed
planning too. The corrected rule verifies the authoritative analysis-source
hash before **all** calls, and separately verifies that the redundant annotation
was recorded with zero execution outcomes available before execution. Comparator
selection remains independently checked after all discovery responses and before
the earliest held-out attempt.

## Passing audit

[FINAL_AUDIT.json](FINAL_AUDIT.json) records zero errors, 71 unchanged frozen
files, 120 complete prefixes, 510 complete branches, and 2,520 unique completed
scheduled calls/attempts. The call and attempt inventories retain requested and
provider-reported models, exact input fingerprints, timestamps and usage.

Reported usage totals 3,505,537 tokens and provider-reported cost 1.5605716 USD.
There are no recorded retries or separate preserved attempts in this suite.
All 81 malformed successful model actions remain in the data as invalid actions;
they were not rerun for better outcomes. This verification makes no behavioral
hypothesis or external billing-attestation claim.
