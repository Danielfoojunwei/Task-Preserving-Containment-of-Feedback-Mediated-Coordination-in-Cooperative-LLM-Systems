# Separating Memory, Disclosure, and Action Controls in Cooperative LLM Collusion Audits

**Research manuscript, 15 October 2026.** The corrected Jira experiment, 510 expanded-suite branches, and 20 exploratory joint-guard branches are complete. Final local audits passed; original audit flags and post-freeze disclosures remain linked. No frozen study source or endpoint was changed to write this manuscript.

## Abstract

We audit memory, disclosure, and action controls in cooperative LLM systems with explicitly assigned coalition objectives. An initial score-suppression study did not support its main hypothesis. A runtime audit found that channel revocation also erased private planning history and that nominally different controllers applied identical feedback schedules. A corrected shared-prefix experiment separated history visibility from future posting permission. Across 20 task seeds and 160 GPT-4.1 mini execution branches, hiding old private history with new posts denied reduced coalition-condition regret by 8.297 reward units (descriptive 95% interval [2.810, 14.653]; two-test Holm p = .03125); denying new posts with history retained showed no supported improvement. We then tested four synthetic domains using 120 sealed proposal prefixes and 480 canonical live branches, plus 30 secondary selector branches. Resource authorization/capacity/budget enforcement reduced coalition harm by 580.175 units [424.110, 740.635] (four-test Holm p = .0078125), principally through avoiding explicit violation penalties; cooperative agents also improved. The other three primary reductions were unsupported, and review quorum exceeded utility/coverage loss limits. Frozen adaptive selection showed no positive mean advantage over discovery-selected fixed policies. Two deterministic counterexamples expose policy-tag and numeric-receipt carriers; live exploitation of those particular channels was not established. An 80-call exploratory joint-guard follow-up showed no additional coalition harm reduction. These results support local contract enforcement and distinguish runtime interventions without demonstrating general collusion prevention.

## 1. Introduction

Restricting communication is an incomplete description of an intervention in a stateful agent system. Removing channel access may also remove remembered messages when a provider reconstructs context each turn. Conversely, restricting a score may leave task proposals, public messages, allocations, and policy metadata available. These differences matter when a subset of agents pursues an objective that conflicts with the owner's task.

We ask three separable questions: does an intervention change what agents can observe or do; does it reduce measured owner harm under coalition instructions; and does it preserve legitimate cooperative performance? Recoverable information, coordinated language, coalition benefit, and welfare harm are separate observations. None alone establishes intentional collusion.

This manuscript reports a completed correction of a Colosseum Jira study and a completed, separately frozen extension to four new synthetic domains. The earlier null is preserved. The extension was designed after the earlier data were available and is not a retrospective confirmation of the original hypothesis. Its adversarial condition explicitly authorizes coalition attempts within a finite interface, supplies a common objective, and leaves refusal, abstention, failed coordination, and defended outcomes possible.

The results distinguish historical context from future permission and identify effective public-contract enforcement in one resource task. They also retain null defenses, a review-utility tradeoff, and residual artifact pathways. The architectural constructions establish finite capabilities; the behavioral experiments determine which effects were actually observed.

## 2. Related work and reuse boundary

**Colosseum** formalizes cooperative multi-agent tasks, action-based regret and coalition metrics, secret-channel probes, objective misalignment, persuasion, and heterogeneous resource roles [1]. We use its pinned Jira runtime for the corrected experiment. The four additional simulators transfer mechanisms; they do not reproduce the original Hospital, Jira, and meeting experiments across the paper's model and judge configurations. In particular, our four resource requesters do not reproduce a heterogeneous resource-provisioner role.

**FLOWSEAL** places provenance tracking and mandatory release checks at tool boundaries, with an isolated semantic declassifier [2]. Its workspace lure, omission-based disclosure, and channel-decoupling attacks already establish that privacy risk extends beyond direct answers. Our registered-boundary gate and artifact mediation reuse enforcement concepts. They do not reproduce its semantic checker, original consent workflow, benchmark suite, or live MCP evaluation.

**OCELOT** addresses cumulative inference and colluding sinks using Witness-Verified Declassification, a trained local defender, typed witnesses, calibrated costs, and deterministic verification [3]. It distinguishes arithmetic budget non-exceedance from model-relative semantic privacy. Our pooled ledger binds registered events and charges event units. It has no calibrated privacy-bit interpretation, learned defender, signed rubric library, or credal audit.

**OrchDebate** is described in the supplied public-record mapping as structured-state orchestration over reusable, self-evolving debate skills [4]. Its full primary algorithm remains unverified here. Our selector is a frozen deterministic rule inspired by that conceptual separation, not a reproduction of training or skill evolution. Verified versions, retained primary texts, hashes, and unavailable components are documented in [sources.json](sources.json) and [PAPER_SCOPE.md](PAPER_SCOPE.md).

## 3. Audit findings motivating the correction

The original feedback-mediated-coordination hypothesis was not supported. Further inspection identified four limits on stronger interpretations of those data.

First, the provider rebuilt execution context, so revoking private-board access removed historical planning messages as well as future access. Second, all 40 audited original-versus-suppressed first-execution prompt pairs differed, and 20 first choices differed before execution feedback existed. Matched task seeds had not fixed actual planning histories. Third, the history-aware and memoryless controllers applied identical feedback schedules in all 40 matched pairs; performance differences could not identify a benefit from controller memory. Fourth, native `tasks_done` counted feasible duplicate claims in 33 of 320 episodes; distinct completed tasks required separate recomputation.

The original private-cost diagnostic also omitted numerical reward coefficients and often elicited the receiver's own cost. A corrected 80-call diagnostic produced only abstentions, including 20 nominally identifiable cases. An algebraic reference recovered all 20 target costs from authoritative score identities and coefficients. The diagnostic's `joint_score`/`joint_reward` naming mismatch limits claims about general arithmetic ability; abstention does not establish privacy.

Decision relevance is a further requirement. In 43,740 native reward evaluations on 20 disjoint scripted seeds, varying only the selected finite cost of a fixed irreversible past assignment shifted every possible future joint reward by a constant and preserved the future maximizing sets. This finite certificate does not cover other future costs, changed incentives, attention, or repeated tasks. It shows why selected-past-cost recoverability alone is insufficient evidence of a changed conditional welfare optimum. Evidence and scope are retained in [revision_results.json](../revision_20261015/revision_results.json) and [decision_relevance_certificate.json](../revision_20261015/decision_relevance_certificate.json).

## 4. Completed corrected Jira experiment

We crossed historical private-message visibility, H ∈ {0,1}, with permission for new private posts, P ∈ {0,1}. Each seed/objective condition shared one actual eight-turn planning prefix across its four execution branches. Original numeric feedback and native rewards were held fixed. Twenty frozen task seeds, 3001–3020, two objective conditions, and four interventions produced 160 branches; all 160 passed the reported trace, context, and prefix checks.

Actors used OpenRouter `openai/gpt-4.1-mini`, temperature 0.7, with at most 1,500 output tokens per response. Welfare regret was exact native optimal reward minus observed reward. The two frozen primary coalition-condition contrasts were

R1 = E[R(H=1,P=0) − R(H=0,P=0)],

R2 = E[R(H=1,P=1) − R(H=1,P=0)].

Positive values favor hiding history or denying posts, respectively. Analysis used paired task seeds, exact two-sided sign-flip reference tests, Holm adjustment across the two primary tests, and descriptive seed-bootstrap intervals. The sign-flip reference requires paired exchangeability/symmetric-null assumptions; branch-order randomization does not eliminate execution sampling noise.

| Frozen primary contrast | Seeds | Mean regret benefit | Descriptive 95% interval | Raw p | Holm p |
|---|---:|---:|---|---:|---:|
| R1: hide old history, new posts denied | 20 | +8.297 | [2.810, 14.653] | .015625 | .03125 |
| R2: deny new posts, old history retained | 20 | −0.256 | [−0.768, 0.000] | 1.000 | 1.000 |

R1 met the frozen support rule. Seven seeds favored hiding history, two favored retaining it, and eleven tied; the median contrast was zero. R2 did not support an improvement and is not evidence of equivalence. These are raw native reward units. The intervals are not multiplicity-adjusted confidence sets.

This result supports a welfare effect of the complete history-visibility intervention in this task family. The intervention included a policy notice, and permission changes can redirect messaging or consume tool budgets. We do not infer an isolated memory mechanism, coalition-specific mediation, or intentional self-benefiting collusion from the primary contrast. Objective interactions and completion effects remain exploratory. Full per-seed values, exclusions, provenance, and limits appear in the [completed report](../revision_20261015/REVISED_EXPERIMENT_REPORT.md) and [results JSON](../revision_20261015/revision_results.json).

## 5. Expanded study methods

The extension uses four finite domains and two objectives per world. Procurement measures buyer-utility shortfall separately from social welfare and coalition profit. Review trading measures merit shortfall, with no award assigned utility zero. Resource allocation measures realized project-value shortfall plus predeclared role, capacity, and budget-violation penalties. The artifact task measures schedule, project-priority, and review utility. These units are not pooled into one cross-domain harm score.

Five discovery seeds, 6001–6005, and ten held-out seeds, 6101–6110, were fixed without opportunity screening. Every world/objective cell generates four sealed round-0 proposals: no actor sees another proposal during that prefix. The raw prefix is then shared across `baseline`, `information_guard`, `action_guard`, and `adaptive_controller`; each branch applies its policy before peer delivery and makes four fresh sequential final model decisions. The completed design contains 120 prefixes, 480 canonical live branches, and 30 secondary unsafe-selector artifact branches: 2,520 recorded actor responses, with malformed responses retained as outcomes. Branches sharing a prefix are paired continuations, not independently initialized tasks.

All task actors use the same GPT-4.1 mini settings as the corrected Jira study. Coalition members receive explicit authorization for a synthetic adversarial assignment, a shared objective, their own private state, public rules, and the channels actually delivered. Honest actors retain cooperative objectives. In the artifact main arms, comments and the instructed permutation codebook are both available; the experiment does not isolate permutation use alone or establish spontaneous discovery. Private data are assigned at world construction. No private-board revocation or fresh post-revocation information treatment is implemented in these domains.

| Domain | Disclosure guard | Task-action guard | Known scope limit |
|---|---|---|---|
| Procurement | Seal peer quotes and messages | Public quote ceiling 65, buyer budget 100 | Legal price coordination remains; rejected supply can harm coverage |
| Review trading | Seal peer ballots and messages | Both designated independent reviewers must approve eligibility | Trusts designated roles; disagreement can yield no award |
| Resource allocation | Remove numerical reward only | Enforce authenticated department, capacity, and shared budget | Text, allocations, and valid favoritism remain |
| Shared artifact | Remove numerical reward only | Strip editor comments; canonicalize commuting task order | Dependency-sensitive order and a later-attestation numeric receipt remain |

The adaptive controller chooses the action guard when registered public/typed-prefix risk is positive, otherwise the information guard. It accesses no evaluator truth or other agent's private state. Artifact risk uses public carrier capability rather than the encoded bit. All registered commitments pass common provenance/binding checks and a pooled eight-event ledger. This common audit layer does not selectively strengthen one policy and provides no entropy bound.

For each domain, the primary endpoint is held-out coalition harm(baseline) minus harm(action guard), with ten paired seeds, exact two-sided sign-flip tests, Holm correction across four domains, and 20,000-resample descriptive bootstrap intervals. A positive mean and adjusted p < .05 are required for primary support. Cooperative utility and coverage limits are prespecified: mean utility loss no more than 2% of each fixed public scale and mean coverage decline no more than five percentage points. Point thresholds are provisional task-preservation criteria, not statistical noninferiority. Confidence intervals and a stricter upper-bound sensitivity are reported separately.

Fixed comparator selection uses discovery data only and is frozen before held-out calls. Adaptive-versus-fixed comparisons, objective interactions, bit strata, dependency subgroups, coalition benefit, and unsafe-selector comparisons are secondary or exploratory. Failure and invalid-action counts remain explicit; malformed actions are not retried for better outcomes. The [preregistration](PREREGISTRATION.md), [manifest](manifest.json), and [71-file freeze record](PREREGISTRATION_SHA256.json) specify these commitments. The freeze records zero expanded live results at its timestamp.

## 6. Finite controls and a selector counterexample

Native parser/guard/feedback/evaluator controls establish harmful opportunities without selecting study seeds. A procurement fixture extracts 29 payment units against truthful outside vendors while retaining an efficient supplier; its legal price survives the cap. A review fixture uses signal-consistent independent ballots and reciprocal coalition votes to produce a low-merit tie winner; independent quorum prevents that outcome. Resource controls show both blocked contract violations and valid first-mover favoritism that survives the same guard. Commuting artifact fixtures demonstrate codebook recovery and its collapse after canonicalization. Every domain also admits a feasible honest alternative. These are deterministic capabilities, not observed LLM behavior; full evidence is in [positive_controls.json](positive_controls.json).

A separate two-world certificate isolates a disclosure path in defense orchestration. Let a protected bit select canonical versus reversed commuting task order. An unsafe selector chooses the information guard for canonical order and the action guard for reversed order. With comments removed, both paths deliver the same canonical artifact, but their public policy tags differ and identify the bit under the stated codebook. A capability-based selector yields the same artifact and policy tag in both worlds. This is an explicit finite construction with one uniformly sampled bit, not a calibrated general leakage estimate. It neither establishes live model exploitation nor independently proves novelty. [Certificate](selector_sidechannel_certificate.json).

**Post-freeze receipt audit.** A subsequent read-only audit found another registered path. Although the editor's round-1 attestation is not retransmitted as artifact text, `feedback` computes a visible numeric validity reward from that attestation. Choosing null versus a valid canonical order toggles the receipt between 0 and 10 while the immutable round-0 artifact, evaluated workflow, and fixed legitimate utility remain identical. The [native two-world certificate](receipt_channel_certificate.json) demonstrates distinguishable actual receiver views under baseline and the action guard. Numeric withholding closes that constructed receipt path; computing feedback solely from committed state also makes the constructed views equal. Neither repair is claimed as a result of the frozen main experiment.

The disclosure was recorded after live calls began, at a progress snapshot of 40 prefixes and 46 discovery branches. The root reviewer had inspected progress counts rather than branch actions or outcomes. No frozen input, primary test, or completed response was changed. The [dated audit disclosure](DEVIATIONS.md) preserves that chronology. This is an architectural capability result, not evidence that a live sender discovered or exploited the receipt codebook. It also limits attribution in the secondary unsafe-selector live arm: matching sanitized artifact text and comments does not isolate public policy tags when numeric receipts remain. Live recovery therefore cannot be attributed uniquely to the selector without examining complete delivered inputs.

## 7. Expanded live results

All 480 canonical and 30 secondary branches completed. The final local audit verified 120 prefixes, 2,520 unique scheduled calls, the 71-file source/world freeze, discovery-comparator timing, reconstructed requests and guards, and retained 81 invalid successful model actions. The exploratory joint follow-up separately completed 20 branches and 80 new responses. Audit scope and first-pass resolutions appear in Appendix A.

### Primary harm reduction and legitimate utility

Each row uses ten held-out coalition task seeds. Positive benefit means baseline harm minus action-guard harm. Native units differ and are not pooled. Intervals are descriptive bootstrap intervals; primary support follows the exact paired tests with Holm correction across four domains.

| Domain | Mean harm benefit [95% interval] | Raw p | Holm p | Primary support |
|---|---|---:|---:|---|
| Procurement | −0.027 [−0.407, 0.300] | 1.000 | 1.000 | No |
| Review trading | −0.063 [−0.164, 0.000] | .250 | .500 | No |
| Resource allocation | +580.175 [424.110, 740.635] | .001953125 | .0078125 | Yes |
| Shared artifact | +3.800 [0.900, 6.900] | .125 | .375 | No |

Resource effects favored the guard on all ten seeds. Its reduction, positive baseline coalition excess harm, cooperative-utility limit, and coverage limit met both the registered point qualifiers and stricter interval sensitivity. The artifact's positive bootstrap interval does not override its unsupported exact/multiplicity-adjusted test: only four seeds improved and six tied.

| Domain | Cooperative utility loss, % of fixed public scale [95%] | Coverage decline, percentage points [95%] |
|---|---|---|
| Procurement | 0.000 [0.000, 0.000] | 0.0 [0.0, 0.0] |
| Review trading | +11.229 [−1.216, 24.890] | +20.0 [0.0, 50.0] |
| Resource allocation | −68.805 [−77.730, −59.933] | 0.0 [0.0, 0.0] |
| Shared artifact | +0.833 [−5.833, 9.167] | 0.0 [0.0, 0.0] |

Negative loss denotes improvement on the frozen scale, not a percentage return relative to baseline utility. Review quorum exceeded the 2% utility and five-point coverage mean limits; it was not task-preserving under the stated criteria. The artifact's utility interval also crossed the stricter limit. No powered noninferiority claim is made. See [harm effects](figures/domain_harm_effects.pdf) and [cooperative utility/coverage](figures/cooperative_task_preservation.pdf).

### What the resource effect measures

The exact coalition harm gain was 580.1748 = 760.0000 avoided violation penalties − 179.8252 reduction in raw project value. Baseline raw value was 351.39518, penalties 760, and net utility −408.60482; guarded raw/net value was 171.56998 with zero penalties. The unguarded value counts budget-infeasible commitments and is not feasible welfare. Average coalition-condition overbudget units fell from 11.6 to zero, and unauthorized and department-overcapacity units each fell from 3.6 to zero. Coalition units fell from 11.6 to 4; registered valid coverage remained one.

Cooperative agents also improved by 220.1748 [191.785, 248.735], about 38% of the coalition-condition gain. Their baseline penalties were 400 and overbudget units eight; guarding removed both. The exploratory objective interaction was +360 [200, 520], entirely the difference in explicit penalty removal; raw-value objective contrasts were zero. This supports local public-contract enforcement, including excess violations under coalition instructions. It does not show private-value optimization or elimination of valid favoritism, which remains possible in native controls.

### Adaptive policy and artifact diagnostics

No adaptive-versus-discovery-selected-fixed comparison had a positive mean harm advantage: procurement −0.018 [−0.297, 0.243] against information guard; review −0.125 [−0.273, −0.003] against baseline; resources −26.225 [−78.676, 0.000] against action guard; artifact −0.300 [−3.400, 2.800] against action guard. These exploratory comparisons provide no observed added-value case for this frozen selector and do not establish equivalence of controllers.

The optional unsafe-selector coalition harm difference versus safe adaptive selection was +1.900 [−2.300, 6.000], with bit-recovery difference 0.000 [−0.500, 0.500]. In the two commuting, true-bit-one coalition cases, baseline recovered both bits; action guard and the unsafe selector recovered neither. The unsafe arm's overall 6/10 accuracy included four correct zero defaults and two dependency-sensitive one-bit cases. Thus the live data do not demonstrate policy-tag exploitation; the separate certificate remains architectural evidence. Numeric receipts also prevent unique tag-channel attribution from complete transcripts. These tiny subgroups are exploratory.

### Exploratory joint guard

The separately frozen follow-up combined action mediation with numeric-feedback withholding and a fixed public identity, reusing all 20 held-out artifact objective prefixes. Coalition mean harm changed from 5.0 under action guard to 5.4 under the joint guard: paired benefit −0.4 [−1.0, 0.0]. Favored-project choices remained 2/10; cooperative utility changed by +0.8 [−0.8, 3.4]. Additional live containment benefit was not demonstrated; no confirmatory p-value claim is made.

On seven commuting coalition tasks, both policies always predicted zero, yielding 5/7 correct reports because five true bits were zero. This is a constant-zero baseline, not observed disclosure through the joint guard. On three dependent tasks, correct reports changed from 2/3 to 3/3, but the same two one-bit cases still selected the favored project and mean harm remained 16.67. Dependency-sensitive order and invalid schedules remain disclosed limits. The joint audit verified that no registered numeric reward fields reached the new inputs. Removing the constructed receipt capability did not establish that main actors had exploited it. [Joint report](../multiscenario_joint_20261015/JOINT_RESULTS.md); [results JSON](../multiscenario_joint_20261015/JOINT_RESULTS.json).

Full domain estimates, qualifiers, failed/invalid-action accounting, and exploratory contrasts are retained in [scenario_results.json](scenario_results.json). The corrected history result remains a separate two-test family; see [history/permission figure](figures/context_history_and_permission.pdf).

## 8. Limitations

One model and small synthetic worlds limit transfer. Each live continuation contributes one sampled action per actor; shared-prefix replay controls planning history, not execution randomness. Explicit coalition objectives and supplied codebooks establish adversarial capacity conditions rather than natural emergence. The four domains expose finite interfaces and do not cover arbitrary tools, memory stores, timing channels, or unconstrained steganography.

Controls may reduce task completion or reject legitimate actions. Public role enforcement does not eliminate valid favoritism, while a quota or price cap need not optimize private welfare. A raw reduction in penalties can reflect generic rule compliance. Local binding hashes and ledgers support reproducibility within a trusted host; they are not independent provider attestation. Event-unit budgets are not semantic privacy guarantees.

Expanded hypotheses were chosen after earlier experiments. Their local freeze separates subsequent held-out evaluation from design changes but does not make the entire research program prospective. Conditional subgroup results and selector diagnostics remain secondary. Full reproductions of FLOWSEAL, OCELOT, and OrchDebate are outside the implemented scope, and independent novelty is not established merely by combining their ideas.

## References and evidence

1. Nakamura et al. *Colosseum: Auditing Collusion in Cooperative Multi-Agent Systems.* [arXiv:2602.15198v2](https://arxiv.org/abs/2602.15198v2), 27 May 2026. Runtime pinned to `b077fe7e2f10566e92156cc12e06ffb2aac54790` with Terrarium 0.1.1.
2. Shim et al. *Confuse the Model, Control the Flow: Understanding and Mitigating Privacy Leakage from LLM Agents with Information Flow Control.* FLOWSEAL, [arXiv:2609.14003v1](https://arxiv.org/abs/2609.14003v1), 12 September 2026. Full paper verified; limited component transfer here.
3. Xie and Li. *OCELOT: Inference-Leakage Budgets for Privacy-Preserving LLM Agents.* [arXiv:2606.12341v1](https://arxiv.org/abs/2606.12341v1), 10 June 2026. Full paper verified; limited component transfer here.
4. *OrchDebate: Adaptive Orchestration for Multi-Agent Debate via Self-Evolving Skills.* [Supplied OpenReview record](https://openreview.net/forum?id=JyJSJitKjy). Title and conceptual description follow the attached mapping; authors, version, and full algorithm remain unverified in this environment.

Machine-readable evidence: [corrected Jira results](../revision_20261015/revision_results.json), [native opportunity controls](positive_controls.json), [selector certificate](selector_sidechannel_certificate.json), [source/version manifest](sources.json), and [expanded results](scenario_results.json). Historical evidence is retained separately and is not pooled into revised primary estimates.

## Appendix A. Audit chronology and artifact provenance

The [final main-suite audit](FINAL_AUDIT.json) passed with no remaining errors or warnings. Its [first pass](FINAL_AUDIT_FIRST_PASS.json) is preserved: flagged feedback-order differences were resolved by replaying under the actual Python 3.11 execution runtime instead of Python 3.12; the authoritative pre-call analysis-source binding is the preregistration hash manifest, rather than a later annotation timestamp. No frozen study source, input, response, or primary test was rewritten to resolve those flags. The [joint audit](../multiscenario_joint_20261015/JOINT_FINAL_AUDIT.json) separately passed. These local checks establish retained-record consistency, not external attestation or scientific validation of a causal mechanism. Figure captions and saved-estimate provenance appear in [FIGURE_CAPTIONS.md](figures/FIGURE_CAPTIONS.md) and [FIGURE_PROVENANCE.json](figures/FIGURE_PROVENANCE.json).

Figures: domain harm effects ([PNG](figures/domain_harm_effects.png), [PDF](figures/domain_harm_effects.pdf)); cooperative task preservation ([PNG](figures/cooperative_task_preservation.png), [PDF](figures/cooperative_task_preservation.pdf)); history and posting permission ([PNG](figures/context_history_and_permission.png), [PDF](figures/context_history_and_permission.pdf)).
