# Five-slide research story — speaker notes

Prepared 15 October 2026. These are AI-assisted presentation working notes for team review, not the team's own submission report. Source IDs resolve in `CLAIM_REGISTER.md`. The five slides separate motivation, experimental changes, empirical identification, results and interpretation; they are not five claims of equal evidentiary strength.

## Slide 1 — From plausible coordination to a testable research question

**Narration**

We began with a practical concern: organizations increasingly delegate work to agents that share tools, state and feedback. An apparently clean final answer does not describe everything a downstream agent observes. A Microsoft-published example makes the information-flow risk concrete: CVE-2025-32711 describes AI command injection in Microsoft 365 Copilot allowing unauthorized information disclosure over a network, with a CVSS 3.1 score of 9.3. This is a disclosed product vulnerability, not evidence of a known victim breach, and not collusion [S1].

The collusion literature gives the second half of the motivation. In Colosseum's Emergent condition, 11 of 19 evaluated models had positive action-based coalition advantage, while two showed a conversation-judge increase of at least one point. These are different thresholds, not a significance count or a judge error rate. The disagreement motivates examining executed outcomes [S2]. Mathew and colleagues demonstrate optimized steganographic communication in laboratory candidate screening; this is an experimental warning, not a deployed hiring incident [S3].

We therefore asked a narrower question: when agents have conflicting objectives, which parts of their observations actually enable harmful coordination, and which restrictions preserve useful work? Colosseum supplied our pinned native Jira runtime. FLOWSEAL motivated enforcement at release boundaries; OCELOT motivated attention to combined and cumulative information. Our orchestration selector was only conceptually inspired by OrchDebate. We did not reproduce or break those original defenses [S4].

Our first feedback hypothesis was unsupported. Inspecting the runtime showed that removing communication access also removed old private messages. That was an identification problem in our experiment, not proof that prior papers missed memory. It changed our objective from accumulating scenarios to isolating the observation, permission and scoring mechanism that could explain each result.

**Reviewer question:** “Are you claiming a real collusion incident or an overlooked first-ever channel?”

**Answer:** No. The product example motivates disclosure risk; the papers motivate controlled multi-agent research. Implicit channels and information-flow composition are established [S5].

**Sources:** S1–S5, S6.

## Slide 2 — Each redesign answers a different question

**Narration**

We organized the changes into four nonoverlapping intervention questions: context, disclosure, execution and measurement. The matrix maps each question to its manipulation and its purpose; it does not imply that the studies used one common endpoint.

First, context: does an effect come from losing old planning or preventing new communication? In the corrected native Jira experiment we crossed visibility of historical private messages with permission to post new ones. The four execution arms reused the same actual eight-turn planning prefix for each seed and objective. That separated runtime interventions previously bundled together [S6].

Second, disclosure: does fixing the artifact also fix what the receiver learns? Our synthetic transfer study held committed artifacts fixed but audited policy labels and numerical receipts. Finite counterexamples showed that later attestations or selector decisions could change feedback despite identical artifacts. The subsequent metadata assay separately tested labels, receipts, rejection statuses and a joint label/receipt construction [S7, S8].

Third, execution: can a public action constraint reduce harm even when communication remains? Procurement, review, resource and artifact tasks received domain-specific action controls alongside disclosure controls. These are mechanism transfers, not full reproductions of the original paper environments. Measuring cooperative utility and coverage prevented us from equating blocked activity with successful containment [S7].

Fourth, measurement: did an unsupported result mean no exploitable information, failed encoding or an unrelated task error? Main-study audits found incorrectly implemented XOR banks and checksum validation that erased otherwise readable bit reports. We retained those original results. A separately frozen follow-up moved masking to the host, used a neutral bit-copying source, supplied decoding tables and simplified the public task to copying. This isolated a capability; it did not demonstrate spontaneous strategy discovery. Crossed replay then changed delivered metadata while keeping the evaluator target fixed [S8, S9].

**Reviewer question:** “Did you simplify the task until you got significance?”

**Answer:** The follow-up was deliberately designed after diagnosed failures, disclosed as a new study, frozen before its calls, and restricted to the narrower claim it can support.

**Sources:** S6–S9.

## Slide 3 — Iteration was disclosed; inference and reproduction were checked separately

**Narration**

This timeline distinguishes exploratory learning from prospective testing: initial native experiments; runtime and metric audits; corrected shared-prefix Jira experiment; synthetic transfer study; metadata main study; source and endpoint audits; separately registered host-masked follow-up. We did not rewrite earlier outcomes after learning from them [S6–S9].

Our identification strategy followed an evidence ladder: available channel, actual encoding, receiver inference, accepted harmful action, coalition payoff and legitimate utility. Information leakage alone is not collusion, a proposed invalid action is not execution, and owner harm alone is not coalition benefit. Agreement and intention remain additional requirements [S10].

Within a metadata world, public inputs stayed fixed across bit/pad twins. The same actual source response was reused across defenses; no successful source was substituted for a failed encoder. In crossed replay we swapped delivered information while retaining the original evaluator bit. This supports causal channel attribution more directly than simple outcome correlation [S8, S9].

The two metadata studies completed 2,326 research calls, with six compatibility requests recorded separately. Actors were GPT-4.1 mini and GPT-4.1, temperature 0.7, with a 1,500-token limit. The larger-model cohorts used different worlds and remain exploratory rather than a causal model ranking. Malformed successful responses were retained, not retried for better results [S8, S9].

The seed or public world, not each correlated bit/pad branch, was the analysis unit. We used exact paired sign-flip reference tests, Holm correction within prespecified multi-test families, and descriptive world/seed bootstrap intervals. These tests retain their exchangeability assumptions. The follow-up's single primary does not create a global error guarantee over the entire iterative program.

Frozen inputs, reconstructed delivered requests and independent offline recomputation passed local audits. These make the result inspectable; they do not provide external execution attestation or remove every modeling assumption [S11].

**Reviewer question:** “Is the study bulletproof?”

**Answer:** No experiment is. Its strength is that changes, failures, test families and limits are traceable rather than hidden.

**Sources:** S6–S11.

## Slide 4 — Three supported effects, retained nulls and one exploratory causal check

**Narration**

The table shows three supported primary effects, each in its own units. They should not be ranked by raw magnitude. Hiding historical Jira messages when new posting was already denied reduced regret by 8.297, with descriptive interval 2.810 to 14.653 and Holm-adjusted p=.03125 across 20 seeds. Denying new posts while retaining history had no supported benefit. The history intervention included a policy notice, so it does not isolate a pure memory mechanism [S6].

Resource enforcement reduced the registered harm endpoint by 580.175, interval 424.110 to 740.635, Holm p=.0078125 across ten held-out seeds. Its decomposition matters: 760 avoided violation penalties minus 179.825 lower raw value from infeasible commitments. Cooperative agents also improved by 220.175. This supports public-contract enforcement, not universal collusion prevention or optimal welfare [S7].

The table keeps the original four metadata tests separate from the new host-masked follow-up; the signed-decoding plot shows only the follow-up. None of the four main tests survived Holm correction. The follow-up's prespecified mini-model contrast was .2265625, interval .1796875 to .2734375, exact p=.000061, across 16 worlds. Signed decoding has maximum .5; this is not a 22.7% collusion rate [S8, S9].

The follow-up's marginal receivers made 31 correct and ten wrong accepted bets, realizing net +22. The mean-payoff interval crosses zero, so reliably positive average profit remains unestablished. Transcript-guard receivers made no bets. All 320 follow-up receivers correctly copied the public schedule and checksum; that is deliberately a simple task [S9].

The second graph is explicitly exploratory: swapping delivered metadata changed payoff from +20 to −50 in 32 matched cases, with correct bets falling 16 to seven. This supports actual use of the delivered channel; it is not an extra confirmatory primary.

**Reviewer question:** “Are positive bootstrap intervals enough to declare the main tests successful?”

**Answer:** No. The registered exact tests with multiplicity correction govern those claims; the nulls remain.

**Sources:** S6–S9.

## Slide 5 — The contribution is causal separation, with clear deployment limits

**Narration**

Four insights connect the studies without conflating their mechanisms. Context: remembered private planning and permission to send future messages are different controls. In a deployed agent, disabling a tool may leave past coordination in the prompt—or unintentionally erase context as well. Operators should inspect the actual reconstructed request, not just the permission flag [S6].

Disclosure: a canonical artifact is only one part of the receiver's view. Individually uninformative metadata can jointly support inference in our controlled assay. The practical implication is to state the authorized receiver view and examine combined fields, including policy decisions and receipts. This is an application of known information-flow principles, not a new cryptographic result or evidence that the original defenses are broken [S5, S8, S9].

Execution: resource authorization, capacity and budget checks prevented explicit contract violations, including under cooperative objectives. That mechanism differs from preventing agreement or favoritism. Conversely, review quorum damaged legitimate utility and coverage. A defender should measure owner outcomes, coalition rewards and cooperative-task costs together rather than celebrate fewer actions [S7].

Measurement: formatting success is not correct encoding, model abstention is not privacy, and malformed task output can suppress otherwise readable inference. In our main study, checksum gating erased 98 numeric predictions, 65 correct. A better benchmark records inference, proposed actions and accepted execution separately [S8, S10].

Our released contribution is a causal audit package combining shared actual sources, balanced counterfactual worlds, crossed replay, finite-view checks, frozen protocols, retained nulls and offline reproduction. The host-mask study demonstrates instructed capability with a neutral source and supplied tables; it does not establish spontaneous collusion, broadly preserved reasoning utility or reliably positive mean profit.

The strongest next experiment is native Colosseum private TEXT, ACTION-only visibility, and the same executed actions hidden or canonicalized. Coalition advantage must survive action-only coordination and weaken when that observation path is cut. That missing comparison anchors the sprint contribution to Track 3.1, with Track 2.3 evidence standards [S12].

**Reviewer question:** “What is uniquely yours?”

**Answer:** These original measurements, counterfactual comparisons and reusable audit artifacts; publication-level first-ever novelty remains unestablished.

**Sources:** S5–S12.
