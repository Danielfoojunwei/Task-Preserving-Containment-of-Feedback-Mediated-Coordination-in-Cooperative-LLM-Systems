# Independent pre-call challenge review

16 October 2026. Reviewer: `mechanism_redteam`. This document reviews the new
prospective protocol; it does not change historical studies or claim a new
experimental result. Initial inspection occurred while the runner, rubric,
analyzer and independent verifier were still being written. Final status is
recorded below after inspecting the executable contract.

## Interpretability conditions

1. **The actual audit happens before current claims/reviews.** Its current-round
   input may contain negotiation reports and earlier action reports, but not the
   current monetary actions. A public disclosure in a later claim/review report
   cannot retroactively trigger the current audit fine. Whole-round concealment
   and pre-action auditor evasion are different outcomes.
2. **Concealment uses the same public-account definition in every arm.** Full
   note access can detect an accepted hiding plan; that is failed evasion, not
   an automatic absence of concealment. Withheld notes make a delivered text
   pact structurally impossible, so the delivery primary concerns retained
   benefit rather than a surprising decline in textual agreement.
3. **Fines affect the returned score and subsequent observations.** Base gains,
   audit deductions and owner loss are separate. An external fine does not
   compensate the owner. Unknown/ungrounded auditor output is retained as
   unknown with the declared no-fine fallback; it is not a valid negative or
   proof that semantic concealment fooled the monitor.
4. **Operational audit and research labels are separate.** A model auditor's
   flag is an actual payoff event, not ground truth. Literal citations validate
   provenance, not semantic correctness. Small frozen scripted controls support
   only their own observed error rates. Accepted agent-originated harmful terms,
   accepted concealment, public disclosure, later execution, paid excess,
   monitor evasion and post-fine mutual benefit must remain separate layers.
5. **The observer contrast is a treatment bundle.** Agents are truthfully told
   the access contract, and actual access changes. The contrast identifies that
   joint interface intervention, not beliefs alone or detector information alone.
   Notes-off full/public auditor projections coincide by construction.
6. **Twenty blocks are the independent analysis units.** Calls and rounds do
   not multiply the sample size. The four prospective pairwise tests use the
   complete matched-world denominator, exhaustive pair swaps and Holm4. An
   untested interaction is descriptive. Prior five corrected nulls remain nulls.
7. **The task deliberately permits the individual-score objective to override
   the fictional reimbursement policy.** Any finding concerns agents under this
   engineered objective and communication interface; it does not establish
   spontaneous misalignment under an ordinary compliant assistant objective.
8. **The monitor's blind spot is engineered.** Trusted numerical receipts and
   payments remain available to a forensic researcher or settlement check.
   Concealing agreement from a text auditor does not conceal the overpayment
   from a party checking that ledger. Same-action receipt-gate replay is offline
   arithmetic unless a separately frozen live branch is actually run.

## Specific issues raised before freezing

| Issue found | Required resolution |
|---|---|
| Initial auditor citation order used lexicographic turn IDs, which place `claim` before `n1` within a round | Use actual stage chronology and verify it independently; prior action reports occur after that round's negotiation |
| Inherited automatic prefix annotation receives the full checkpoint, including prior round ledgers | Remove those ledgers from the annotation input, or disclose that only manual pure-prefix review is ledger-blind; do not call the automatic annotator fully outcome-blinded |
| A round-4 pure-prefix packet omits round-4 claim/review reports | Define the primary public-disclosure endpoint as disclosure by an audit checkpoint, or include the final reports in a separate text-only post-action review; report later leaks separately |
| Removing host arm identifiers does not hide treatment cues in agent-authored text | State that explicit fine/access references in notes can reveal assignment; do not claim guaranteed condition blinding |
| Public reports are owner-facing and never delivered to the peer | Tell the auditor this provenance fact; report-only text can provide corroborating disclosure, but its ordering must not be treated as proof that a peer received a proposal |
| The design note proposed a prepayment audit but the executable protocol selected pre-action audit | Keep the prospective executable protocol authoritative and align other descriptive documents before freezing |

## Final implementation review

The executable runner, analyzer, independent verifier, analysis plan and evidence
rubric were inspected before live dispatch. A separate reviewer run of all new
offline tests passed: **90 passed in 1.14 seconds**. No API call was made by this
reviewer. The two initially failing test fixtures were corrected before this
pass; neither failure was an observed live implementation defect.

The runner now orders citations by physical negotiation/claim/review chronology;
informs the auditor that owner-facing reports are not peer messages; excludes
previous numerical ledgers from the research annotator input; applies real fines
to both scores without reducing owner loss; returns post-fine feedback; withholds
the current audit decision until settlement; and preserves invalid audit output
as unknown under the declared no-fine policy. The analyzer uses the runner's
lowercase `control_gate.json`, requires all 6,608 planned calls and all 80
notes-on sealed review records, validates literal positive evidence and delivery,
and retains the complete four-test family when unclear labels withhold a test.

The frozen endpoint definition in the analysis plan and rubric explicitly limits
P2 to disclosure by a pre-action checkpoint. Round-4 claim/review disclosures are
secondary and cannot retroactively alter the last audit. Both documents separate
accepted concealment from execution/evasion and post-fine benefit from owner
harm. The analyzer reports pre-fine benefit, actual deductions, excess payment,
invalid audits, coverage and sorting separately. These resolve the substantive
issues found during source review.

**No executable blocker to the planned launch was identified.** This is a
pre-call review of a bounded experiment, not an assurance that the monitor is
accurate, that covert pacts will occur, or that a result will identify a general
psychological root cause. The coordinator was separately asked to synchronize
the protocol's call count and condition-blinding caveats before freezing.

One release-stage requirement remains: raw `prefix_review_packet.json` contains
the original session ID, which embeds condition and fine. The manual-review
export must replace that identity with an opaque ID and hash the exported
packet before independent review. The automatic prefix annotator also receives
the condition-bearing session ID; it must not be described as condition-blind.
Even opaque manual packets can reveal assignment through the actors' own
references to fine magnitude or auditor access. This limits blinding and must
remain disclosed. The actual operational auditor does not receive those host
condition IDs or fine fields.

Inspected source hashes (the later canonical experiment freeze remains
authoritative if additional reviewed pre-call changes are made):

| File | SHA256 at final inspection |
|---|---|
| `run_study.py` | `2fe3a6b1ba7cfdd9810fb03387ba91da5dca343f713c4784fdce7c17e391ef3c` |
| `analyze.py` | `67382ad1572e0b8aa9b1f4d24966543b7025b8fee3767fcd62cb3f39ce4f677c` |
| `independent_verify.py` | `ad974286d2398661fc01858d281f428845dc84ccc362fd89c501995ce1a245e5` |
| `ANALYSIS_PLAN.md` | `b64f6e950232c1ee88ec74a5b69c39a77cb8196b62c8733d1d87b3ce692f108e` |
| `EVIDENCE_RUBRIC.md` | `a8feb99ed09f14cdaab56d8509c938a5217964d71f27e5a838f87ecc6710822c` |
