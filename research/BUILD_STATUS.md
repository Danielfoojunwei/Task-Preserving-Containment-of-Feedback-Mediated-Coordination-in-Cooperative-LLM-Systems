# Build status — 14 October 2026

## Completed in this build

- 44 focused tests passed; some execute the byte-exact pinned Jira tool with explicitly labeled surrounding fixtures.
- Generated 40-cell core pilot, 60-cell peer-snapshot ablation, and 160-cell held-out controller-comparison manifests.
- Implemented source-pinned runtime adapter, no-model runtime probe, recipient-specific tracing, fixed feedback guards, exact small-instance reward oracle, rule-based skill selectors and live-only paired analysis.
- Bash scripts passed syntax checks. Fork/publish and model runner dry runs executed with no writes or model calls.
- Missing-runtime gate correctly refused an absent checkout/dependency; this was an absence test, not a successful runtime integration.
- A local overlay research branch was created. It has no upstream ancestry or remote. The publication script places this overlay onto the real pinned upstream ancestry in the authenticated user's fork.

## Not completed

- No remote GitHub fork or branch was created/pushed. The connected GitHub interface exposes no fork/branch/write action. No accessible Colosseum fork was returned for the authenticated user `danielfoojunwei774`.
- No full installed Colosseum/Terrarium runtime was executed and no new LLM calls or agent episodes occurred.
- No causal harm-reduction, noninferiority, spontaneous migration or novelty result is claimed.
- The earlier 1,497-test cumulative package was NOT rerun as part of this build; the 44 tests are a separate focused suite.
- OrchDebate's full PDF remains inaccessible. Only its public title/abstract direction was verified. Implemented selectors are transparent rules with a structured state and approved skill interface, not OrchDebate's learned algorithm. Model-based selection and skill evolution are not implemented.

## Ready to transfer

Run `scripts/fork_and_publish.sh` without arguments to inspect its dry run. Run with `--publish` only in an authenticated GitHub CLI terminal. It verifies the fork parent and owner, starts the dedicated research branch from the pinned Colosseum commit, commits only the overlay directory, and disables upstream pushes.

Read `docs/EXPERIMENT_PROTOCOL.md` for MECE responsibilities, H0–H5, exact arms, evidence requirements, controls, uncertainty and failure handling. Do not bypass the real-runtime probe before live calls.
