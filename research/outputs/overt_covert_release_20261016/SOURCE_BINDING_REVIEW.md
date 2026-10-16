# Source-binding review before numerical release

16 October 2026. This concerns unfrozen reporting helpers, not the experimental
prompts, assignments, frozen verifiers, primary endpoints or live execution.
The coordinator and reviewers had not opened the main numerical comparisons.

An independent source-only review reproduced a defect in temporary synthetic
fixtures: changing a saved round-4 claim public report and its matching end-state
entry could pass the initial secondary exporter. The passing raw audit certified
the original files, but the exporter had no preserved inventory connecting its
later reads to those exact audited bytes. The round-4 final report was outside
the sealed primary prefix, so that prefix could not supply the missing binding.
No actual experimental record was changed or used in the reproduction.

The supplemental audit wrapper now captures every semantic `calls/` and `runs/`
file before invoking the unchanged frozen verifier, checks the entire inventory
is unchanged after a passing audit, and exclusively writes a snapshot and
`SOURCE_BINDINGS.json`. It declares only three runtime-lock exclusions:
`.call.lock`, `.budget.lock`, `.scheduler.lock`. Unknown extra files stay bound.

Secondary review, replay, packaging and portable verification require this
inventory and check its raw-report, verifier, freeze and snapshot hashes, its
chronology, and the exact source files. Changed validity flags, coupled
report/state edits, unread wire-call changes and inventory additions/deletions
are regression cases. The original synthetic exploit now fails during packet
construction, final unchanged-source checking and fresh source loading.

The author and coordinator each ran the full 93-case release-helper suite
successfully. The independent critic rechecked the exploit and ran 33 targeted
wrapper/source-binding checks successfully. These are software checks, not
behavioral findings or semantic truth labels. The original helper is retained
in Git history; fixes precede any actual secondary export or numerical release.

Hashes and locally recorded times establish artifact consistency. They are not
external timestamp attestation, public preregistration, or independent proof of
the semantic judgments. Portable reproduction additionally reruns the frozen
raw verifier against the archived wire records.
