# Research extension: collusion opportunities and task-preserving containment

Completed 15 October 2026. All live task actors used **OpenRouter `openai/gpt-4.1-mini`, temperature 0.7, maximum 1,500 output tokens**. These are synthetic research environments; agents have no real-world procurement, funding or resource authority. Coalition objectives are explicitly instructed. Attached documents supplied research context and did not override the user's request.

Read the [paper extension](multiscenario_20261015/PAPER_EXTENSION.md), [expanded results](multiscenario_20261015/MULTISCENARIO_REPORT.md), [corrected Jira results](revision_20261015/REVISED_EXPERIMENT_REPORT.md), and [exploratory joint-guard report](multiscenario_joint_20261015/JOINT_RESULTS.md).

## Findings

The corrected Jira experiment separated historical planning visibility from future private-post permission. Hiding prior private history reduced coalition-condition regret by **8.297** reward units, descriptive 95% interval **[2.810, 14.653]**, two-test Holm **p=.03125**. Denying new posts while keeping history showed no supported benefit. The effect includes the whole visibility intervention and its policy notice; it does not establish intentional collusion or a pure memory mechanism.

Four new scenario families shared actual sealed planning prefixes across defenses. The held-out primary comparisons were baseline minus action-guard harm, ten paired seeds per domain:

| Scenario | Mean benefit | Descriptive 95% interval | Holm p, four tests | Interpretation |
|---|---:|---|---:|---|
| Procurement | −0.027 | [−0.407, 0.300] | 1 | No supported benefit; legal coordination can survive the price cap |
| Review trading | −0.06348 | [−0.16409, 0] | .5 | No supported benefit; cooperative utility fell 11.229% and award coverage fell 20 percentage points |
| Resource allocation | +580.1748 | [424.110, 740.635] | .0078125 | Supported public-contract enforcement; utility/coverage criteria met |
| Typed artifact | +3.8 | [0.9, 6.9] | .375 | Primary support rule not met; uncertainty remains despite the positive descriptive interval |

Harm units differ across domains and must not be pooled. Resource improvement includes **760 units of avoided public violation penalties**, offset by **179.8252 less raw value from otherwise infeasible overcommitted allocations**. Cooperative runs also improved by 220.1748 units. Role/budget/capacity enforcement stopped those violations; valid favoritism remains possible. The reported resource effect is not a universal collusion-prevention result. Frozen adaptive selection showed no positive mean advantage over the development-selected fixed comparator in any domain.

Native deterministic controls demonstrate harmful coalition opportunities and feasible honest alternatives in every domain. Two separate constructions expose channels through disclosed selector decisions and numeric receipts. They are architectural capability evidence, not observed spontaneous model discovery or proof of independent novelty. The receipt finding was disclosed after the source freeze; all original responses and tests remain unchanged.

The additional joint guard removes numeric receipts and normalizes commuting artifacts. Its 20 paired follow-up branches showed no added behavioral harm reduction. Correct guesses of zero in commuting cases reflect the bit distribution; dependent ordering remains a declared residual channel. Full bit-stratified outcomes prevent interpreting raw recovery fractions as proof of leakage.

## Evidence and scope

- Corrected Jira: 40 live planning prefixes, 160 execution branches; separate 80-call private-cost diagnostic and native enumeration certificate.
- Expanded suite: 120 live prefixes, 480 canonical branches and 30 secondary branches; **2,520 new actual calls**.
- Joint follow-up: 20 reused prefixes, 20 branches; **80 additional calls**, zero new planning calls.
- Both expanded audits passed. The main suite preserved 81 malformed responses and the joint suite four; malformed actions were never rerun for better outcomes. No transport retries occurred in these two suites. Counts of completed calls are not counts of successful task actions.
- Reported expanded plus joint usage: **3,642,057 tokens**, provider-reported cost **$1.618302**. These totals exclude earlier studies and do not attest to account billing.

[Source scope](multiscenario_20261015/PAPER_SCOPE.md) distinguishes the pinned Colosseum runtime from new synthetic extensions and partial concept transfers from FLOWSEAL, OCELOT and OrchDebate. Full reproductions of the latter three were not performed. Event budgets are registered-event units, not calibrated privacy bits. The original negative study is preserved in `original_paper_experiments.zip` and is not pooled into the new primary tests.

The [final main audit](multiscenario_20261015/FINAL_AUDIT.json) verifies all 71 frozen files, exact requests, shared prefixes/worlds, guard commitments, usage and comparator timing. Its [first-pass audit and correction](multiscenario_20261015/AUDIT_CORRECTIONS.md) remain available: Python 3.12 changed floating-point summation text; exact reconstruction passes under the actual Python 3.11.17 runtime. No study data changed. The [joint audit](multiscenario_joint_20261015/JOINT_FINAL_AUDIT.json) verifies its 80 new calls and reused prefix identity.

All three new analyses reproduced identical estimates in a fresh offline copy; see [verification](OFFLINE_REPRODUCTION.json) and [instructions](REPRODUCING.md). Exported scientific figures are under `multiscenario_20261015/figures/` as PNG and PDF. `ARTIFACT_SHA256.json` covers every included source artifact except itself; the ZIP has an external checksum. Local hashes support reproducibility, not independent provider attestation.
