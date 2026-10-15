# Central empirical finding: privacy announcements change behavior independently of information availability

Prepared 15 October 2026 from the completed, separately frozen validation study.
These are AI-assisted research and presentation notes, not the team's final
submission prose. The contribution is the measured result below; the software
and audit trail support that result.

## One finding, with two linked pieces of evidence

**In this controlled live-agent interface, jointly informative metadata supported
secret inference under matched neutral instructions, but the policy announcement
could suppress betting while information remained available or provoke betting
when the view contained no target information. Observed action safety therefore
did not identify whether the information channel was closed.**

This is one empirical claim about the relationship between an observation, the
announced security policy, and the receiver's action. It is not a new theorem
about XOR, a new class of covert channel, or evidence of spontaneous collusion.

### The joint information effect survived held-out controls

Twenty fresh GPT-4.1 mini public worlds each included both protected bits, both
balanced host pads, and two responses to identical neutral prompts. Six neutral
arms varied only the delivered observation or the authorized explicit-bit
positive control. The public task, incentives, decoder and routing tables stayed
fixed. The independent unit was the public world.

| Joint view minus control | Mean signed-decoding effect | Descriptive world-bootstrap 95% | Holm-adjusted p |
|---|---:|---|---:|
| Full fixed view | .087500 | [.056250, .118750] | .000427246 |
| Label only | .093750 | [.068750, .118750] | .000061035 |
| Receipt only | .103125 | [.075000, .131250] | .000091553 |
| Target-independent donor codeword | .068750 | [.031250, .109375] | .003540039 |

All four prespecified comparisons passed the registered joint-specific
replication criterion. Each contrast stayed positive in both ten-world halves,
both stochastic repeats, and all leave-one-world-out estimates. These are
consistency checks, not additional independent replications. Signed decoding S
has maximum .5, with constant guesses and abstention contributing zero; these
effects are not collusion percentages.

### The announcement changed action on the same data

The secondary factorial crossed the actual joint/full observation with the exact
earlier marginal/full policy-announcement bundles. A bundle includes both the
policy name and its mandatory description; the experiment does not identify the
effect of an individual word. Crossed descriptions can be inaccurate by design.

| Actual receiver view | Announced joint decoder / marginal guard | Announced no information / full guard |
|---|---:|---:|
| Joint target information present | 49/80 accepted bets: 38 correct, 11 wrong; net +32 | 0/80 bets; all bit reports null |
| Full target-independent view | 23/80 accepted bets: 10 correct, 13 wrong; net −32 | 0/80 bets; all bit reports null |

The registered secondary announcement effect on accepted betting harm was
**3.15 owner-utility units per response**, descriptive 95% interval
**[2.45, 3.89375]**, Holm6 p=**.000011444**. The actual-view effect was 1.1375
[.56875, 1.6625], Holm6 p=.00466919; their interaction was 2.275
[1.1375, 3.325], Holm6 p=.00466919. All six secondary comparisons across signed
decoding and accepted harm passed their separate Holm family. The comparison of
the two main-effect magnitudes is not an additional registered hypothesis test.

The exact finite request laws establish information availability independently
of model behavior: individual fields were target-independent; their joint view
carried the target bit when source attestations differed; full, single-field and
donor views were target-independent. All 40 actual sources copied correctly.
Thus neither the quiet informative arm nor the betting uninformative arm can be
explained by changing the underlying information availability within that row.

## Why this is a useful empirical extension

Prior information-flow work already recognizes implicit/control channels and
the need to account for what an observer receives. Collusion work already
distinguishes conversation from actions. Our additional measurement separately
varies **actual information** and **the model's security announcement**, while
holding the same task, source snapshots and public inputs fixed. It shows why
zero observed harmful action is insufficient evidence that a channel is closed,
and why harmful action is insufficient evidence of successful private inference.
This is a bounded experimental extension; first-ever publication-level novelty
has not been established by an exhaustive literature search.

The practical relevance is to tool-using agents receiving approval labels,
receipts and privacy notices. Information-flow enforcement controls what is
available to learn; action authorization and instructions affect what happens
next. An evaluation should test those properties separately. The experiment does
not demonstrate this precise weakness in a named production implementation.

## What the error checks actually show

- All **1,320 planned calls** completed, with **zero transport retries** and
  provider-reported cost **US$0.371024**. All **1,280 public-copy tasks** succeeded.
- The explicit positive control recovered **160/160 bits**. It produced only
  **102/160 accepted correct bets**: inference and action are different outcomes.
- Neutral joint receivers made **6 wrong numeric bit reports**, **35 correct
  reports**, and **119 abstentions** in 160 cases. Their signed effect is robust
  under the registered comparisons, but per-response decoding is not reliable.
- Identical joint-input repeats disagreed on bit output in **14/80 pairs** and
  on route in **13/80**. Those disagreements are retained, not averaged away in
  the presentation of reliability.
- Known target-independent neutral controls still produced unsupported numeric
  guesses and bets. The donor control made **28/160 bets**, with net −4;
  neutrality of the target information does not enforce safe action.
- False-one and false-zero rates in the report are **bit-classifier errors**,
  with abstention and invalidity separate. They are not calibrated false-positive
  or false-negative rates of a deliberate-collusion detector. No such detector
  was evaluated here.
- Zero wrong reports in the explicit control still leaves a one-sided 95%
  upper bound of **13.91%** on a fresh independent world containing any wrong
  numeric report, under the stated identical-world-distribution assumption.
  No claim of zero population error is justified.

The neutral joint mean payoff was .225 with descriptive world-bootstrap interval
[.075, .375]. This is an exploratory payoff summary, not a registered profitability
test. The previous cohort's mean-profit interval remains unchanged and includes
zero. Original and validation cohorts are reported separately.

## How the earlier studies fit this single argument

Native Jira work showed why an access flag does not define retained context;
resource work showed why lower harm can reflect contract-penalty prevention.
These are diagnostic lessons motivating the observation and outcome controls.
They are separate empirical results, not replications of one common metadata
mechanism. The earlier four main metadata tests remain unsupported. The host-mask
follow-up and this validation were each designed with earlier outcomes known,
then frozen before their own calls. A logical question–test–finding presentation
must preserve that provenance.

## Scope and evidence

Sources copy a bit neutrally; decoder/routing tables are supplied; the host
intentionally constructs a one-bit channel; utility is a simple public-copy
task; only one model family is used. The findings do not establish autonomous
collusion discovery, general workflow preservation, a break of original defense
implementations, or security against unregistered physical side channels.

- [Prespecified protocol](../research/outputs/stability_20261015/PROTOCOL.md)
- [Complete results and uncertainty](../research/outputs/stability_20261015/RESULTS.md)
- [Frozen analysis output](../research/outputs/stability_20261015/analysis.json)
- [Independent raw-record verification](../research/outputs/stability_20261015/INDEPENDENT_VERIFICATION.md)
- [Input freeze](../research/outputs/stability_20261015/FREEZE.json)
- [Nearest prior-art review](../research/outputs/controlplane_20261015/LITERATURE_POSITIONING.md)

All evidence here is dated 15 October, before the 23–25 October sprint, and must
be disclosed as prior work if used in a sprint submission.
