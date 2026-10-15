# Held-out metadata and policy-announcement validation

Completed 15 October 2026. **1,320 planned calls completed** (40 sources and 1,280 receivers), no transport retries, provider-reported cost **$0.371024**. The protocol, implementation, analysis and allocation were frozen before this study's calls. Earlier studies were known; their outputs remain unchanged.

The single empirical result concerns actual information versus the receiver's policy announcement. Joint decoding passed all four prespecified observation ablations on 20 fresh worlds. Independently crossing actual views with the earlier announcement bundles produced 0/80 bets with informative metadata described as uninformative, and 23/80 bets with target-independent metadata described as informative. See [RESULTS.md](RESULTS.md) and [the unified finding](../../../docs/UNIFIED_RESEARCH_FINDING.md).

## Inspect and reproduce without API access

Dependencies used locally: Python 3.11, NumPy 2.3.5, SciPy 1.17.0 and jsonschema 4.26.0. The existing CI pins NumPy 2.2.6, compatible with SciPy 1.17.0. Raw provider records, source snapshots and exact requests are retained in `calls/`, `sources/` and `results/`. Credentials and authorization headers are not included.

From the repository or the complete evidence package root:

```bash
python -m unittest discover -s research/outputs/stability_20261015 -p 'test*.py' -q
python research/outputs/stability_20261015/analyze_stability.py
python research/outputs/stability_20261015/independent_stability_check.py
```

Analysis writes derived `analysis.json` and `RESULTS.md`; the verifier writes derived independent-verification files. It checks raw replies and actions without importing study implementation or analysis code, including exhaustive primary and secondary sign enumeration. Neither command invokes APIs. The 13 runner/analysis tests also run without network calls. The saved `offline_tests.log` records their pre-launch pass.

`FREEZE.json` lists the 12 immutable input hashes and time. The independent report checks that this preceded every retained request and that actual source snapshots preceded host masking. Local chronology and provider records support reproducibility; they are not external execution attestation.

`SIMULATED_ANALYSIS_CALIBRATION.json` contains an optional, fixed-seed synthetic check of Type-I error/power under independent Bernoulli assumptions. It is not observed model data or calibration of a collusion detector.

## Interpretation limits

Sources copy neutrally, the host deliberately creates the known XOR channel, and receivers receive decoding/routing tables. The public task copies supplied answers. The announcement manipulation crosses exact policy/contract bundles; some statements are deliberately inaccurate. Do not interpret this as spontaneous collusion, a universal prompt effect, a production-defense exploit, broad task preservation or zero population error. Bit-classifier error rates, abstention and accepted harmful actions are separate measures. All results are pre-sprint work dated 15 October.

The runner only calls the API through explicit `--run`, with unchanged frozen inputs, its original immutable allocation and the original $5 local reported-cost/reservation ceiling. No additional calls are needed to inspect or reproduce the completed study.
