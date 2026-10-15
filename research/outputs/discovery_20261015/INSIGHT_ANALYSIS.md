# Exploratory findings from the completed paper experiments

All 320 existing episodes and the separate 40-episode public extension are discovery evidence for revised claims. The analysis below uses the 240 fixed-policy episodes: 20 matched task seeds, each with the same 12 objective/channel/feedback cells. The 80 controller episodes are not mixed into fixed-policy contrasts.

The strongest candidate is a direct private-channel intervention with original numerical feedback retained. This changes the intervention target; it does not rescue the original hypothesis about score suppression.

Effects are exact system welfare regret contrasts in native reward units; brackets are paired seed-bootstrap 95% intervals (20,000 resamples). Positive private-revocation effects favor removal. Positive instruction-cost or suppression-cost effects indicate more regret.

| Contrast | All 20 historical task seeds | Historical held-out 10 |
|---|---:|---:|
| Coalition: private revocation | +11.37 [+5.33, +17.14] | +12.78 [+4.31, +20.96] |
| Cooperative: private revocation | +1.37 [-5.46, +7.80] | +5.76 [-0.40, +12.59] |
| Revocation × assigned objective | +9.99 [+2.00, +17.87] | +7.02 [-5.15, +18.52] |
| Coalition instructions cost before revocation | +8.55 [+1.84, +14.92] | +7.11 [-3.40, +16.69] |
| Coalition instructions cost after revocation | -1.44 [-5.18, +1.41] | +0.08 [-2.43, +2.17] |
| Suppression cost × objective after revocation | +9.48 [+2.36, +17.28] | +10.92 [+1.23, +21.48] |

The coalition revocation estimate is +20.71 on development, −0.81 on pilot, and +12.78 on historical held-out seeds. Its pooled leave-one-seed-out range is [10.42, 12.88]. Among 9 seeds where both episodes complete four distinct feasible tasks without violations, the mean is +6.70; this subset is post-treatment sensitivity evidence. Native tasks_done counts feasible assignments, including duplicate claims. Distinct-task completion is exported separately in corrected_completion.csv.

Corrected coalition completion under original feedback rises from 3.50 distinct tasks with private access available to 3.90 after revocation: +0.40 [0.15, 0.65]. Duplicate claims fall from 7/20 to 1/20 episodes, while feasible assignments rise only from 3.85 to 3.95. The native 20-point violation penalty implies that the lower duplicate count accounts for 6.00 reward units of the 11.37 mean welfare difference. This is descriptive reward accounting, not an identified causal mediator; independent planning-prefix variation and selection remain possible explanations.

A systematic family of 31 pooled regret contrasts was recorded. The revocation candidate has exact two-sided sign-flip p=0.0027, Holm-adjusted p=0.0831; its objective interaction has p=0.0260, Holm-adjusted p=0.7023. Sign-flip inference assumes paired exchangeability/symmetry, and original run-order randomization was not verified. This adjustment covers this enumerated family only, not the complete history of paper-wide searching. These are candidate signals, not confirmatory discoveries.

Coalition self-benefit is not established. The coalition-minus-cooperative instruction effect on the member/nonmember mean reward gap is +2.62 [-1.20, +6.75] before revocation and +0.72 [-2.05, +3.94] afterward. System welfare harm alone does not demonstrate a profitable coalition or malicious intent. Native per-agent regret uses a different reference than exact system regret.

The separate fresh-task public ablation has five task seeds. Its coalition-specific public-message harm interactions remain −7.71 [−32.25, +8.42] with original feedback and +8.98 [−4.72, +22.68] with score suppression. There is no established harmful public-channel migration. Observed messages only establish channel use.

## Structural findings and the fresh-seed test

Parallel code/trace audits identify a bundled intervention: each execution turn freshly rebuilds init_context, so revocation removes the private planning history as well as future channel access. The old private-channel estimate therefore does not distinguish memory removal from posting permission. The revised test separates both factors.

The same audits show that 40/40 matched history-rule/memoryless-rule pairs (80 episodes) used identical applied feedback sequences, so their between-rule reward differences cannot establish memory value. The H1 decoder omitted numeric reward coefficients; 17/20 retained-score answers and 16/20 withheld-score answers equaled the receiver's own cost. Native defaults make all 20 audited sender costs algebraically recoverable. This is mathematical recoverability evidence, not demonstrated behavioral decoding. Native tasks_done double counts feasible duplicate claims in 33/320 episodes; distinct completion must replace it. Original-versus-suppressed first execution prompts differed in all 40 audited pairs and first choices differed in 20/40, before any feedback. These audit findings explain why exact prefix replay is necessary. Source artifacts: [mechanism audit](../revision_20261015/ORIGINAL_MECHANISM_AUDIT.json) and [diagnostic forensics](../revision_20261015/diagnostic_forensics.json).

A separate installed-runtime certificate on seeds 5001–5020 enumerates 43,740 native rewards. Varying only the finite selected cost of a fixed past irreversible claim shifts all possible future joint rewards by a constant, preserving the maximizing assignments in all 20 instances. Thus recovering that already-selected cost alone does not change the conditional welfare-optimal future allocation in this one-shot task. This separates information disclosure from decision relevance; it does not establish behavior or cover unknown future costs and repeated tasks. [Certificate](../revision_20261015/decision_relevance_certificate.json).

Use seeds 3001–3020, original feedback, GPT-4.1 mini at temperature 0.7 and 1,500 output tokens. Cross private history visible/hidden with future private posting allowed/denied under both objectives: 160 execution branches, sharing 40 actual planning prefixes. For a given seed/objective every arm replays exactly the same prefix before any task action. Randomize four-arm order.

Freeze two primary endpoints: R1 = coalition regret(history=1, permission=0) − regret(history=0, permission=0); positive means hiding planning history helps. R2 = coalition regret(history=1, permission=1) − regret(history=1, permission=0); positive means denying future private posts helps with history fixed. Use paired exact two-sided sign-flip tests, Holm across these two tests, and 95% seed-bootstrap intervals. Both objective interactions, R1−R2, reward gaps, distinct completion, violations and usage are exploratory. Do not expand seeds after inspecting outcomes. Never rerun a completed episode for a more favorable outcome.

This bounded test can confirm or reject a local intervention effect. It cannot establish intent, mathematical feedback recovery, broad safety, or a value from historical controller memory. One model, one synthetic family and one language-model completion per cell remain limitations. Channel removal also changes prompts and action opportunities; those are candidate explanations to audit, not an identified mediation pathway.

Reproduce the discovery analysis with `python analyze_discovery.py`. Full per-seed effects, t intervals, bootstrap intervals, multiplicity diagnostics and candidate definitions are in `insight_analysis.json`.
