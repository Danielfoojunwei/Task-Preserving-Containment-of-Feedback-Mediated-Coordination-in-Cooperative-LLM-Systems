# Repeated-reciprocity release builder

This directory contains a downstream, offline presentation builder. It does not
call a model, load raw calls, run the frozen analyzer, or edit the study. The
study and its earlier null results remain separate records. The builder makes
no claim that a harmful action proves an agreement.

Run only after the prefix-selection reviews have been sealed and the parent
researcher has released the validation analysis:

```bash
python research/outputs/reciprocity_release_20261016/build_release.py \
  --analysis research/outputs/reciprocity_causal_20261016/ANALYSIS_VALIDATION.json \
  --manual-review /path/to/released_manual_review.json
```

The optional `--manual-review` (also `--manualreview`) input is copied verbatim
into the replay's evidence-review panel and hashed in the build manifest. The
builder does not infer a manual confirmation from an automatic label, count
confirmations from an unknown schema, or treat an assigned pact as independent
formation. Without this input the replay explicitly says that a released manual
review was not supplied. Do not supply private working notes or unreleased
review records.

Incomplete validation, missing pilot prerequisites, or a mismatched primary
schema fail before any result artifact is written. A complete primary release
requires all 68 sessions and 16 matched blocks, the three frozen contrasts, and
the predeclared 20,000-bootstrap intervals. The builder reads the analysis
output; the independent raw-record verifier remains the source of verification.

Outputs are `primary_effects.png/.svg`, `main_descriptive.png/.svg`, CSV tables,
`RESULTS_TABLES.md`, a self-contained `replay.html`, and a SHA-256
`BUILD_MANIFEST.json`. If complete conditional continuations are present, each
cohort gets a separate continuation plot. Main validation, assigned controls,
cooperative controls, and selected continuations are never pooled.

The forest plot uses the **16 randomized matched blocks** as its inference
unit. Its intervals are descriptive 95% paired-block bootstrap intervals; raw
exact and Holm-adjusted p-values are both shown. Round/action counts shown in
descriptive tables are denominators, not additional independent samples.

The replay shows only actual recorded amounts and task outcomes from the
released analysis. Its receipt-gate toggle recomputes payments and reviewer
liability from those same proposals. It does not generate a new agent response.
Preserving the valid payment component is a pointwise property; it does not
guarantee complete reimbursement, correct sorting, or an end to agreement.
Conditional live gates are disclosed to agents and change both information and
enforcement. Dropping future notes retains the existing round-2 history.

Dependencies: Python 3.11+ and Matplotlib. There are no external web resources
in the generated replay. Fonts and SVG hash salt are fixed; SVG trailing
whitespace is normalized. Source and output hashes provide provenance, not an
external timestamped preregistration.

`package_evidence.py` is a separate explicit packaging command. After both
studies and their release have been completed and approved for outcome release:

```bash
python research/outputs/reciprocity_release_20261016/package_evidence.py \
  --out /workspace/exports/reciprocity-evidence-20261016.zip
```

It includes all three complete new study trees, this release tree, the five-slide
presentation in `presentations/reciprocity_20261016`, and the unchanged borrowed
`controlplane_20261015/api_client.py`. It verifies every referenced
freeze hash, excludes credentials/environment files and transient files, rejects
source changes during packaging, and preserves each archived source's byte
hash, size and nanosecond mtime in `SOURCE_MANIFEST.json`. Its generated restore
helper verifies bytes before restoring local mtimes. The generated offline
verification driver runs all three folders' tests and independent verifiers with the
OpenRouter key removed, retaining logs outside the archive. Building an archive
does not itself run those checks or externally attest chronology. Existing
archive destinations are never overwritten.

After the separate supplemental analysis is released, build its two-contrast
forest plot, six-panel descriptive figure, CSV tables, and optional five-test
joint multiplicity table with:

```bash
python research/outputs/reciprocity_release_20261016/build_supplement.py \
  --analysis research/outputs/negotiation_causal_20261016/ANALYSIS.json
```

This requires all 24 supplemental sessions and 864 calls to be complete, and
uses eight randomized matched blocks. The directed-minus-plain contrast assigns
a negotiation instruction bundle; the second contrast tests note delivery within
that directed setting. Neither identifies an individual wording ingredient or
a wording-by-delivery interaction. The optional joint Holm (5) table reads
already released adjusted values and preserves the original Holm (3) and Holm
(2) reports. Supplemental observations are never pooled with the main study.

The final combined entry point is `evidence_replay.html`. It retains separate
parent, negotiation-supplement and adaptive-defense cohorts and separate review
scopes. Seven overt agent-originated pacts have exact round-1 proposal/acceptance
quotations; no strict-covert success is inferred. The default view is directed
world 9301. `replay.html` remains the historical main-study-only view.

Rebuild the combined replay and copy the verified presentation defense figure:

```bash
python research/outputs/reciprocity_release_20261016/build_combined_replay.py
```

`COMBINED_REPLAY_BUILD_MANIFEST.json` hashes all input analyses, independent audit
reports, review sources, literal-prefix packets, builder sources and copied
figure assets. Each displayed actual payment, excess, reviewer-liability score,
net owner loss and receipt coverage is reconstructed from recorded proposals.
`adaptive_defense.png/.svg` are exact copies of the presentation's verified
`defense_outcomes` assets. The separate adaptive-defense study includes all eight
directed round-2 contexts, three branches and two fresh cases per branch, without
judge-label or profit selection. These descriptions add no p-values.

The focused archive covers these three new studies and their release and
presentation. Historical-context links outside these trees require the full
repository; older studies are not recursively bundled.
