# Proposed startup instructions — save unconfirmed

The cloud configuration tool returned `CONFLICT / draft_not_editable` when the
updated `start_skill` was submitted on 16 October 2026. It said the current draft
may already be published or publication may be in progress. No configuration
change, credential change, runtime update or publication was confirmed. These
instructions preserve the proposed research-specific extension for later review.
Keep the existing installation instructions and repository requirements.

Use the existing checkout at
`/workspace/Task-Preserving-Containment-of-Feedback-Mediated-Coordination-in-Cooperative-LLM-Systems`
and the pinned `/workspace/colosseum` checkout. Do not create a Git worktree.
The repository's existing `scripts/bootstrap.sh` supplies the normal development
environment when dependencies need installation. Preserve its configured
workspace caches and `COLOSSEUM_ROOT`. No background application server is needed.

Read the latest `docs/VALIDATION.md` and every cohort's `PROTOCOL.md`,
`FREEZE.json`, completion records and independent report before claiming readiness
or results. Prepared code is not evidence that an experiment ran. Preserve frozen
sources and all successful, failed and interrupted requests.

The completed reciprocal-reimbursement evidence is recorded at local commit
`5d9be963`. The separate `research/outputs/overt_covert_mechanisms_20261016`
attempt halted on three HTTP 401 “Missing Authentication header” responses after
13 requests. It has no completed round or main experiment. Do not resume it,
delete its halt file or silently retry its requests.

`research/outputs/credential_transport_diagnostic_20261016` completed 12 neutral
model requests, six sequential and six with at most three workers. This verified
that execution at lower concurrency worked at that time; it did not identify
the cause of the earlier failures. A read-only authenticated key check also
succeeded through the configured proxy.

The separately frozen cohort is
`research/outputs/overt_covert_relaunch_20261016`. It uses GPT-4.1 actors at
temperature 0.7 with 1,000 output tokens; GPT-4.1 mini live auditors with 500
tokens and separate prefix annotators with 1,500 tokens. Its plan contains 160
main worlds, four controls and 48 monitor challenges: 6,608 planned calls.
Three workers and a $49.50 local cap are fixed. All new attempts, diagnostics,
unresolved reservations and any separately frozen continuations must together
stay within the new $50 allowance. Earlier completed studies have separate
recorded budgets.

Never run paid phase CLIs in parallel. Run controls, independent control
verification, monitor challenges and validation sequentially. Check existing
completion and halt files before starting anything. Completed calls are immutable
and reusable offline; do not duplicate them. No model substitution, behavioral
retry or outcome-selected seed replacement is authorized by these instructions.
Any new infrastructure failure requires diagnosis and a separately documented
prospective execution. Existing authorization for the necessary bounded research
persists; do not ask again for a model choice or a secret value in chat.

Use only the inherited proxy, CA trust and existing `OPENROUTER_API_KEY` binding
for `openrouter.ai`. Never print or inspect its value. A placeholder is not proof
of a missing key. Check metadata through the cloud status tool and verify the
actual required operation. Readiness metadata has reported `unknown` even while
individual requests succeeded; report those facts separately.

The relaunch's 93 offline tests are `test_runner.py`, `test_analysis.py` and
`test_independent.py`. Run them with the installed pytest environment from that
cohort directory. `python independent_verify.py --phase all --release --output-dir
independent/final` checks raw evidence offline. Primary numerical analysis requires
all planned requests and sealed independent reviews of every one of the 80
notes-on worlds. Do not infer behavioral findings from partial controls or count
API calls as independent experimental samples.

Any continuation cohort has its own protocol, source snapshots, release guard,
tests, freeze, cost preflight and aggregate-budget accounting. Its prepared files
alone do not establish execution. Consult final completion and verification
records for the latest state. This proposal does not publish the environment or
change the credentials of the currently running task.
