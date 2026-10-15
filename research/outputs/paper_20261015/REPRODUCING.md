# Reproducing this experiment

This archive contains outcomes and exact manifests, not an independently attested
execution record. Artificial benchmark task truth is evaluator-only data.

1. Verify files against ARTIFACT_SHA256.json. Retain preserved_attempts as well as
   successful results; do not select a replacement outcome by reward.
2. Check out Colosseum b077fe7e2f10566e92156cc12e06ffb2aac54790 and install its
   frozen dependencies, including terrarium-agents 0.1.1. The research adapter
   source, tests and original protocol are in research_overlay/.
3. Make the overlay and Colosseum importable with PYTHONPATH. Run the 44-test
   overlay suite, its preflight, and runtime_probe. Compare installed source hashes
   with runtime_gate.json. H5's native-generator smoke checks are recorded in
   h5_runtime_smoke.json. No software test count is a model-episode count.
4. Main model settings are in model.json. Credentials are supplied through the
   environment and the supported network proxy, never committed. This session
   uses OpenRouter's OpenAI-compatible endpoint, https://openrouter.ai/api/v1.
5. Frozen study cells are development_peer_manifest.json (60),
   research_overlay/configs/peer_ablation_manifest.json (60 pilot), and
   heldout_full_manifest.json (200). Eight pilot episodes were reused from the
   earlier live smoke/seed-105 batch and are included in the archive.
6. run_paper.py executes missing cells, freezes the development comparator before
   the held-out stage, and preserves successful outcomes. Its absolute paths
   describe this cloud workspace; adapt those path constants when reproducing
   elsewhere. Run individual cells with kinetic_audit.run to use another layout.
7. EXTENSION_PROTOCOL.md specifies the separate H1 replay and H5 fresh-task
   ablation. diagnostic_h1.py and extension_h5.py implement them. Do not pool
   extension outcomes with the original one-shot experiment. H5's generic
   ka_result.json carries the original first-round task digest; use the explicit
   fresh_task_digest and fresh-round results in extension_result.json for H5
   comparisons. Native scoring remains unchanged in both rounds.
8. report.py recalculates outcome tables, bootstrap intervals, treatment checks,
   missing decisions and the failure ledger from recorded evidence. make_figures.py
   exports PNG and PDF figures. Bootstrap units are task seeds, including in H1.

OpenRouter transport authentication failures occurred during this execution.
The bounded recovery amendment, all failed attempts, and final incomplete cells
are part of the report. SDK/internal retries and provider billing are not fully
instrumented, so reported tokens are not an account billing total.

The history-aware and memoryless selectors are frozen deterministic rules. They
do not implement an LLM selector, learning, self-evolution, or an algorithm-faithful
OrchDebate reproduction. The one-model study is exploratory.
