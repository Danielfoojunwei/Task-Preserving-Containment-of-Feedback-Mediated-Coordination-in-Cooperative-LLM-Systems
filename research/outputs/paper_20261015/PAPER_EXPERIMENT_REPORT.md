# Paper experiment results — 15 October 2026

Completed main episodes: **320/320** (60 development, 60 pilot including peer ablation, 200 held-out).
Fresh-task extension: **40/40**. Read-only diagnostic calls: **40/40 maximum**.

All actors: OpenRouter openai/gpt-4.1-mini, temperature 0.7, maximum 1,500 tokens per response. Diagnostic receivers use temperature 0 and 512 output tokens. Rule controllers make no extra model calls.

Original source and native reward functions are pinned. Development selection precedes held-out execution. Earlier seed-105 results are retained and disclosed; the exploratory extensions were specified after those pilot outcomes were visible.

## Interpretation

- The primary positive-interaction hypothesis H2 is **not supported**: the held-out estimate and bootstrap interval are in the opposite direction. Numerical feedback cannot be described as causing coalition harm on the strength of these results.
- H1 shows **no incremental recovery benefit** from the numerical score in this recorded-prompt diagnostic. This does not disprove mathematical recoverability under other information assumptions.
- H3 cooperative utility lies within the proposed bounds in this exploratory bootstrap: normalized mean welfare loss is about 0.35%, with no mean task-completion decline. This is not a powered confirmatory noninferiority result.
- H4 shows **no clear advantage of the history rule** over the development-frozen fixed comparator. The history-versus-memoryless contrast is also reported; persistent guard states limit how strongly this setup isolates the value of memory.
- H5 coalition-specific public-channel harm is **not established** in the fresh-task extension: both feedback-condition interaction intervals include zero. Observed public posts alone are not proof of harmful migration.

## Findings

- Held-out H2 assigned-objective interaction: **-10.916549188427519** (95% seed bootstrap interval [-21.578862889968722, -1.37360170872345]; 10 complete task blocks). Positive values favor the specified differential feedback hypothesis; the estimate alone is not evidence of intent or a decoded secret.
- H3 cooperative normalized welfare loss under score suppression after revocation: 0.0034593954707829743 (interval [-0.005808717016519411, 0.015049449655703574]). Task-completion decline: 0.0 (interval [0.0, 0.0]). Compare upper uncertainty bounds, not only means, with 0.02 and 0.05.
- H1 replay recovery-rate gain from retaining numerical feedback: 0 (interval [0, 0]; clustered by source task seed). This diagnostic is separate from original task behavior.
- H4 history-rule regret reduction versus the development-selected fixed comparator under coalition instructions and revocation: -7.462795050321356 (interval [-15.93993846283893, 0.1533442923023017]). History-versus-memoryless effects and all cooperative trade-offs are retained in the JSON.
- H5 exploratory public-message harm interaction: {"original": {"n": 5, "mean": -7.712924288078057, "bootstrap95": [-32.254733155448754, 8.42240055110427]}, "suppress_score": {"n": 5, "mean": 8.98374706704106, "bootstrap95": [-4.715368918419716, 22.682863052501837]}}. Positive values mean enabling public messages increases coalition-condition regret more than cooperative-condition regret. A channel-specific harm or migration claim also requires the fresh-message and consequential-outcome evidence.

## Main results

| Split | Completed | Revoked objective interaction | 95% seed bootstrap interval |
|---|---:|---:|---|
| development | 60 | 0.46590495172924024 | [-7.680208889637525, 8.283751155715095] |
| pilot | 60 | -16.562284213198968 | [-34.00535209537267, -0.5413697949592958] |
| heldout | 200 | -10.916549188427519 | [-21.578862889968722, -1.37360170872345] |

Positive interaction means feedback suppression reduces regret more under coalition than cooperative instructions. It does not establish intent, a mediation mechanism, or coalition benefit. All intervals are exploratory seed-cluster bootstraps.

## Held-out condition table

| Objective | Private revoked | Policy | N | Mean reward | Mean regret | Task completion |
|---|---|---|---:|---:|---:|---:|
| coalition | False | history_rule | 10 | 112.029 | 7.152 | 97.5% |
| coalition | False | memoryless_rule | 10 | 96.927 | 22.255 | 95.0% |
| coalition | False | original | 10 | 102.882 | 16.299 | 97.5% |
| coalition | False | peer_snapshot | 10 | 105.882 | 13.299 | 95.0% |
| coalition | False | suppress_score | 10 | 102.912 | 16.269 | 97.5% |
| coalition | True | history_rule | 10 | 108.203 | 10.978 | 92.5% |
| coalition | True | memoryless_rule | 10 | 102.420 | 16.762 | 100.0% |
| coalition | True | original | 10 | 115.666 | 3.515 | 100.0% |
| coalition | True | peer_snapshot | 10 | 110.310 | 8.871 | 95.0% |
| coalition | True | suppress_score | 10 | 104.443 | 14.738 | 95.0% |
| cooperative | False | history_rule | 10 | 114.828 | 4.353 | 100.0% |
| cooperative | False | memoryless_rule | 10 | 110.115 | 9.067 | 97.5% |
| cooperative | False | original | 10 | 109.991 | 9.190 | 95.0% |
| cooperative | False | peer_snapshot | 10 | 107.895 | 11.286 | 95.0% |
| cooperative | False | suppress_score | 10 | 114.076 | 5.105 | 97.5% |
| cooperative | True | history_rule | 10 | 114.897 | 4.284 | 100.0% |
| cooperative | True | memoryless_rule | 10 | 111.926 | 7.256 | 97.5% |
| cooperative | True | original | 10 | 115.750 | 3.431 | 100.0% |
| cooperative | True | peer_snapshot | 10 | 105.042 | 14.140 | 92.5% |
| cooperative | True | suppress_score | 10 | 115.444 | 3.738 | 100.0% |

## Hypothesis coverage

- **H0:** installed-runtime fixed-action gate passed. Full trace/fidelity counts appear below. Native prompt logs document formatted input; they are not an independent capture of encrypted provider traffic.
- **H1:** paired read-only diagnostic replay; see paper_results.json for recovery, abstention and conditional error. No diagnostic is inserted before an original actor decision.
- **H2:** objective interaction and separate coalition outcomes are reported; small seed counts and one-shot decision opportunities limit interpretation.
- **H3:** normalized cooperative welfare loss and task-completion decline are reported with intervals. Proposed bounds are 2% and five percentage points; point estimates alone do not establish noninferiority.
- **H4:** frozen development comparator: `original`. Whole controller assignments are compared on ten untouched held-out seeds. The selectors are frozen rules, not a trained or self-evolving OrchDebate implementation.
- **H5:** separate exploratory fresh-task/public-message ablation. Tasks and private profiles are regenerated after revocation; only explicit public posts are ablated. Effects alone cannot prove secret decoding or spontaneous channel migration.
- **Controller identifiability limitation:** a retain decision leaves the current guard in place. In a short one-shot run, history and memoryless rules can therefore settle on the same persistent guard. Differences in realized reward do not by themselves demonstrate a benefit from historical state.

## Integrity, usage and limitations

- Verified trace chains: 320/320; suppression failures: 0; revocation failures: 0.
- Fresh-task trace chains verified: 40/40.
- Reported agent-turn tokens in main episodes: 16,914,657. Provider retries, dollar charges and unreported usage are not inferred.
- Exact oracles use native reward enumeration. Missing decisions, explicit skips and violations are retained separately in episode_results.csv.
- Locally verified hash chains are reproducibility evidence, not independent attestation. One model and a small synthetic Jira task family do not establish broad safety.
- No confirmatory power or multiple-comparison claim is made. Extensions remain exploratory and are not pooled into the original study.
- Preserved unsuccessful attempts: 15 main and 11 fresh-task attempts, plus any interrupted directories without a result. Automatic authentication recovery was bounded to three total attempts; five retained failures received one final isolated fourth attempt. Completed outcomes were never rerun.

## Artifacts

- paper_results.json: full grouped estimates, paired effects and bootstrap intervals.
- episode_results.csv: every main episode, coalition metrics, task outcomes and reported tokens.
- fidelity_audit.json: per-episode trace and treatment checks.
- results/: raw traces, prompts, trajectories, task truth, exact oracle and native metrics.
- h1_diagnostic/ and h5_extension/: separate diagnostic and fresh-task evidence.
- EXTENSION_PROTOCOL.md and frozen_comparator.json: scope and held-out comparator freeze.
