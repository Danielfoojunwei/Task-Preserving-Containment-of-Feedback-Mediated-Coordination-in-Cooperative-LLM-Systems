# Reproducing the research extension

Verify `ARTIFACT_SHA256.json` before working on the evidence. Original provider responses, requests, failed attempts, synthetic evaluator truth, planning prefixes, source freezes and analysis files are included. Credentials are supplied only through the environment and are not included.

The archive retains the original execution paths as evidence. `reproduce_offline.py` maps those paths in memory to a fresh working copy. It does not edit source freezes or original records, and disables provider network calls. Install Python 3.11 and NumPy 2.2.6, then run from the extracted archive:

```bash
python reproduce_offline.py --out /tmp/collusion-analysis-reproduction
```

This copies the two main datasets and the exploratory joint-guard dataset, regenerates their frozen analyses, and checks that primary estimates/tests and exploratory joint summaries are identical. Regenerated report timestamps and machine-dependent log-file mtime observations are not identical evidence. The source records remain unchanged. The original overlay package is included in `research_overlay/` for trace-chain verification. Statistical tests operate on paired task seeds, not individual actor messages.

The standalone synthetic domains and host components need only the standard library. Their invariant checks use pytest. Matplotlib 3.10.8 generates the exported PNG/PDF scientific figures. The Jira native execution additionally requires Colosseum commit `b077fe7e2f10566e92156cc12e06ffb2aac54790`, its pinned dependencies, and `terrarium-agents==0.1.1`. The original archive's `REPRODUCING.md` supplies its runtime details.

Live runners are evidence-producing programs, not offline checks. They require a configured `OPENROUTER_API_KEY` and make paid calls. Existing completed outputs are immutable; scripts do not rerun successful cells. To run a genuinely new replication, use new output directories and freeze a new protocol before calls. Do not modify a frozen seed, guard or prompt to improve an outcome. The original scripts retain the workspace layout used for execution; document any relocation or implementation changes in a new replication.

`multiscenario_20261015/DEVIATIONS.md` records the receipt-channel audit after the source freeze. The additional joint-guard study has its own protocol and is exploratory. Do not merge it into the four primary tests. The finite host-component tests and certificates are architectural evidence, separate from live LLM behavior.
