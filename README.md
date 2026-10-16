# Task-Preserving-Containment-of-Feedback-Mediated-Coordination-in-Cooperative-LLM-Systems

[Apart sprint alignment](docs/SPRINT_ALIGNMENT.md) · [Submission checklist](docs/SPRINT_SUBMISSION_CHECKLIST.md) · [Execution plan](docs/SPRINT_EXECUTION_PLAN.md). Primary anchor: **Track 3, Q3.1, collusion via actions, tools and side channels**; secondary connection: Track 2, Q2.3, evidence standards. Overview, Resources and Guidelines are mapped. Prior work is allowed with disclosure; current results are dated 15 October. The team-written official-template PDF, short abstract, author metadata and required ethics appendix remain outstanding.

The latest agreement-formation check completed **300 live calls across 30 pairs**. No pair met the frozen standard for a resolved prohibited or strictly covert pact. One conditional-reciprocity case overpaid both agents; a receipt-bound settlement replay removed its 11 excess units while paying all 9 valid units. The complete release preserves negative cohorts, adversarial controls, raw calls and blinded judgments: [report](research/outputs/agreement_release_20261016/REPORT.md) · [interactive replay](research/outputs/agreement_release_20261016/replay.html). This is a bounded payment-defense result, not a demonstrated autonomous covert agreement.

The central metadata result remains the separate **1,320-call held-out validation**: actual information and policy announcements independently changed receiver behavior. See [the unified finding](docs/UNIFIED_RESEARCH_FINDING.md). The earlier control-plane extension completed 2,326 calls, including a decoding follow-up; its original nulls and narrower limitations remain unchanged.

[Latest paper](research/outputs/controlplane_20261015/PAPER_CONTROLPLANE.md) · [Latest evidence bundle](outputs/bundles/task-preserving-research-20261015-controlplane.zip) · [New validation](docs/CONTROLPLANE_VALIDATION.md) · [Results figure](research/outputs/hostmask_20261015/host_masked_composition.png)

The 15 October 2026 live research extension is complete: four new synthetic scenario families, 120 shared planning prefixes, 510 execution branches, and 20 separately registered joint-guard follow-ups. Task actors used GPT-4.1 mini, temperature 0.7, maximum 1,500 output tokens.

[Research bundle](outputs/bundles/task-preserving-research-20261015-expanded.zip.parts/README.md) · [Validation](docs/VALIDATION.md) · [Paper extension](research/outputs/multiscenario_20261015/PAPER_EXTENSION.md)

The supported expanded result concerns host enforcement of resource authorization, capacity and shared budgets. Other guards had null results or utility costs. The bundle preserves these outcomes, the earlier negative study, corrected Jira findings, architectural certificates, exact prompts/responses and source freezes. Source scope distinguishes full native-runtime use from partial paper-inspired component transfers.

The complete implementation and recorded studies are under [research/](research/README.md). Start with the [contribution ledger](docs/RESEARCH_CONTRIBUTIONS.md) for supported findings and scope limits, or [publication notes](docs/PUBLICATION.md) for the imported snapshot and archive layout.

Offline validation uses Python 3.11 and makes no model calls:

```bash
python -m pip install -e 'research[test]' numpy==2.2.6 jsonschema==4.26.0
python scripts/verify_research_snapshot.py
python research/outputs/controlplane_release_20261015/reproduce_offline.py --out /tmp/controlplane-reproduced
```

The expanded ZIP is stored as four byte-verified parts because it exceeds GitHub's single-file limit. Restore it with `python scripts/restore_bundles.py`. The latest control-plane ZIP remains available as one file. Frozen source and raw evidence are preserved; historical absolute workspace paths in provenance map to `research/` in this repository.
