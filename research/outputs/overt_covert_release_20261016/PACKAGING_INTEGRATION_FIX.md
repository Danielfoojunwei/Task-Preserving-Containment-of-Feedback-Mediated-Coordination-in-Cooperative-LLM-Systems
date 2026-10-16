# Packaging integration correction — 16 October 2026

The first actual packaging attempt stopped before ZIP creation. Its retained
log, `/tmp/overt-covert-package.log`, reports `ValueError: independent primary
source hashes do not bind included inputs` at the original
`package_evidence.py:258`. Packaging and offline validation still expected five
primary-check hashes. The passing independent primary report correctly contained
six: verifier, plan, raw audit, sealed reviews, analysis, and
`source_binding_validator` for the release's `source_bindings.py`.

Both packaging and offline validation now require exact equality with all six
hashes, including the included validator's bytes. The archived and newly
reproduced primary checks use the same contract. Missing, incorrect and extra
hash entries remain errors; no field is ignored and no comparison is relaxed.
The actual archived primary report passes this six-input check. Its validator
hash is `6e69c93ebff0e17cd611eb3f090bd2362d8fe563fa08e8be58a1810b6e841f78`.

Affected synthetic checks passed: **32 portable tests and 13 source-binding
tests (45 total)**. Seven new regression tests reject a missing/wrong validator
hash or extra hash in either contract, and reject changed validator bytes in
both. The existing full synthetic reproduction now checks all six pins in both
archived and reproduced reports. The earlier full-suite receipt is retained;
these additional guard regressions are a separate check.

The next actual export exposed a performance defect before ZIP creation. The
audited-artifact inclusion guard repeatedly searched the sorted list of roughly
63,000 files for roughly 62,000 artifacts. The coordinator stopped only that
owned exporter after more than three minutes at full CPU; no source or model
process changed.

`build()` now caches `file_set = set(files)` immediately after collection. Raw
audit, review seal, continuation report and every audited-artifact membership
check use that exact set. The sorted list still determines archive order, and
the second collection/list equality and source-signature checks remain intact.
This removes quadratic membership work without changing an evidence guard.

Two additional structural regressions passed: a list subclass rejects every
linear membership request while a full synthetic main/continuation package
still succeeds in sorted order; omitting one audited source still fails before
archive creation. The affected suites now pass **34 portable + 13 source-binding
tests (47 total)**. These counts supplement the retained earlier receipts.

This corrects an offline integration contract. No frozen experimental code,
audit report, analysis, label, scientific outcome or report PDF changed, and no
model/API call was made. A fresh actual package and complete offline
reproduction are still required after this correction; this note does not
claim those later steps have already passed.
