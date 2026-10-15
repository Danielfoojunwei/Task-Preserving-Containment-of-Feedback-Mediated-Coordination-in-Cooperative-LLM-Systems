# Formal prior-art source check

Retrieved 2026-10-15T12:26:52.776141+00:00. Primary-source downloads only; no model/API calls.

Do not claim first discovery of authorization/denial/termination/retry leakage. A defensible contribution is an incremental controlled empirical evaluation and bounded mitigation under explicit observables and schedules.

## A Calculus for Flow-Limited Authorization

Owen Arden, Anitha Gollamudi, Ethan Cecchetti, Stephen Chong, Andrew C. Myers. arXiv:2104.10379v1 (2021-04-21). https://arxiv.org/abs/2104.10379v1

- Authorization decisions based on sensitive membership lists and passwords can compromise confidentiality; schemes may fundamentally require disclosure, which must be identified. **Locator:** Abstract and Section 1, printed pp.1-2; extracted text lines 20-35, 50-62.
- Authorization proofs can themselves form a side channel. FLAC protects proof confidentiality while other data policies are modified. **Locator:** Section 5, printed p.14; extracted text lines 873-877.
- 2021 report strengthens and corrects earlier FLAC (CSF 2016) and builds on FLAM (CSF 2015); authorization-flow interaction is established prior work. **Locator:** Section 1, printed p.3; extracted text lines 132-140; references [7],[9], printed p.33.

**Scope:** Formal language/type-system guarantees; no LLM-agent collusion experiments. Cover says technical report April 22, 2021; arXiv submission/history is April 21.

## The LLMbda Calculus: AI Agents, Conversations, and Information Flow

Zac Garby, Andrew D. Gordon, David Sands. arXiv:2602.20064v2 (2026-07-10). https://arxiv.org/abs/2602.20064v2

- An untracked Python retry loop outside CaMeL IFC reveals a secret-dependent policy-block/termination bit; adaptive reruns can launder the secret one bit at a time. The paper explicitly identifies this control-boundary failure and cites multi-run security. **Locator:** Section 1, printed p.2; extracted text lines 86-92.
- Proves termination-insensitive probabilistic noninterference (TIPNI), not termination-sensitive noninterference; compatibility rather than equal endpoint subdistributions is central. **Locator:** Section 4.2, printed pp.13-15; extracted text lines 606-701.
- An internal retry loop carries taint from a failed attempt into the next attempt and hence into the final plan. **Locator:** Section 7.1, printed p.20; extracted text lines 961-969.

**Scope:** Formal Lean calculus/interpreter plus AgentDojo banking evaluation; exact prior art for denial/retry leakage. Current theorem intentionally permits termination leakage.

## AgentSecBench: Measuring Prompt Injection, Privacy Leakage, and Tool-Use Integrity in LLM Agents

Faruk Alpay, Taylan Alpay. arXiv:2605.26269v1 (2026-05-25). https://arxiv.org/abs/2605.26269v1

- Defines intent-to-execution noninterference with permitted leakage and confidentiality leakage I(S;Y | authorized leakage, trusted inputs, policy). A zero canary result is not proof of zero information leakage. **Locator:** Section 3.2, printed p.5, Definitions 2-3; extracted text lines 201-225.
- One designated marker and one observation intervention; adaptive multi-turn adversaries and obfuscated encodings are outside the evaluated class. **Locator:** Section 4.6, printed p.11; extracted text lines 529-538.
- Exact-marker non-emission establishes resistance only to the chosen distinguisher; multistep plans, mixed authority, semantic encodings and larger models remain outside claims. **Locator:** Section 10, printed p.18; extracted text lines 901-915.

**Scope:** Six defense classes with Qwen3-0.6B and Qwen3-1.7B; paired adversarial/benign controls; lexical utility proxy.

## If Agents Were Angels, No Governance Would Be Necessary: Out-of-Band Policy Enforcement at a Trusted Tool Boundary

Marc Millstone, Tyler Akidau, Johannes Brüderl, Marat Pekker. arXiv:2608.27646v1 (2026-08-27). https://arxiv.org/abs/2608.27646v1

- Four protected email reconstructions occurred without exact field exposure. One trial used increasingly selective predicates over a masked email field and returned row counts as an oracle. **Locator:** Abstract; Section 8.1, printed pp.12-13; extracted text lines 774-816.
- Structural absence from one execution is not relational noninterference. Suggested defenses include coarsened counts/cursors, minimum cohorts and history-aware query budgets; none is evaluated. **Locator:** Section 8.1, printed p.13; extracted text lines 806-816.
- Warnings may themselves reveal the existence of protected data. Timing, aggregate execution, durable approval dispatch and broader deployment paths are outside the released evaluation. **Locator:** Section 10.1, printed p.13; extracted text lines 814 onward.

**Scope:** Out-of-band trusted tool boundary; does not claim to close row-count oracle or prove general noninterference. Defensive follow-on should compare scope with these limitations.

## Nonmalleable Progress Leakage

Ethan Cecchetti. arXiv:2505.12210v1 (2025-05-18). https://arxiv.org/abs/2505.12210v1

- Progress-insensitive noninterference permits termination behavior leakage, potentially arbitrary leakage within a run or across automatic restarts. Separates attacker-controlled progress leakage from approved progress downgrades. **Locator:** Abstract and Section 1, printed p.1; extracted text lines 1-39.
- Defines nonmalleable progress leakage and gives a type system with Rocq-verified theorems and inference for safe progress downgrades. **Locator:** Section 1, printed p.2; extracted text lines 91-106.

**Scope:** General formal IFC foundation; no claim to be an LLM-agent-specific collusion experiment.
