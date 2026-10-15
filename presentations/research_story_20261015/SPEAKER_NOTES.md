# Five-slide research story — speaker notes

Prepared 15 October 2026. AI-assisted presentation working material for team review. Source IDs resolve in `CLAIM_REGISTER.md`. The five slides form one argument: question → mechanism → controls → results → finding. The current validation was fixed before its own calls, after earlier outcomes were known; it was not an original plan for the entire research program.

## Slide 1 — Can defensive metadata steer an agent?

**Narration**

Our question concerns a practical boundary: a tool-using agent receives more than a final answer. It can also receive labels, receipts and policy messages. Can those observations jointly guide a harmful decision even when each field, inspected separately, reveals nothing about the target?

A deployed-product vulnerability explains why information boundaries deserve attention. Microsoft's CNA record for CVE-2025-32711 describes AI command injection in M365 Copilot allowing unauthorized information disclosure over a network. That establishes a product vulnerability, not a known victim breach or multi-agent collusion [S1].

The academic motivation is behavioral. In Colosseum's benign private-channel probe, 11 of 19 models showed a positive change in action-level coalition advantage, while two crossed the conversation-judge increase threshold. Those are different thresholds, not significance counts or a detector false-negative rate. The finding nevertheless motivates measuring decisions separately from conversation [S2]. Mathew and colleagues also elicited steganographic communication under oversight and paraphrasing in constructed candidate-screening tasks. That is a laboratory result, not a deployed hiring incident [S3].

Our use of Colosseum grounded the work in action-based auditing and a native workplace runtime. The information-flow papers made clear that labels, policy outcomes and observation sequences already have recognized security implications. We do not claim their authors missed implicit flows. Nor did we fully reproduce or break FLOWSEAL, OCELOT, OrchDebate, CaMeL or FIDES [S4, S5].

The open empirical question for this presentation is narrower: what changes because of the actual combined information, and what changes because the agent is told that a guard has or has not protected that information? Distinguishing those explanations matters whenever an apparent reduction in harmful action is used as evidence that a channel has been closed.

**Reviewer question:** “Does a real-world incident demonstrate your exact mechanism?”

**Answer:** No. The CVE motivates information-boundary failures. Our mechanism and its behavioral effects are measured in a controlled synthetic interface.

**Sources:** S1–S5.

## Slide 2 — The combination reveals what either field hides

**Narration**

The mechanism uses a fresh private bit, B. An actual source model copies that bit into an attestation, A. The source sees no host mask and is not asked to collude. We save its returned action before the host applies masking, then reuse that exact action across receiver conditions [S13].

The host releases a label equal to balanced mask R and a receipt equal to A XOR R XOR public polarity P. Each field alone has the same distribution for both target bits after balancing R. Together they recover the attestation. If the source copies correctly, that is also the target bit. All 40 new source calls copied correctly. The algebra is established; the empirical question is what a live receiver does with this view [S5, S13].

The receiver is supplied a decoder and routing table. It reports a bit or abstains, and separately chooses SAFE, LEFT or RIGHT. A correct risky bet earns the coalition two units; a wrong one loses four. Either accepted bet reduces owner utility from ten to three. A receiver can therefore infer correctly but choose SAFE, or infer nothing and still harm the owner by betting. Inference and action are deliberately separate measurements [S13].

The legitimate task is unchanged: copy a supplied public schedule and checksum. This makes task preservation interpretable, but easy. It does not test preservation of complex reasoning. We also limit the information claim to the registered finite receiver view; physical timing, billing and unregistered tools are outside it.

Earlier Jira context/access and resource-penalty experiments helped identify the need to hold actual observations and execution outcomes apart. They concern different mechanisms and are not additional replications of this result. The present story follows one source-to-metadata-to-decision path, rather than combining those unrelated effect sizes [S6, S7].

**Reviewer question:** “Did the agents invent this signaling scheme?”

**Answer:** No. The host implements masking and receivers receive decoding tables. This measures instructed capability and decisions, not autonomous protocol discovery or shared collusive intent.

**Sources:** S5–S7, S13.

## Slide 3 — One mechanism, distinct controls, fixed tests

**Narration**

We completed 1,320 calls: 40 sources and 1,280 receivers. The receiver model was GPT-4.1 mini, temperature .7, with a 1,500-token limit. Twenty fresh worlds each contained both target bits and both host masks. The same neutral request was repeated twice per cell, without replacing unfavorable outputs or selecting successful encoders [S13].

Six observation arms answer distinct questions. Joint metadata supplies the proposed signal. Full fixed metadata removes target information. Label-only and receipt-only test whether either component suffices. A same-format donor codeword contains information about a donor bit fixed independently of the target, testing whether valid-looking metadata alone induces unsupported claims. An authorized explicit bit is the positive reading control [S13].

All six receive the same neutral instructions. Separately, a two-by-two experiment crosses actual joint/full views with the exact earlier marginal/full announcement bundles. These bundles include `assigned_policy` and `mandatory_contract`; they are more than a one-word label. Some crossed announcements are intentionally inaccurate. This experimental manipulation separates information availability from what the agent is told about the guard [S9, S13].

The world is the statistical unit. Four primary joint-minus-negative contrasts require positive means and Holm-adjusted p-values below .05. Six announcement tests form a separate secondary Holm family. Exact sign-flip tests retain a symmetric-null exchangeability assumption; 20,000 world bootstraps give descriptive intervals. Repeats and half-cohort checks describe consistency rather than independent replications.

Raw inference, task validity and accepted execution remain separate. All planned cells completed; independent reconstruction imported no study code and reproduced the primary results from saved provider JSON. Local hashes verify consistency, not external execution attestation. The protocol was frozen before these calls, with earlier results known. Our original four metadata tests remain unsupported, and cohorts are not pooled [S8, S9, S13].

**Reviewer question:** “Are these collusion-detector false-positive and false-negative rates?”

**Answer:** No. False-one/false-zero describe bit inference. Abstention and invalidity are separate; zero observed errors are not zero population risk.

**Sources:** S8, S9, S13.

## Slide 4 — Joint decoding passed all four held-out comparisons

**Narration**

All four prespecified comparisons passed. Joint-minus-full signed decoding was .0875, interval .05625 to .11875, Holm4 p=.000427. Joint-minus-label was .09375, Holm4 p=.000061; joint-minus-receipt was .103125, p=.000092; joint-minus-donor was .06875, p=.00354. Effects stayed positive in both repeats, both half-cohorts and every leave-one-world mean. These are descriptive consistency checks within one 20-world study [S13].

Signed score S is .5 for perfect balanced decoding and zero for constant guesses or universal abstention. The neutral joint arm had S=.090625; full had S=.003125. Joint responses still included 119 abstentions out of 160. The authorized explicit bit was recovered in 160/160 cases, but produced only 102 accepted bets: knowing the target and acting on it were different outcomes [S13].

The announcement graph explains why that distinction matters. With the same joint information, the marginal announcement produced 49/80 accepted bets, while the full announcement produced none. With an actually target-independent full view, the marginal announcement still produced 23/80 bets, with ten correct guesses and thirteen wrong guesses: net payoff −32. The full announcement again produced none. Neither absence of bets nor their presence establishes whether target information is available [S13].

All six secondary tests survived Holm6. The announcement contrast changed mean accepted owner harm by +3.15 per call, interval [2.45,3.89375], adjusted p=.00001144. The actual-view contrast changed harm by +1.1375, adjusted p=.004669. These separate effects are not a registered test that one is statistically larger than the other.

All 1,280 receiver public-copy tasks succeeded. Neutral joint payoff averaged +.225, descriptive interval [.075,.375]; this is not the primary decoding test or a global profitability guarantee. The earlier host-mask effect, .22656, remains a separate cohort, not a pooled estimate [S9, S13].

**Reviewer question:** “Can a closed channel still produce harm?”

**Answer:** Yes. Our declared full views contain no target information, yet some receivers made owner-harming guesses. Those guesses are not evidence of successful target disclosure or deliberate collusion.

**Sources:** S9, S13.

## Slide 5 — Privacy announcements changed action on the same data

**Narration**

The finding has one central implication: action outcomes do not by themselves establish whether an information channel is closed. In this controlled interface, joint metadata supported target-specific inference under matched neutral instructions, while announcements independently changed inference and accepted action. Both facts are necessary to interpret apparent containment [S13].

An informative view looked behaviorally contained under the full announcement: no accepted bets occurred, even though the registered joint signal remained available. Conversely, a target-independent view still generated harmful guesses under the marginal announcement. Its 23 bets harmed the owner despite losing the coalition 32 units overall. We therefore cannot equate harmful action with information leakage or equate observed abstention with confidentiality.

The supported secondary contrast is the exact announcement bundle used here, including its policy identity and mandatory contract. We did not identify a universal effect of the word “secure,” or prove that models believed the announcement. The intentionally inaccurate crossed bundles are an experimental instrument, not a recommended deployed policy [S13].

For tool-using systems, this suggests two operational questions. First, what can the combined authorized observation reveal? Second, which actions may execute even if the agent is uncertain or simply wrong? A confidentiality layer and an action authorization layer address different properties. Existing information-flow research already motivates that distinction; our addition is a live behavioral measurement under component, donor, repeat and announcement controls [S5, S13].

This is bounded evidence. The source was neutral, the decoder supplied, the public task copying, and the model from one family. There is no spontaneous coalition, new XOR theorem, deployed exploit, original-defense break or calibrated collusion detector here. The next transfer should preserve the independent view/announcement manipulation in a native tool workflow. Track 3.1 supplies the carrier question; Track 2.3 supplies the demand for convincing evidence [S12].

**Reviewer question:** “What is new beyond known information-flow principles?”

**Answer:** This specific empirical separation: joint target-bearing metadata and security announcements changed live inference and accepted harm through distinguishable manipulations. Publication-level first-ever novelty remains unestablished.

**Sources:** S5, S12, S13.
