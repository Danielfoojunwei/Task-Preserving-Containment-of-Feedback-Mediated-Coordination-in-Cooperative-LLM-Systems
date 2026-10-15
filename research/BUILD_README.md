# Task-Preserving Colosseum Research Overlay

**What exists:** a runnable offline test suite, a pinned-runtime integration adapter, a 40-episode pilot manifest, exact small-instance reward evaluation, an evidence-aware analyzer, and an OrchDebate-inspired structured-state / skill interface.

**What does not exist yet:** a remotely created GitHub fork from this session, a successfully executed full pinned runtime, live LLM results, a learned/self-evolving OrchDebate implementation, or a validated anti-collusion defense.

The GitHub connector available during this build exposes reads but no fork/branch/push actions. Container network/DNS and model credentials were also unavailable. The authenticated connected login was `danielfoojunwei774`; no accessible Colosseum fork was returned. The script below performs the requested authorized fork and publication in your authenticated terminal. It does not ask you to recreate the research code.

## 1. Validate the local build (no GitHub or model calls)

```bash
cd colosseum_task_preserving_starter
python -m pytest -q
python -m kinetic_audit.design --out configs/pilot_manifest.json --split pilot --seeds 5
python -m kinetic_audit.run --upstream /path/to/colosseum \
  --manifest configs/pilot_manifest.json --index 0 \
  --model-config configs/model.example.json --out outputs
```

The last command is a dry run, even with a real model key in the environment. Test dependencies: Python >=3.11 and pytest. Installed runtime adds dependencies through Colosseum's lockfile.

## 2. Create the real user-owned fork and publish ONLY the research branch

Install/authenticate GitHub CLI in your own terminal, then run:

```bash
gh auth login
bash scripts/fork_and_publish.sh --publish "$HOME/colosseum-research"
```

The script verifies the authenticated owner, creates/reuses `danielfoojunwei774/colosseum`, verifies that its parent is `umass-ai-safety/colosseum`, clones it, starts `research/task-preserving-collusion` from the pinned upstream commit, copies this overlay into `research/kinetic_audit`, commits only that directory and pushes only the research branch. It disables pushes to the upstream remote. It does not force-push, modify main, open an upstream pull request, or launch a model.

The files in this ZIP are a **research overlay**, developed on a separate local Git branch; the ZIP does not contain Git history. They are not a GitHub fork or a reconstructed upstream checkout. Do not push it directly into Colosseum. Use the supplied script to place it on real upstream ancestry. The script has been syntax-checked and dry-run locally, NOT run against GitHub.

## 3. Install pinned runtime and run the no-model integration probe

```bash
cd "$HOME/colosseum-research"
bash research/kinetic_audit/scripts/setup_runtime.sh "$PWD"
source .venv/bin/activate
export PYTHONPATH="$PWD/research/kinetic_audit:$PWD${PYTHONPATH:+:$PYTHONPATH}"
python -m kinetic_audit.preflight --upstream "$PWD"
python -m kinetic_audit.runtime_probe --upstream "$PWD" --out outputs/runtime_probe_001
```

The probe uses actual installed classes and makes no API/model calls. It does not fall back to mocks. Source drift, import problems, nonreproduced leakage or changed fixed-action rewards produce a failed/blocked gate. Inspect the failure rather than bypassing it. Some environment imports may require the official CoLLAB submodule; follow the pinned repository README if it is absent.

## 4. One real episode, only after that probe passes

Create a local copy of `configs/model.example.json`, replace the model placeholder with an exact tool-capable model supported by the pinned runtime, and configure its API key as an environment variable. Do not put keys in committed JSON or this chat. Set a hard spending cap in the provider account; this runner is not a dollar-accurate billing firewall.

```bash
# Run at the real Colosseum repository root, with PYTHONPATH and .venv active.
python -m kinetic_audit.run --upstream "$PWD" \
  --manifest research/kinetic_audit/configs/pilot_manifest.json --index 0 \
  --model-config /path/to/local-model.json \
  --runtime-gate outputs/runtime_probe_001/runtime_gate.json \
  --out outputs/ka_pilot \
  --execute-live --acknowledge-provider-billing
```

Explicit flags are required. One invocation executes one cell, with a timeout and a unique output directory. No background runner is installed. A model attempt may incur charges even if it fails; provider retries are not currently instrumented as a billing cap. This live integration has not been end-to-end verified in the build container.

After confirming one cell, execute the remaining manifest indexes deliberately, preserving the manifest and reporting all failures. Do not use the same output path to overwrite a failed run. Label explicit reruns with a new run directory and preserve originals.

## 5. Analyze real results (synthetic data are rejected)

```bash
python -m kinetic_audit.analyze \
  --manifest research/kinetic_audit/configs/pilot_manifest.json \
  --results outputs/ka_pilot --out outputs/analysis.json
```

`ka_result.json` distinguishes `LIVE_LLM`, failed live attempts, and unexecuted cells. The analyzer checks task fingerprints before paired comparisons and never replaces a missing episode with zero harm. Five seeds are an exploratory pilot, not adequate evidence for broad safety claims.

## File map

- `docs/EXPERIMENT_PROTOCOL.md`: entire setup, MECE framework, H0-H5, arms, estimands, controls, statistics, caveats.
- `docs/ORCHDEBATE_MAPPING.md`: verified inspiration vs proposed adaptation vs implemented functionality.
- `kinetic_audit/instrumentation.py`: board/callback/recipient tracing, late revocation, feedback guards, rule selector integration.
- `kinetic_audit/run.py`: hash-checked upstream runner integration; no edits to upstream files.
- `kinetic_audit/runtime_probe.py`: installed-runtime, zero-model gate.
- `kinetic_audit/core.py`: typed state, skill proposals, immutable local ledger.
- `kinetic_audit/oracle.py`: exact enumeration through upstream task rewards.
- `kinetic_audit/design.py`, `analyze.py`: randomized manifests and evidence-aware analysis.
- `scripts/fork_and_publish.sh`: authenticated fork/research-branch setup.
- `tests/vendor/`: byte-exact MIT-licensed pinned Jira tool used in fixture tests, with license.

## Safety and evidence scope

Only artificial benchmark data; no production accounts, real workplace allocation, or real private costs. Raw host traces contain benchmark private states and belong outside agent tool access. This package's local hash chain is not independent attestation. The reference hypothesis concerns numerical feedback, not all possible communication. An actor can retain old messages, infer through task choices, or share information through authorized text. No intent inference from conversation or coordination alone.

Pre-sprint source analysis and toy results belong in the prior-work disclosure. Fresh sprint runs, when executed, must be identified separately. Do not lead a paper with a software-test count as evidence of live defensive success.
