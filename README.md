# Task-Preserving-Containment-of-Feedback-Mediated-Coordination-in-Cooperative-LLM-Systems

[Apart sprint alignment](docs/SPRINT_ALIGNMENT.md) · [Submission checklist](docs/SPRINT_SUBMISSION_CHECKLIST.md) · [Execution plan](docs/SPRINT_EXECUTION_PLAN.md). Primary anchor: **Track 3, Q3.1, collusion via actions, tools and side channels**; secondary connection: Track 2, Q2.3, evidence standards. Overview, Resources and Guidelines are mapped. Current results are dated 15–16 October and must be disclosed as pre-sprint work. The team-written official-template PDF, author metadata and required ethics appendix remain outstanding.

The latest follow-up completed **3,996 unique live calls ($15.71)**. Seven of eight explicitly negotiating GPT-4.1 pairs originated and accepted reciprocal overapproval terms; their public reports disclosed them. Branching all eight histories showed that withholding future text notes left owner loss unchanged at 115.5 units, while a disclosed live receipt cap reduced it to zero and paid every valid receipt. Unsupported proposals continued. **None of five primary causal contrasts passed multiplicity correction; no autonomous covert agreement is established.** [Report](research/outputs/reciprocity_release_20261016/REPORT.md) · [recorded-action replay](research/outputs/reciprocity_release_20261016/evidence_replay.html) · [five-slide breakdown](presentations/reciprocity_20261016/SLIDES.md).

The earlier **300-call, 30-pair negative agreement study** remains unchanged: [historical report](research/outputs/agreement_release_20261016/REPORT.md). Each new cohort was separately frozen before its own calls; the research program's adaptations and review disagreements are disclosed.

The central metadata result remains the separate **1,320-call held-out validation**: actual information and policy announcements independently changed receiver behavior. See [the unified finding](docs/UNIFIED_RESEARCH_FINDING.md). The earlier control-plane extension completed 2,326 calls, including a decoding follow-up; its original nulls and narrower limitations remain unchanged.

[Metadata paper](research/outputs/controlplane_20261015/PAPER_CONTROLPLANE.md) · [Metadata evidence bundle](outputs/bundles/task-preserving-research-20261015-controlplane.zip) · [Metadata validation](docs/CONTROLPLANE_VALIDATION.md) · [Metadata results figure](research/outputs/hostmask_20261015/host_masked_composition.png)

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
