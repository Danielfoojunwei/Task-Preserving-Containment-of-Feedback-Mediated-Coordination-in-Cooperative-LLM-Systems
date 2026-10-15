# OrchDebate: exact reuse boundary and implementation status

## Verified vs unavailable

The public OpenReview record identifies *OrchDebate: Adaptive Orchestration for Multi-Agent Debate via Self-Evolving Skills* and describes structured-state orchestration over reusable debate-control skills. The PDF and public API did not return the paper in this session. No claim is made about its exact state schema, optimizer, training loop, catalogue, ablations or performance. This code is **OrchDebate-inspired**, not an algorithm-faithful reproduction or copied library.

## Mapping

| Abstract-level inspiration | Our concrete adaptation | Build status |
|---|---|---|
| Structured state | `SkillState`: current/prior numeric exposure counts, access state, policy epoch and permitted intervention budget; excludes private rewards/costs/objective labels | Implemented + tested |
| Reusable control skills | `retain`, `peer_snapshot`, `suppress_score` with host contracts and immutable observations | Implemented + fixture tested |
| State-dependent orchestration | `choose_skill`: frozen transparent history-aware rule and memoryless ablation | Implemented + tested; NOT an LLM |
| Model-selected skill | `parse_skill_proposal`: exact schema and state-digest validation for an untrusted selector | Interface implemented; model invocation NOT implemented |
| Self-evolving skills | Candidate changes may be developed offline, evaluated on development tasks, then frozen and approved before held-out evaluation | Design only; NOT implemented |
| Debate success | Replaced by exact task regret + cooperative utility + completion + cost | Evaluation design and analyzer implemented; no live results |

## Why the distinction matters

The paper inspires HOW to choose interventions. Colosseum defines WHERE decisions happen and HOW cooperative task outcomes are measured. The trusted host decides WHICH operations are permitted. Neither majority agreement nor a cleaner transcript is a safety reward. A self-evolving defender must not rewrite the reward evaluator or suppress evidence.

Example: if the host has observed only retrospective peer-record score mutation, choose a shared-snapshot guard. If actor receipts themselves carry cumulative scores, peer-only protection is insufficient for that exposure; the rule selects score suppression. If the task contract requires score feedback or no switches remain, retain the current setting. These are exposure-based engineering choices, not established harm-optimal decisions.

The rule cannot infer private costs or collusive intent, and it cannot undo information already observed. Scores or task identifiers can survive elsewhere. Every new policy version invalidates previous claims of transfer.

## Test the added value, not just the combined system

1. Compare original and fixed score suppression first.
2. Compare strongest fixed guard with memoryless and history-aware rules using identical skills.
3. Only then integrate a model selector, with equal information and total budget.
4. Only after validating a fixed library, evaluate a library evolved on development tasks against a frozen library on new tasks.

A successful defense comparison is not evidence that OrchDebate's full method was implemented. A near-zero effect of adding the controller is a meaningful null: use the simpler fixed rule.
