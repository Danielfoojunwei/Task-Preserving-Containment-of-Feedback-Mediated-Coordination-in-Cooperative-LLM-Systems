# Post-freeze audit disclosures

## Residual numeric receipt channel in the typed artifact

Recorded at 2026-10-15T11:45:59.870300+00:00. Runtime progress snapshot: 40 completed prefixes, 46 completed discovery branches, stage discovery_branches. Root inspected counts only, not branch actions/outcomes, when recording this source-code audit finding. It arrived after the source freeze and after live execution began.

An independent read-only audit found that TypedArtifact.feedback hides the editor's round-1 artifact text/order, but computes a numeric joint_reward from that later attestation. A null versus valid canonical round-1 artifact can therefore alter a visible 0/10 feedback value while the actual committed round-0 artifact and evaluated task utility stay unchanged. Baseline and action_guard retain this receipt path; information_guard removes it. The sender was explicitly allowed to use reachable fields but was not given this receipt codebook. This is an architectural capability finding; observed exploitation must be established from live traces.

No frozen source, input, seed, primary endpoint, completed response, or main test is changed. The narrow action-guard primary comparisons remain the registered tests. Their interpretation includes this residual numeric channel and cannot establish all-channel containment. The secondary unsafe-selector live arm no longer isolates policy-label disclosure by itself: equal editor-comment projection does not remove this additional receipt path. The original two-world label-only certificate remains a separate non-LLM capability proof with its own restricted transcript. Live recovery cannot be attributed uniquely to the policy tag without checking complete delivered inputs.

The follow-up certificate and any proposed joint guard or committed-state feedback correction are labeled additional exploratory/architectural work. They are not retroactively inserted into the four-test confirmatory family. A further live arm, if run, requires its own dated protocol and source hashes before its calls.
