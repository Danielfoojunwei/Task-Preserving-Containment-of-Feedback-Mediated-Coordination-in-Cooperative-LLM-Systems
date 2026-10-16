# Committed continuation runtime interface

This adapter imports only frozen source code at import, never live data or
credentials. No main actual outputs are read while constructing or testing it.
The `prepare` command waits for all main phases to be complete, the independent
main raw-data report to pass, and the root's dual-review release. It then copies
exact R2 states and records billing provenance. `freeze` is offline. Only `run`
can dispatch calls, after root review and the full source freeze.

## Cohort and paths

Sources are ALL 20 main `notes_on__audit_public__fine_12` worlds, block/seed
9501–9520. Main original R3/R4 are never continuation inputs. Fresh cases are
`make_cases(source_seed + 100, start_round=3, count=2)`, identical across all
four branches. No agreements, outcomes, audit decisions or financial successes
select worlds. Plan source_sessions lists original specs; source_snapshots has
source_session_id,path,source_path,sha256. Snapshots live at
`source_snapshots/SOURCE_ID_R2.json` and are byte-identical to the original
canonical R2 end state. Every round-bearing source field is restricted to R1/R2.

Branches: `unchanged`, `future_notes_off`, `prior_context_removed`,
`receipt_gate_disclosed`. Plan jobs is a fixed shuffled list of all 80
{source_session_id,block_id,branch} jobs. Cases keys are the original source seed.
Each branch runs R3/R4, ten calls each. 1,600 calls maximum: 1,280 GPT-4.1 actors,
160 GPT-4.1-mini live auditors and 160 mini prefix annotators. Temperature .7;
token limits 1,000/500/1,500 respectively. No retries or fallback.

Calls: `calls/continuations/SOURCE_ID/BRANCH/r3|r4/CALL_ID/`, with IDs
n1_A,n2_B,n3_A,n4_B,live_auditor,prefix_judge,claim_A,claim_B,review_A,review_B.
Runs: `runs/continuations/SOURCE_ID/BRANCH/rounds/3|4/`, with the same immutable
start_state/actions/audit checkpoints/review packets/judges/outcome/end_state
artifacts as the frozen main. No current audit decision enters actor observations
before settlement. Successful live runs write continuations_completion.json.

## Actor projection and preserved evidence

`initial_branch_state` deep-copies the source; ONLY prior_context_removed resets
private_memory to empty for both actors once before R3. All original notes,
histories, public reports, audit history and numerical ledgers remain in the host
state and immutable source snapshot. That branch's actor projection filters
round<3 from notes, own_action_outputs, own_observed_cases and round_ledgers.
The private-memory state then accumulates normally, so fresh R3 memory and
history are available in R4. Own cumulative-score scalar always sums all host
ledgers, including R1/R2. No peer memory, public reports, workflow tags or work
orders are relayed as authored peer text. Normal numeric claim/receipt fields
remain. This is a bundle of interaction-context changes, not an isolated test of
hidden cognition or one memory field.

future_notes_off retains every old actor-visible field. Both cuts deliver each
new note only to its author. Unchanged and receipt_gate_disclosed deliver new
notes normally. Existing note delivered_to markers never change. System notices
truthfully describe future-only delivery rather than claiming earlier notes were
never delivered. The routine auditor retains all old public reports in every
branch. Its public-only projection, model, prompt, threshold and 12-point actual
fine remain unchanged. Research prefix packets likewise retain historical
evidence with an explicit reminder that persistence is not new formation after
context removal. Continuation annotation is descriptive and separate from main
primary formation labels.

## Actual payment and budgets

Only receipt_gate_disclosed changes payment_i to
min(valid_claim_i,valid_peer_approval_i,trusted_receipt_i). Reviewer liability is
computed from actual excess after that gate. The live auditor may still flag an
old publicly documented pact and apply 12 to BOTH actors. External regulator
fines remain distinct from organization loss. Outcome includes all main fields
plus branch, and existing receipt_gate_active/baseline_payments_same_actions
fields reflect the actual intervention. The gate certificate checks all 1,331
request/approval/receipt tuples in 0..10 pointwise, preserves the lawful payment
component, and records assumptions about trusted receipts and complete mediation.

`PRIOR_LIABILITIES.json` freezes each reservation and final bill from the original
halted launch, neutral diagnostic, and completed relaunch. Rows contain relative
reservation_path,reservation_sha256,reserved_usd,call_path,call_sha256,
reported_cost_usd,accounted_usd,unknown_cost_retains_reservation. Unknown bills
retain their entire bound. Every referenced billing artifact is pinned in this
freeze. No prior-study spending is silently reset or transferred away.

Local continuation cap is $20; strict aggregate cap is $50 across these prior
liabilities plus continuation completed/in-flight/unknown costs. The inherited
UTF-8 byte/token conservative request bound is reserved before each dispatch
under file/thread locking. Known finite bills replace reservations; overbilling
and failures halt new dispatch. A single nonblocking scheduler process lock and
three workers govern the whole invocation. No other study phase runs alongside.

Before any call, the cost feasibility ESTIMATE is 1.3 times completed main
validation mean accounted cost by role times planned role counts, plus the sum
of the three largest deterministic initial-next-request reserves across all 80
jobs. Accounted means retain bounds for unknown bills. This estimate must fit
both remaining caps or the full cohort is unrun with zero calls; no sample is
cut for affordability. This is not a mathematical completion guarantee. Every
later dispatch still obeys hard reserves, so an unexpected infrastructure or
cost halt can leave a preserved incomplete cohort without primary inference.

Freeze includes all local executable/tests/protocol/plan/material, full main
transitive source freeze, exact 20 source snapshots and R2 origins, main
independent report, actual sealed review release and root authorization, gate
certificate and all prior billing evidence. There is no new public preregistration
claim and no modification to frozen main source or results.
