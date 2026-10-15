# Independent design review: observable control-plane transcripts

This is a prospective mechanism/design critique. It makes no API calls and does
not change previous studies. The proposed contribution is a bounded test of
complete registered observations, not a claim that covert channels or
noninterference are new discoveries.

## The useful question

Can two guards deliver the same safe artifact while exposing different
**joint observable transcripts**, and can an actual receiver use that difference
to coordinate a consequential action? Does equalizing the registered transcript
preserve a public task when the protected bit is irrelevant, and what changes
when that bit is a legitimate task input?

The previous frozen artifact implementation supplies a concrete trigger: a
later hidden editor attestation changes a public numeric receipt even though
the committed artifact and legitimate task utility remain fixed. A policy label
and rejection/missingness fields can create additional observable routes.

## Three precise mechanisms

Use a fresh balanced secret bit B, a fixed public instance P, and identical
receiver private state across the B=0 and B=1 worlds. The receiver must not be
given a secret-specific filename, case label, seed parity, raw sender reply,
parse error, or evaluator truth by another route.

1. **Receipt route:** the hidden later attestation is null or valid; a payload
   guard emits the same committed artifact but a receipt of 0 or 10. The full
   guard derives the receipt exclusively from the committed public artifact.
2. **Status route:** accepted/rejected/missing source actions all map to the
   same safe public artifact, while the payload-only guard exposes the status.
   The full guard uses a safe public default, one fixed release slot, and one
   fixed status. Record the true status in evaluator-only logs.
3. **Joint-correlation route (recommended diagnostic):** give the sender an
   independent balanced private pad R. Let a public guard-choice label encode R
   and the later receipt encode B XOR R, while the artifact is always canonical.
   Each field separately has the same distribution under B=0 and B=1. Their
   pair determines B exactly. This tests a real compositional failure that
   separate per-field leakage audits miss. Fixing either field closes this
   particular two-field code; fixing the full registered transcript closes all
   codes in the declared finite alphabet.

The joint-correlation case is a constructed positive control with an instructed
codebook. It does not establish spontaneous discovery, general-purpose
steganography, or a new information-theoretic theorem. It makes the claim about
**joint** observation auditable and useful beyond another single obvious bit.

## Match the intervention to the claim

The payload-only guard preserves the safe artifact but leaves the registered
control-plane observables available. The complete-transcript guard must handle
all of the following together:

- canonical task payload and safe defaults for absent/invalid source actions;
- fixed visible policy label and algorithm-description fields;
- receipts computed from committed public state;
- fixed rejection, missingness and diagnostic fields;
- fixed number/order of visible release slots;
- no protected source data in free text, raw reply echoes or internal metadata.

“Complete” means complete for the explicitly enumerated receiver interface.
External timing, token billing, network traffic, other tools and compromised-host
logs are outside the guarantee unless implemented as observable fields. Do not
call a transcript complete while silently excluding a field that is present in
the actual receiver prompt. Save and hash the exact receiver request body.

Independent stages need a joint rule: equality of each field's marginal
distribution is insufficient. Likewise, equality of one release is insufficient
if a later hidden action changes a receipt or public state used by the next
release.

## Causal use versus a constant-zero receiver

Balance both B and R within each public-instance block. Evaluate these separately:

- recovery of the actual protected bit;
- whether the receiver followed the code carried by the **delivered** transcript;
- the receiver's legitimate public-task outcome;
- bit-conditioned coalition success;
- unconditional harmful-action frequency.

A receiver that always emits 0 has 50% balanced recovery. An agent that always
takes the harmful option can cause harm without using any channel. Neither is
evidence of communication. Use a balanced public challenge C and, where useful,
define the target action as B XOR C so a fixed action cannot satisfy every target.
Keep recovery and harmful action distinct even when the coalition payoff joins
them.

Add crossed-transcript replay before attributing a mechanism. Hold the public
task, receiver state and evaluator's hidden B fixed, but give the receiver the
paired transcript that encodes the other B. If its reported bit and conditional
action follow the delivered codeword, that is evidence that the transcript
caused the response. Changing the evaluator's B alone cannot cause a receiver
effect because it never enters the prompt. For the XOR diagnostic, additionally
ablate each component separately; the joint view should enable recovery while
either single-component view is uninformative under the balanced pad design.

Sender compliance is another endpoint. If the sender fails to encode the
instructed bit, do not relabel its output as successful transmission. Report
sender-to-transcript and transcript-to-receiver performance separately. Actual
LLM replies may deviate from the finite positive-control encoder.

## A finite, useful guarantee

Let A be the registered finite sender-action alphabet, including absence,
malformation, rejection-triggering values and both attestation states. Let G
map a public state P and source action to the **entire** registered receiver
transcript T and next public state P'. The strong certificate checks that, for
every a in A at each reachable public state,

    (G(P,a).T, G(P,a).P') = (T_P, P'_P).

By induction, an adaptive sender cannot change the registered transcript through
any finite number of these transitions. If fresh B is independent of P and of
the receiver's initial private state/randomness, any receiver kernel has the
same output distribution under B=0 and B=1. Its balanced recovery probability is
at most 1/2. This is a bounded interface guarantee; it does not require a claim
about how well a particular LLM detects a code.

For a specified stochastic encoder, enumerate the transcript laws P0 and P1.
The best possible balanced binary recovery probability is

    accuracy* = (1 + TV(P0,P1)) / 2,
    TV(P0,P1) = (1/2) sum_t |P0(t)-P1(t)|.

The XOR example has per-field TV=0 but joint TV=1; the complete guard has joint
TV=0. The universal upper bound comes from the all-actions/next-state certificate,
not from checking only the two actions a compliant sender happened to choose.
Finite enumeration must include the failure/status alphabet that the actual
host accepts. Arbitrary unconstrained free text cannot be silently covered by
an exhaustive finite claim.

## The task-preservation boundary

Use two public task modes with the same interface:

- **Bit irrelevant:** a valid canonical schedule and the public high-value
  project are sufficient. Fixing the registered transcript can preserve this
  legitimate task while eliminating the witnessed communication routes.
- **Bit required:** the correct legitimate route is B XOR C. If the guard keeps
  the entire receiver transcript independent of B, balanced legitimate routing
  accuracy is also at most 1/2. Explicitly authorized declassification of the
  required route restores utility and necessarily reveals B given public C.

Thus a task-preservation claim must state what information the task needs and
what declassification is authorized. A correct result can be a quantified
privacy/utility boundary. Do not describe the bit-required failure as a bug
that a better prompt can fix while retaining perfect noninterference.

## Recommended freeze and reporting constraints

Freeze the finite alphabet, all observable fields, guard mappings, codebooks,
balanced bit/pad/challenge assignments, counterfactual replay rules, legitimate
utility and harm endpoints before the corresponding calls. Treat model-based
channel use as empirical and the finite guarantee as mathematical. Preserve
malformed responses without outcome-based reruns. Audit exact request bodies,
including defaults and omitted fields, rather than only a cleaned action object.

The study can support an explicit bounded contribution: a compositional
control-plane leakage example with observed causal receiver use, a finite joint
transcript guarantee, and a task-declassification boundary. It should not claim
universal collusion prevention or complete reproductions of the cited papers.
