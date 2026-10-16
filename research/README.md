# Research implementation and frozen evidence

This directory imports the complete local research overlay and its studies. `IMPORT_MANIFEST.json` records source-byte hashes and the eight pilot-result links relocated to work after cloning. Venvs, caches, runtime locks and PID files are excluded. The original development README is retained unchanged in [BUILD_README.md](BUILD_README.md); its early “no live results” statements are historical.

Current findings and limits are in the [contribution ledger](../docs/RESEARCH_CONTRIBUTIONS.md), [main manuscript](outputs/controlplane_20261015/PAPER_CONTROLPLANE.md), [earlier extension](outputs/multiscenario_20261015/PAPER_EXTENSION.md) and [corrected Jira report](outputs/revision_20261015/REVISED_EXPERIMENT_REPORT.md). Original nulls, malformed responses, failed compatibility requests and prospective source freezes are retained.

The [16 October agreement/defense report](outputs/reciprocity_release_20261016/REPORT.md)
covers 3,996 new unique calls. Seven explicitly negotiating pairs originated
overt prohibited terms; blocking future notes did not change financial harm in
eight continued source worlds. Live receipt enforcement contained all excess
while unsupported proposals continued. Five primary causal contrasts remain
unsupported after multiplicity correction. New studies ran on Python 3.12.14;
their 105 offline tests and three independent raw-record audits pass. See the
release README for standalone offline verification and packaging commands.

Use Python 3.11. Core software checks require the project's `test` extra. Saved analysis additionally uses NumPy 2.2.6 and jsonschema 4.26.0; plots use Matplotlib 3.10.8. No credential is needed for the checks below.

```bash
python -m pip install -e 'research[test]' numpy==2.2.6 jsonschema==4.26.0
python scripts/verify_research_snapshot.py
cd research
python -m pytest -q tests
cd outputs/controlplane_20261015
python -m unittest -q test_api_client test_integration
```

From the repository root, regenerate both latest frozen primary analyses on copies, with network access blocked by the wrapper:

```bash
python research/outputs/controlplane_release_20261015/reproduce_offline.py --out /tmp/controlplane-reproduced
```

The older extension wrapper accepts an explicit imported source root:

```bash
python research/outputs/research_extension_20261015/reproduce_offline.py --source-root research/outputs --out /tmp/earlier-extension-reproduced
```

Native live-runtime work uses upstream Colosseum commit `b077fe7e2f10566e92156cc12e06ffb2aac54790`, CoLLAB submodule `018c9e4229d2c5d980285f25be3cca8d1508140f`, and Terrarium 0.1.1. That separate upstream checkout was clean; it is not vendored here. Follow [runtime setup](scripts/setup_runtime.sh) in the pinned checkout and set `COLOSSEUM_ROOT` to its location. Live flags make paid calls and are not offline reproduction commands.

Frozen records may retain historical `/workspace/colosseum_task_preserving_starter` provenance. That root maps to this `research/` directory. These historical strings were not rewritten because source hashes and exact recorded requests must remain intact. Current repository documentation uses portable links.

The full expanded ZIP exceeds GitHub's single-file limit and is retained as [verified parts](../outputs/bundles/task-preserving-research-20261015-expanded.zip.parts/README.md). Restore the original bytes with `python scripts/restore_bundles.py` from the repository root. The latest control-plane ZIP is available intact under `outputs/bundles/` at the repository root.

This is research evidence and AI-assisted working material. Sprint submission requires the team's own report, author metadata, exact prior/event attribution and the required appendix; it has not been submitted.
