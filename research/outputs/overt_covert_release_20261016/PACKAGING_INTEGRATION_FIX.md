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

This corrects an offline integration contract. No frozen experimental code,
audit report, analysis, label, scientific outcome or report PDF changed, and no
model/API call was made. A fresh actual package and complete offline
reproduction are still required after this correction; this note does not
claim those later steps have already passed.
