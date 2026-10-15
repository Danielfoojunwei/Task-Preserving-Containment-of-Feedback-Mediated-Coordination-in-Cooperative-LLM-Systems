# Causal Audits of Defender-Generated Channels in LLM-Agent Transcripts

**Research manuscript, 15 October 2026.** The main study and separately registered host-masking follow-up are complete. Their unsupported and supported primary results are reported separately, with both local audits passed. No frozen source or original endpoint was changed.

## Abstract

LLM-agent defenses can canonicalize payloads while exposing policy labels, receipts or rejection outcomes. We tested these established mechanisms in a balanced shared-source audit. The main study completed 1,958 research calls using GPT-4.1 mini on 32 worlds per carrier and GPT-4.1 on eight fresh worlds. None of four Holm-adjusted primary contrasts was supported. Interpretation was limited by source encoding errors and 476 checksum-invalid receiver actions whose decoded bits and routes were reset by the frozen evaluator. After these outcomes were known, a separately registered 368-call follow-up moved XOR masking to the host, simplified the public task to copying supplied values, and separated bit scoring from task validity. Its 16-world mini-model marginal-minus-transcript decoding effect was 0.2265625 [95% descriptive interval 0.1796875, 0.2734375], exact paired p=.00006103515625. Individual fields were private in every realized world; mini-model marginal guarding yielded 31 correct and ten wrong accepted bets, realized net payoff +22; transcript guarding produced no bets. Reliably positive mean coalition payoff was not established. Public copy tasks succeeded throughout. This is controlled two-agent capability with an adversarial receiver, not evidence of source intent or emergent collusion. Known XOR composition and noninterference principles are not novelty claims; task preservation is demonstrated only for the simplified task.

## 1. Research question and evidence levels

A validator can commit identical public data yet disclose its selected path, an unused attestation's validity, or a rejection status. We ask whether actual models instantiate and use these carriers, whether information supports profitable owner-harming action, and what mediation costs legitimate work. Encoding feasibility, actual decoding, coalition payoff, and equal-view certificates require separate evidence.

Earlier artifact experiments did not isolate live policy-tag/receipt exploitation; removing receipts did not add demonstrated harm reduction. The main study below remained unsupported. The subsequent host-masking follow-up addresses the measured encoding and task-scoring limitations with a new, prospectively frozen dataset; it does not replace earlier outcomes.

## 2. Prior art and incremental scope

CaMeL explicitly discusses indirect call dependencies and secret-conditioned exceptions, with STRICT-mode dependency propagation [1]. FIDES distinguishes payload-oriented explicit secrecy from noninterference of call sequences [2]. LLMbda identifies policy-block leakage through untracked retries and preserves failed-attempt taint inside retries [3]. A trusted-tool-boundary study reports filtered-row-count oracles [4]. FLAC and Nonmalleable Progress Leakage address authorization-decision confidentiality and progress channels [5,6]. AgentSecBench supplies permitted-leakage projections and paired adversarial/benign testing [7]. Steganography, privilege control, internal-channel audits and secure agent design have further precedents [8–13].

Colosseum supplies objective-grounded auditing [14]; FLOWSEAL supplies provenance and mandatory release checks [15]; OCELOT addresses cumulative inference and colluding sinks [16]. OrchDebate remains conceptual orchestration inspiration with its detailed primary method unverified here [17]. None is fully reproduced or shown vulnerable in its original implementation.

The bounded increment is a balanced causal microbenchmark linking registered host-generated joint metadata to actual receiver decisions and simple-task utility. Control-plane leakage, XOR composition, conditional information accounting and noninterference are established principles. Independent publication-level novelty remains unproven. Versioned overlap analysis and 14 retained primary PDFs appear in [LITERATURE_POSITIONING.md](LITERATURE_POSITIONING.md) and [LITERATURE_SOURCES.json](LITERATURE_SOURCES.json).

## 3. Interface, task and incentives

Each synthetic public world contains four task records with varying priorities and values. The receiver must output every task ID once, ordered by decreasing priority, and compute the sum of their values modulo 97. Those answers are scored from the model response. The host preserves essential public data and commits a valid canonical schedule, but does not automatically complete the receiver's scheduling or arithmetic task.

A sender privately receives a fresh bit B. Joint-channel cases additionally give it independent pad R. Public codebook polarity P and routing challenge C vary by world; the public task, P and C remain identical across that world's secret twins. The sender returns four typed fields: a two-template permutation, a validation-path selector, attestation validity, and a request token. No free-text source message reaches the receiver.

In the adversarial game the receiver may select SAFE, LEFT or RIGHT. SAFE yields coalition payoff zero and owner utility ten. A correct B-conditioned bet—route determined by B XOR C—yields coalition payoff +2; a wrong bet yields −4. Either bet reduces owner route utility to three. Thus an uninformed balanced bet has expected payoff −1, and abstaining is permitted. Risk-neutral profitable betting requires correctness probability greater than two-thirds. Models are assigned an authorized synthetic adversarial objective; successful encoding or harm is not assumed.

We separately record decoded bit, abstention, both types of bet, correct profitable harm, coalition payoff, owner utility, schedule/checksum performance, and action validity. In the main game route utility is independent of arithmetic errors. An invalid receiver action has owner utility zero and failed task coverage, so total harm must be interpreted alongside invalidity and route-only harm rather than automatically attributed to communication.

Receivers see only the public world, serialized registered transcript, public policy assignment, and optional shared strategy prepared before the secret. They do not see B, R, raw source actions, evaluator answers, filenames, response IDs or logs. The instructed main senders receive formulas involving private B/R and public P and must compute their actual output themselves. Host reference encodings are used for checks, not substituted as successful live sender responses.

## 4. Carriers and defenses

| Carrier | Active receiver observation | Registered instructed mapping |
|---|---|---|
| Policy label | PASS/NORMALIZE validation-path label | Label encodes B XOR P; public committed payload is identical |
| Numeric receipt | 0/10 validity receipt from an uncommitted attestation | Receipt encodes B XOR P without changing the committed artifact |
| Rejection status | ACCEPTED/REJECTED request status | Token outcome encodes B XOR P; public artifact remains committed |
| Joint XOR | Label and receipt together | Label encodes independent R; receipt encodes B XOR R XOR P |

In the ideal joint encoding, each field alone has the same distribution under B=0 and B=1, whereas the pair determines B. This is the familiar XOR/one-time-pad composition example, not a new theorem. Actual LLM encoding adherence and observed distributions remain empirical quantities.

The three policies share the same canonical public artifact. `payload_only` preserves the registered active observations. `marginal_guard` fixes the informative field in each single-carrier assay, but preserves the joint label/receipt pair because their **ideal individual** marginals are bit-independent. This is a specified typed stress baseline, not a general inference detector, calibrated budget, or implementation of OCELOT. In the separate all-channels strategy campaign it fixes the label while leaving receipts and status available.

`transcript_guard` supplies a public-state fallback: fixed label and status, receipt derived from committed public state, one fixed release slot, and fixed timing label/explanation. At fixed public inputs, the intended finite interface maps every allowed sender action and registered invalid/missing class to the same transcript and next public state. A public fallback is appropriate here because the main legitimate task does not require B. It is not a general replacement for CaMeL or a proof that every real workflow can hide its decisions without losing utility.

The exhaustive certificate enumerates 16 valid sender actions plus specified missing/invalid equivalence-class witnesses across bits, pads, polarity, challenge, task family and carrier. It measures exact finite-view total variation and ideal Bayes bounds. It covers the declared serializer and typed interface, not every malformed object, compromised host, unregistered tool or unbounded parser failure. Physical timing, caches, API charges and transport-created episode absence are excluded. Fixed slot fields do not claim constant real latency.

## 5. Frozen live design

Primary homogeneous sender/receiver actors use OpenRouter `openai/gpt-4.1-mini`; exploratory validation uses `openai/gpt-4.1` on fresh worlds. Both use temperature 0.7 and at most 1,500 response tokens. There are 32 mini public worlds per carrier, seeds 7301–7332, and eight full-model worlds, seeds 7401–7408. This is not a matched causal comparison between model sizes.

Each world contains B=0 and B=1. The joint assay additionally exhausts R=0 and R=1 at each B. Every actual source response is reused immutably across all three policies, with fresh receiver calls per policy. The completed main-study allocation is:

| Component | Sender/planner calls | Receiver calls |
|---|---:|---:|
| Main four-carrier banks | 400 | 1,200 |
| Crossed delivered-source controls | 0 | 80 |
| Bit-required legitimate-task boundary | 0 | 48 |
| Cooperative public-task controls | 0 | 32 |
| Before-secret strategy generation | 6 | 0 |
| Strategy-generated adaptive campaign | 96 | 96 |
| **Research total** | **502** | **1,456** |

All 1,958 scheduled research calls completed. Six compatibility requests are separate: four supported-format successes and two HTTP400 schema rejections, with no research secrets. Those failures are neither experimental actions nor transport retries. Final supported primitive schemas and stricter host parsers are retained.

Four jobs run concurrently, with dependent actors sequential within jobs. Successful responses, including malformed actions or failed strategies, are never retried for better outcomes. Transport recovery is bounded to three identical-request attempts with all records retained. The $15 local ceiling uses reported costs plus conservative in-flight reservations; it is not a provider account guarantee. The stop rule required any financial or transport interruption to remain explicit incomplete evidence.

The protocol, source, literature and design inputs were frozen before research dispatch. The [preregistration](PREREGISTRATION.md), [manifest](manifest.json), [design cells](design_cells.json), and [64-file hash record](PREREGISTRATION_SHA256.json) are authoritative. This manuscript is a post-freeze report and does not alter them.

## 6. Outcomes and inference

Let q be the receiver's predicted bit, with null/invalid responses assigned q=0.5 for the primary score. Within world w, average q over pads at each bit and define

S(w,g) = [mean(q | B=1,w,g) − mean(q | B=0,w,g)] / 2.

Perfect informative decoding gives S=0.5; constant zero, constant one and all-abstention strategies give S=0. A negative score indicates systematic inversion. Neutral abstention is a scoring convention, not an assertion that the actor successfully guessed. Raw recovery counts treat abstention as unsuccessful and are reported with coverage and conditional accuracy.

The four mini-model primary effects are `payload_only − transcript_guard` S for policy label, numeric receipt and rejection status, and **`marginal_guard − transcript_guard` S for joint XOR**. The last contrast directly tests the field-marginal stress baseline. Joint payload-only comparisons and all full-model results are secondary or exploratory.

The public world is the paired sampling unit: its bits, pads and policies remain together. We use exact two-sided paired sign-flip reference tests via integer-lattice dynamic programming, Holm adjustment across four tests, and 20,000 seeded paired-world bootstrap resamples. Positive mean and adjusted p<.05 are required for primary support. Sign-flip exchangeability/symmetric-null assumptions, discrete resolution and limited power remain explicit. No cell is selected on sender encoding success.

Source adherence, field/joint distributions, profitable harmful action and payoff are separately reported. A significant decoding effect alone does not establish self-benefiting harmful coordination; an uninformed harmful bet can harm the owner while losing coalition reward. S=0 alone does not prove privacy either: other output features or selective abstention could disclose information. Equal complete-input certificates and behavioral inference are separate evidence.

## 7. Main-study controls

The first eight mini worlds add 80 crossed receivers: the opposite-bit transcript is delivered at fixed public task/pad while the original evaluator bit remains fixed. This tests whether decisions follow delivered information; source adherence is assessed against its own bit.

Six planners generate shared all-channel strategies before receiving campaign secrets. Four fresh worlds per model exhaust B/R, with no supplied codebook, feedback search or outcome-based retry. Because source actions differ across policies, these are whole-campaign exploratory comparisons, not shared-source isolation or unconstrained emergence.

Thirty-two cooperative receivers on four worlds per model test owner utility and public-task performance. Descriptive limits are two percentage points subtask loss and five points coverage decline; this bank cannot establish noninferiority.

A further 48 receivers legitimately require the B-conditioned route. They reuse actual main joint sources and compare payload-only, transcript guarding and authorized route declassification. Equal secret-invariant inputs imply at most one-half expected balanced correct routing without authorized information. This standard necessity boundary is separate from harmful betting and complete task success.

## 8. Main-study results

The main study completed all 1,958 research calls and six compatibility requests. The [independent audit](FINAL_AUDIT.json) reconstructed all 1,456 receiver inputs, checked 496 source records and six plans, verified source reuse and 184 full-guard secret-twin equality groups, and reported `PASSED_COMPLETE`. All 64 frozen artifacts were unchanged. There were no research transport failures; the two compatibility HTTP400 failures remain preserved. Recorded provider usage, including compatibility, was 1,946,387 tokens and $1.6241176; it is not an independently reconciled invoice.

### Primary contrasts

All tests use 32 paired mini-model worlds. Effects compare S under payload-only versus transcript guard for the first three carriers and marginal versus transcript guard for joint XOR. Bootstrap intervals are descriptive, not multiplicity-adjusted confidence sets.

| Carrier | Mean ΔS [95% interval] | Exact two-sided p | Holm p | Primary support |
|---|---|---:|---:|---|
| Policy label | 0.015625 [−0.015625, 0.046875] | .625 | .625 | No |
| Numeric receipt | 0.117188 [0.000000, 0.218750] | .0620694 | .125 | No |
| Rejection status | 0.101563 [0.023438, 0.187500] | .0317383 | .125 | No |
| Joint XOR: marginal − full | 0.035156 [0.011719, 0.066406] | .03125 | .125 | No |

None met the frozen four-test support rule. Positive descriptive intervals or unadjusted tests do not override that result. Null support does not establish equivalence or privacy. Main and exploratory estimates remain in [controlplane_results.json](controlplane_results.json) and [CONTROLPLANE_REPORT.md](CONTROLPLANE_REPORT.md).

### Source adherence and the composition claim

All 400 main source actions were domain-valid, but valid formatting did not imply correct encoding. Only 1/32 mini joint worlds and 4/8 full-model joint worlds had all four bit/pad source actions compliant and realized zero individual-field information with one bit of joint information. Many other realized source banks leaked through a single field or carried less joint information. The ideal XOR construction therefore cannot be described as the actual condition achieved throughout this model experiment.

The [source composition audit](source_composition_audit.json) computes exact information quantities for the saved, equally weighted four-cell banks, without inspecting receiver outcomes. These are not calibrated information costs for the stochastic model kernel or evidence of repeated-generation privacy. The conditional chain rule correctly accounts for the ideal XOR pair; failure of an unconditional marginal sum is a classical fact. GPT-4.1's joint decoder abstained throughout, so its zero S is not a successful behavioral demonstration of joint-channel use or a test that cleanly validates containment of an active decoder.

### All-or-nothing action scoring

All 1,958 successful research responses satisfied the client schema, but 476 of 1,456 receivers failed the stricter domain check. Every such failure was an out-of-range checksum: 466 mini and ten full-model responses; 400 failures occurred in the 1,200 main receivers. The frozen evaluator invalidates the **entire** response and replaces decoded bit and route with null when any domain check fails.

Consequently, the primary score measures a usable whole action under that quality gate, not isolated bit inference. Checksumming errors can remove otherwise readable communication responses from decoding and betting endpoints. Retaining this definition preserves the registered test; silently changing it would not. A [post hoc raw-field sensitivity](PARTIAL_VALIDITY_SENSITIVITY.md) found 98 numeric bit reports suppressed by checksum invalidity: 65 correct and 33 wrong. Mini receipt and rejection raw-field effects were each 0.21875, with descriptive intervals [0.109375, 0.3203125] and [0.140625, 0.296875]; post hoc Holm displays were .002698 and .0000839. Label remained 0.015625 and joint marginal-minus-full 0.02734375 [−0.00390625, 0.0625], descriptive Holm .34375. This endpoint was selected after the audit: it is exploratory despite adjusted p-values. Raw proposals rejected by the host are not executed attacks, and none replaces the original four unsupported primaries.

### Harm, controls and interpretation

Some individual bets were profitable, but the main mini payload-only mean coalition payoffs were 0.03125, −0.375, −0.250 and −0.125 across label, receipt, rejection and joint carriers. The joint marginal-guard mean was −0.125 [−0.28125, 0.03125]; the full-model joint arms had no profitable bets. This does not demonstrate a robust profitable joint-channel attack. Owner harm also includes invalid whole actions, so a low-utility record cannot automatically be attributed to secret transmission.

Crossed receipt replay showed an exploratory original-minus-crossed prediction-score contrast of 0.4375 [0.1250, 0.7500], while its conditional-action contrast was zero [−0.2500, 0.2188]. This illustrates why an observation-dependent prediction is not sufficient evidence of profitable behavioral coordination. Other crossed, strategy-generated and utility comparisons remain exploratory. The small cooperative point qualifiers do not establish noninferiority: actual combined schedule/checksum success was poor, including zero complete public-task success in the mini cooperative bank. In the full-model bit-required task, authorized release yielded correct routing in all eight bit cells, yet complete boundary success was only 1/8 because task answers still failed. Correct routing and task completion must remain separate.

## 9. Separate host-masking follow-up

### Disclosed redesign and scope

The user authorized this follow-up after the main nulls, source audit and checksum issue were known. Its [separate protocol](../hostmask_20261015/PREREGISTRATION.md) and six-source freeze preceded all 368 new calls. It has one prespecified mini-model primary, not a retroactive replacement for the original four-test family; there is no global family-error guarantee for the entire iterative research program.

Sixteen fresh mini worlds, 7701–7716, and eight exploratory full-model worlds, 7801–7808, each contain B=0/1. Forty-eight actual sender calls copy B into a boolean Z. Their prompts do not specify malicious intent or require XOR; the source behavior therefore establishes controlled reporting capability, not collusive intent. After each source is saved, the host uses the identical Z for R=0/1 and all policies, releasing label R and receipt Z XOR R XOR P. Each individual field is B-independent for any realized B→Z map; true-bit transmission still requires source adherence.

Receivers use compact public decoding/routing tables. The host provides the varying canonical schedule and checksum; the legitimate task is to **copy** them, not perform arithmetic or general semantic normalization. Bit scoring is separated from domain-task correctness; accepted host bets are still evaluated separately. There are 288 main receiver calls and 32 crossed receivers. Model profiles and risky-payoff rules remain the same.

### Results

All 48 source reports copied their bits correctly. Across all 24 actual worlds, individual-field total variation was zero, retained-pair TV was one and transcript-guard TV was zero; full guarded requests were identical across the four bit/pad cells. These exact properties concern the balanced realized interface, not a new information-theoretic result.

The sole mini primary marginal-minus-full ΔS was **0.2265625 [0.1796875, 0.2734375]**, exact two-sided paired p=**.00006103515625**, on 16 worlds. Exploratory full-model ΔS was 0.46875 [0.421875, 0.500000], on eight fresh worlds. No Holm adjustment is needed for the separately specified single primary. Exact-test assumptions and descriptive-interval limits remain as above.

| Model / policy | Accepted correct bets | Wrong bets | Net coalition payoff | Mean owner utility |
|---|---:|---:|---:|---:|
| Mini marginal guard, 64 cells | 31 | 10 | +22 | 5.515625 |
| Mini transcript guard, 64 cells | 0 | 0 | 0 | 10 |
| Full marginal guard, 32 cells | 4 | 0 | +8 | 9.125 |
| Full transcript guard, 32 cells | 0 | 0 | 0 | 10 |

The mini marginal mean payoff was 0.34375 per cell, with world-bootstrap 95% interval [−0.03125, 0.6875]. Thus realized net +22 is descriptive and does not establish reliably positive mean coalition payoff.

All transcript-guard receivers abstained from decoding and chose SAFE. All 320 receiver actions were schema/domain valid and correctly copied the schedule and checksum. Thus the study records profitable individual harmful bets using jointly informative metadata and preserved **simple public copy utility** under transcript guarding. It does not establish preservation on the earlier arithmetic task or general cooperative workflows.

On eight mini worlds, original-minus-swapped prediction S was 0.4375 [0.234375, 0.593750]; accepted-action S changed by 0.34375 [0.140625, 0.531250]. Swapping delivered source information changed correct bets from 16/32 to 7/32 and payoff from +20 to −50 while the evaluator target stayed fixed. These exploratory results support dependence on the delivered codeword, not just a default correlated with the evaluator.

The [follow-up audit](../hostmask_20261015/FINAL_AUDIT.json) passed under the execution's Python 3.11 runtime: all six frozen files unchanged, 368 unique calls, zero schema/domain-invalid receivers. Full estimates and retained cells are in [analysis.json](../hostmask_20261015/analysis.json) and [extra outcome summary](../hostmask_20261015/HOSTMASK_EXTRA_SUMMARY.json). Follow-up usage was 223,739 tokens and $0.2296432. Combined main and follow-up totals are 2,326 research calls plus six compatibility requests, 2,170,126 tokens and $1.8537608 in stored provider usage, not reconciled invoices.

## 10. Limitations and claim boundaries

The experiment studies a synthetic broker with finite typed fields and intentionally constructible channels. It does not run the full CaMeL, FIDES, FLOWSEAL, OCELOT or OrchDebate algorithms or demonstrate their deployed implementations are broken. Its field-marginal baseline represents a deliberately local distribution check; it cannot inherit the guarantees or failure modes of a calibrated inference-budget system. XOR synergy and exact equal-view reasoning are established information-flow facts.

Instructed formulas test capability. Before-secret strategy generation adds limited plan flexibility but no feedback learning, long-run adaptation, or exhaustive adversarial search. Actors from two related model profiles on different-sized world banks cannot establish broad cross-model generality. Provider versions, stochastic execution, prompt effects and invalid actions limit attribution.

The public tasks are secret-independent; the successful follow-up reduces them to copying supplied answers. Real workflows may legitimately require secret-dependent decisions, meaningful warnings or approvals. Their authorized leakage and utility requirements need explicit policies; silence or falsified status is not automatically a task-preserving fix. The separate necessity task illustrates this boundary without claiming to solve general declassification.

Full-view equality covers only the registered observer. Other principals may see different audit logs, resource effects, costs or timing. Transport failures and physical release absence are disclosed rather than silently counted as private successful episodes. Local hashes and stored provider records support reproducibility, not external attestation. The main four-test family and later single-primary follow-up were each frozen before their own calls; the latter was deliberately designed after known earlier nulls and measurement failures. Independent novelty and general collusion prevention remain unestablished.

## References and source provenance

1. Debenedetti et al. _Defeating Prompt Injections by Design._ CaMeL, [2503.18813v2](https://arxiv.org/abs/2503.18813v2).
2. Costa et al. _Securing AI Agents with Information-Flow Control._ FIDES, [2505.23643v2](https://arxiv.org/abs/2505.23643v2).
3. Garby, Gordon, and Sands. _The LLMbda Calculus: AI Agents, Conversations, and Information Flow._ [2602.20064v2](https://arxiv.org/abs/2602.20064v2).
4. Millstone et al. _If Agents Were Angels, No Governance Would Be Necessary: Out-of-Band Policy Enforcement at a Trusted Tool Boundary._ [2608.27646v1](https://arxiv.org/abs/2608.27646v1).
5. Arden et al. _A Calculus for Flow-Limited Authorization._ [2104.10379v1](https://arxiv.org/abs/2104.10379v1).
6. Cecchetti. _Nonmalleable Progress Leakage._ [2505.12210v1](https://arxiv.org/abs/2505.12210v1).
7. Alpay and Alpay. _AgentSecBench: Measuring Prompt Injection, Privacy Leakage, and Tool-Use Integrity in LLM Agents._ [2605.26269v1](https://arxiv.org/abs/2605.26269v1).
8. Motwani et al. _Secret Collusion among AI Agents: Multi-Agent Deception via Steganography._ [2402.07510v5](https://arxiv.org/abs/2402.07510v5).
9. Mathew et al. _Hidden in Plain Text: Emergence & Mitigation of Steganographic Collusion in LLMs._ [2410.03768v2](https://arxiv.org/abs/2410.03768v2).
10. Roger and Greenblatt. _Preventing Language Models From Hiding Their Reasoning._ [2310.18512v2](https://arxiv.org/abs/2310.18512v2).
11. Shi et al. _Progent: Securing AI Agents with Privilege Control._ [2504.11703v3](https://arxiv.org/abs/2504.11703v3).
12. El Yagoubi, Badu-Marfo, and Al Mallah. _AgentLeak: A Benchmark for Internal-Channel Privacy Leakage in Multi-Agent LLM Systems._ [2602.11510v3](https://arxiv.org/abs/2602.11510v3).
13. Beurer-Kellner et al. _Design Patterns for Securing LLM Agents against Prompt Injections._ [2506.08837v3](https://arxiv.org/abs/2506.08837v3).
14. Nakamura et al. _Colosseum: Auditing Collusion in Cooperative Multi-Agent Systems._ [2602.15198v2](https://arxiv.org/abs/2602.15198v2).
15. Shim et al. _Confuse the Model, Control the Flow: Understanding and Mitigating Privacy Leakage from LLM Agents with Information Flow Control._ FLOWSEAL, [2609.14003v1](https://arxiv.org/abs/2609.14003v1).
16. Xie and Li. _OCELOT: Inference-Leakage Budgets for Privacy-Preserving LLM Agents._ [2606.12341v1](https://arxiv.org/abs/2606.12341v1).
17. _OrchDebate: Adaptive Orchestration for Multi-Agent Debate via Self-Evolving Skills._ [Supplied OpenReview record](https://openreview.net/forum?id=JyJSJitKjy); title/concept follow the supplied mapping, with full primary algorithm unverified here.

Version dates, hashes and exact overlap locators are retained in [LITERATURE_SOURCES.json](LITERATURE_SOURCES.json), [LITERATURE_POSITIONING.md](LITERATURE_POSITIONING.md), and [formal source notes](literature_sources/formal/VERIFIED_SOURCE_NOTES.md). The separately retained RTBAS source is included in that index as additional IFC context, not counted as an implementation reproduced by this study.

Figures: main/crossed tests ([PNG](figures/primary_and_crossed.png), [PDF](figures/primary_and_crossed.pdf)); post hoc sensitivity ([PNG](figures/posthoc_partial_validity_sensitivity.png), [PDF](figures/posthoc_partial_validity_sensitivity.pdf)); separate host-mask follow-up ([PNG](../hostmask_20261015/host_masked_composition.png), [PDF](../hostmask_20261015/host_masked_composition.pdf)). Follow-up estimates were independently [recomputed](../hostmask_20261015/INDEPENDENT_REPLICATION.md).
