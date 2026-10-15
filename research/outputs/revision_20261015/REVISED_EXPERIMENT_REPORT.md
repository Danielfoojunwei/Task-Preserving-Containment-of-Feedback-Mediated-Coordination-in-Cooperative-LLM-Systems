# Revised paper experiments: memory visibility and private posting

Status: **COMPLETE**; 160/160 execution branches, 160 passing trace/context/prefix checks.

The revised experiment separates historical private planning messages from permission to post new private messages. Each seed/objective shares one actual eight-turn planning prefix across four randomized execution arms. Original numerical feedback and native reward remain fixed. All previous experiments remain discovery evidence; their original negative hypothesis result is preserved.

The actors use OpenRouter openai/gpt-4.1-mini, temperature 0.7, maximum 1,500 output tokens. The 20 frozen task seeds are 3001–3020. Native distinct feasible tasks, duplicate claims and reward outcomes are reported separately.

| Frozen primary endpoint | Paired seeds | Mean regret contrast | Seed-bootstrap 95% | Exact two-sided p | Holm p (2 tests) |
|---|---:|---:|---|---:|---:|
| R1: Hide old private history; new posts denied | 20 | +8.297 | [+2.810, +14.653] | 0.015625 | 0.03125 |
| R2: Deny new private posts; old history visible | 20 | -0.256 | [-0.768, +0.000] | 1 | 1 |

Positive values favor the stated intervention. R1 = R(H=1,P=0) − R(H=0,P=0); R2 = R(H=1,P=1) − R(H=1,P=0), both under coalition instructions. Each uses exact native optimal reward minus observed reward. Bootstrap intervals are descriptive; primary support requires a positive mean and Holm-adjusted p ≤ .05.

R1 supports the predicted welfare improvement in this synthetic task family.

R2 does not establish the predicted welfare improvement under the frozen testing rule.

## Discovery and measurement corrections

The earlier private-revocation intervention also removed historical planning records because the provider rebuilt agent context each execution turn. Its welfare contrast therefore bundled historical context with future access. The old controller comparison realized identical applied feedback schedules in all 40 matched history-rule/memoryless-rule pairs (80 episodes); differences between those labels cannot identify a value from controller memory.

The old H1 inference diagnostic omitted numeric reward coefficients; 17/20 retained-score answers and 16/20 withheld-score answers equaled the receiver’s own cost. Native default coefficients algebraically recover all 20 audited target costs. This is recoverability evidence, and does not show harmful behavioral coordination or intentional disclosure. The original-versus-suppressed first execution prompts differed in all 40 audited pairs, and first choices differed in 20/40 before feedback existed. Task-seed matching alone therefore did not hold actual planning history fixed.

On 20 disjoint scripted native task seeds (5001–5020), 43,740 native reward evaluations verified that changing only the finite cost of a fixed past irreversible assignment shifts every possible future joint reward by the same constant. All future maximizing sets remained identical. Recovering this selected past cost alone cannot change the conditional welfare-optimal allocation in these one-shot instances. Other hidden future costs, agent incentives, attention and repeated tasks remain outside the certificate. This is native reward enumeration, not LLM behavioral evidence. [Certificate](decision_relevance_certificate.json).

Native tasks_done counted feasible duplicate assignments in 33/320 earlier episodes. Its mean was 3.812 feasible claims; corrected distinct feasible tasks averaged 3.709. New reporting uses distinct completed tasks as the completion metric. The prior discovery family enumerated 31 raw-regret contrasts; its strongest private-revocation candidate did not survive Holm adjustment (p=.0831). Historical signals are not confirmations of revised claims.

In the historical fixed original-feedback coalition condition, distinct feasible tasks increased from 3.50 with private access to 3.90 after revocation; duplicate claims fell from 7/20 to 1/20 episodes. The native duplicate penalty accounts for 6.00 reward units of the 11.37 mean welfare contrast. This descriptive accounting suggests a coordination-error pathway to inspect, while independent planning-prefix variation prevents a causal mediation claim.

## Separate corrected private-cost diagnostic

Completed 80/80 read-only calls on disjoint seeds 4001–4020. The four conditions crossed numerical score present/withheld with exact public reward coefficients given/unsupplied. The receiver was explicitly distinguished from the target agent. All four arms produced 0/20 recoveries and 20/20 abstentions. The single separately registered diagnostic primary contrast, score present minus withheld with coefficients given, was 0.00 (95% seed bootstrap [0, 0]; exact paired two-sided p=1). This diagnostic test is separate from the R1/R2 family.

No behavioral recovery is established by these calls. Native algebraic recovery succeeds in 20/20 cases with the authoritative score identity and coefficients, so abstention does not establish privacy. The prompt names the formula joint_score while the carrier field is joint_reward and does not explicitly equate those names; this limits claims about general arithmetic ability. The degenerate zero bootstrap interval describes this sample and is not a guarantee of zero population disclosure risk. [Diagnostic results and provenance](DIAGNOSTIC_RESULTS.md).

## Exploratory outcomes

All effects below are exploratory. They use paired task seeds and descriptive 95% bootstrap intervals; they do not enter the two-test primary family.

| Contrast | Paired seeds | Regret effect [95%] | Distinct task effect [95%] |
|---|---:|---|---|
| cooperative_R1 | 20 | -2.247 [-6.156, +0.000] | +0.050 [+0.000, +0.150] |
| cooperative_R2 | 20 | +1.974 [+0.000, +5.609] | -0.050 [-0.150, +0.000] |
| R1_objective_interaction | 20 | +10.545 [+4.381, +17.392] | -0.400 [-0.650, -0.150] |
| R2_objective_interaction | 20 | -2.230 [-6.121, +0.000] | +0.050 [+0.000, +0.150] |
| coalition_R1_minus_R2 | 20 | +8.554 [+2.971, +14.944] | -0.350 [-0.600, -0.100] |
| coalition_history_permission_interaction | 20 | -1.014 [-4.426, +2.013] | +0.000 [-0.150, +0.150] |

A positive task-count contrast follows the algebraic contrast shown; it is not necessarily improvement (R1/R2 regret effects and task counts use the same signed coefficients). Coalition-specific claims require separately supported objective interactions. Reward disparity alone does not establish self-benefiting collusion.

Reported execution tokens: 1692567. Planning prefixes incur separate model calls once per seed/objective; cached replay usage is zero. Provider retries, dollar charges and unreported token usage are not inferred.

Integrity checks verify local trace chains, exact prefix contents, task/role fingerprints, actual intervention fidelity and recomputed unique feasible task counts. Local hashes support reproduction, not independent attestation. All per-seed primary effects, exclusion reasons, group means and source hashes appear in revision_results.json; branch-level values appear in episode_results.csv. Failed attempts are preserved by the runner.

## Limits

- One model, one small synthetic task family, one completion per arm; prefix replay pairs planning, not execution sampling noise.
- Sign-flip tests rely on paired exchangeability/symmetric-null assumptions; randomized arm order limits temporal confounding.
- Private-history visibility includes an explicit policy notice; effects may include notice or prompt-content effects.
- Permission denial can consume tool budgets or redirect public messaging; effect alone does not establish a communication mechanism.
- Coalition versus noncoalition reward disparity is not proof of intentional self-benefiting collusion.
- Local ledger hashes are reproducibility checks, not independent provider attestation.
- Exploratory interactions, completion, per-agent rewards and usage require separate confirmation.

Artifacts: [preregistration](PREREGISTRATION.md), [full results](revision_results.json), [discovery analysis](../discovery_20261015/INSIGHT_ANALYSIS.md). Use `python analyze_revision.py --results <execution-results-directory>` to regenerate.

Structural audit artifacts: [ORIGINAL_MECHANISM_AUDIT.json](ORIGINAL_MECHANISM_AUDIT.json), [diagnostic_forensics.json](diagnostic_forensics.json).
