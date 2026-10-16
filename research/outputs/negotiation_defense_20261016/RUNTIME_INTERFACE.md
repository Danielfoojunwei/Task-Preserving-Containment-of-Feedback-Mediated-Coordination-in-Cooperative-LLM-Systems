# Separate adaptive-defense continuation interface

This study is separate from both frozen earlier studies. It imports their code
read-only and does not revise their plans or modify any earlier artifact.
`run_study.py` has `prepare`, `freeze`, and `run` commands, accepting optional
`--directory`. Root alone prepares, freezes, and launches. No network occurs
at import, during prepare, or during freeze.

`plan.json.sources` includes **all eight** supplement `directed` worlds from
blocks 9301–9308, without selection on agreement judgments or monetary results.
Each is the original session spec plus `source_state_path`,
`source_state_sha256`, and local `snapshot_path`. The original source is exactly
`../negotiation_causal_20261016/runs/validation/{session_id}/rounds/2/end_state.json`.
Prepare copies its original bytes into
`sources/{session_id}/round2_end_state.json`; it does not summarize or reconstruct
the state. Original and local snapshot hashes are frozen before new calls.
Source validation rejects notes/actions/cases later than round 2 and requires
round ledgers exactly 1 and 2. No original rounds 3–4 are copied or delivered.

`plan.json.jobs` contains 24 `{session_id,branch}` jobs in a frozen random order.
Every source has `unchanged`, `no_future_notes`, and
`live_receipt_gate_disclosed`. `plan.json.continuation_cases[str(block)]` is
exactly the parent's `make_cases(block+100,start_round=3,count=2)`, supplying two
fresh alternative cases numbered 3 and 4. Every branch from a source gets the
same cases and independent copies of the exact round-2 state.

The supplement's directed negotiation paragraph remains unchanged in every
branch. The parent branch engine controls actual delivery and settlement:

- `unchanged` retains note delivery and baseline monetary rules.
- `no_future_notes` retains every past delivered note but sends each newly
  authored note only to its author. Claims and settlement remain observable as
  declared previously; this is not complete channel removal.
- `live_receipt_gate_disclosed` truthfully announces the parent's receipt gate
  and actually settles `min(claim,peer approval,trusted receipt)`. Approval
  liability is computed from actual post-gate excess. All other prompts,
  objectives, directed negotiation scaffolding and case inputs are preserved.

Actor/judge models, temperature, limits, independent memories, owner projection,
per-field validation, prefix-only judgment and immutable transport are inherited
unchanged. Each branch has two rounds, each with eight actors plus one prefix
judge: **384 actor calls plus 48 judge calls, maximum 432**. The first planned
actor call is the auth test and is resumed without a duplicate transport call.
There is no new pilot or replacement world; the parent preflight must pass.

Paths preserve the parent continuation schema:

- `calls/continuations/{source_session_id}/{branch}/r{3|4}/{call_id}/` stores
  requests, attempts, provider responses and budget reservations.
- `runs/continuations/{source_session_id}/{branch}/rounds/{3|4}/` stores exact
  start/end state, parsed actions, checkpoint, review packet, judge and outcome.
- Call IDs remain `n1_A,n2_B,n3_A,n4_B,prefix_judge,claim_A,claim_B,review_A,review_B`.
- `continuation_completion.json` reports completion/failures and cost accounting.

All action/state/outcome field meanings follow the frozen parent
[interface](../reciprocity_causal_20261016/RUNTIME_INTERFACE.md). Note and report
privacy, literal quote/delivery validation, and independent monetary parsing
remain unchanged. Prefix evidence never receives current or future actions.

The new study has a separate **$5** cap. Previous caps remain $25 for the parent
and $10 for the negotiation supplement; unused amounts cannot be borrowed.
Their sum bounds aggregate authorization at $40. The imported module instance's
runtime cap is set to $5 only in this process. Conservative pre-call reserves,
known actual-cost replacement, unknown-cost retention, cross-process locking,
persistent transport halts and three-session concurrency are inherited.

The freeze hashes local runner/tests/interface/protocol, independent verifier
and tests, descriptive analysis, plan, prompt material, every local source
snapshot and original round-2 source, and all imported parent/supplement runtime,
interface/protocol/rubric/freeze/verifier references plus the borrowed client.
Both earlier freezes are checked again before launch.

Results support descriptive branch comparisons conditional on these eight
source histories. No new p-values are calculated. All eight sources are kept,
including sources without an accepted agreement, refusals, malformed outputs,
unilateral outcomes and failures. A gate can contain payments while attempted
coordination persists; this does not demonstrate that agreement intentions end.
