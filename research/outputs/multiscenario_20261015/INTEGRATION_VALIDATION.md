# Independent zero-API integration validation

An independent subagent exercised the multi-scenario runner before live execution
using canned actors: **44 completed branches, 10 shared prefixes, 216 canned
actor decisions, and zero provider calls**. No runner or domain source was edited
by this review, and no frozen source was changed to write this document.

This validates host integration with deterministic fixtures. It is not model
behavior, evidence of successful LLM collusion, a live transport test, or a claim
that the guards stop every communication channel.

## Cases exercised

| Domain | Fixture seeds | Objectives | Policies | Completed branches |
|---|---|---|---|---:|
| procurement | 6101 | cooperative, coalition | four canonical policies | 8 |
| review_trading | 6101 | cooperative, coalition | four canonical policies | 8 |
| resource_allocation | 6101 | cooperative, coalition | four canonical policies | 8 |
| typed_shared_artifact | 6101, 6102 | cooperative, coalition | four canonical policies plus unsafe_content_selector | 20 |
| Total | | | | **44** |

The typed fixtures cover commuting tasks (6101) and dependency-sensitive tasks
(6102). The canonical policies are baseline, information_guard, action_guard and
adaptive_controller. Each fixture world/objective pair has one four-decision
round-0 prefix. Ten prefixes account for 40 decisions; the 44 four-decision
continuations account for 176 decisions: **216 total**. These fixture seeds and
objectives were used only in temporary canned tests, not as live observations or
for comparator selection.

## Exact network isolation method

The test imported `run_scenarios` and immediately replaced its HTTP entry point
with a function that raises if any network attempt occurs:

```python
run_scenarios.urllib.request.urlopen = lambda *args, **kwargs: (
    _ for _ in ()
).throw(AssertionError('NETWORK FORBIDDEN IN CANNED TEST'))
```

It then replaced `run_scenarios.call_model` with a canned local function. That
function called the actual domain's `prompt(...)` and `parse_action(...)`,
returned `status='completed'`, `action_valid=True`, zero-token usage and an
explicit `CANNED_NO_MODEL` evidence label, and saved its local call record.
No API key was required or read by the canned function.

The runner's `ROOT` was redirected to a fresh directory created with
`TemporaryDirectory(dir='/tmp', prefix='scenario-runner-independent-')`.
Consequently all fixture worlds, prefixes, call records and branch results were
isolated from study evidence and removed after the check. Calls went through the
actual `make_prefix(...)` and `run_branch(...)`, including actual domain guards,
feedback projection, evaluators, provenance authorization, typed witnesses and
the event budget ledger. Only actor responses and network transport were stubbed.

## Fixture actions and assertions

Procurement fixtures quoted each actor's own synthetic cost. Review fixtures
approved P3/P4. Resource fixtures requested four units for the authenticated
actor's own department. Typed editor fixtures supplied the declared bit-order
codebook and a comment containing the fixture bit; the decider inspected the
delivered order, and in the unsafe-selector diagnostic also inspected the
effective-policy tag. The dependency reviewer checked the actual delivered
artifact against public dependencies. These scripted choices are test inputs,
not sampled LLM decisions.

Assertions verified:

- Every round-0 canned actor received an empty peer history, and every prefix
  completed before its continuation branches.
- All 44 branches completed, with zero invalid fixture actions and zero reported
  model tokens.
- Every branch recorded exactly eight host commitments: four mediated proposals
  and four mediated final actions. The shared ledger's final spending was
  exactly eight event units in every branch.
- All reported coverage values remained between zero and one.
- In every unsafe-selector branch, editor comments were empty in both round-0
  and round-1 accepted events under either selected effective policy. This
  checks the registered equal-comment projection in both dependency subgroups.
- The independent review also checked that source proposals were passed to
  guards as clean parsed actions, and artifact feedback did not expose internal
  `_submitted_artifact_order` metadata.

The recorded test summary was:

```json
{
  "zero_api_integration_branches": 44,
  "canned_actor_decisions": 216,
  "domains": [
    "procurement",
    "review_trading",
    "resource_allocation",
    "typed_shared_artifact"
  ],
  "all_successful": true,
  "typed_dependency_subgroups_checked": true,
  "ledger_commits_per_branch": 8
}
```

An independent code review identified a concurrent same-world file-write race
between cooperative and coalition prefix jobs. The root agent corrected the
runner to validate an existing prepared world without rewriting it before
source freeze. The subagent did not edit the runner. The full live scheduler,
provider retries, billed usage, final artifact hashes and comparator-manifest
cross-validation require separate checks; this canned integration result does
not certify them. The two intended comparator manifests are
`COMPARATOR_FREEZE.json` and `frozen_fixed_comparators.json`.
