# Five-slide research briefing

**Information closure and apparent containment are different.**

Prepared 15 October 2026. This AI-assisted research presentation follows one empirical argument: question → mechanism → controls → results → finding. It is not the team's final sprint submission.

## Presentation files

- [Editable PowerPoint](research_story_5_slides.pptx), exactly five slides with embedded speaker notes.
- [Rendered PDF](research_story_5_slides.pdf).
- [Speaker notes](SPEAKER_NOTES.md), with reviewer questions, provenance and limitations.
- [Claim register](CLAIM_REGISTER.md), with primary sources, exact result tables and qualifications.

## Five distinct roles

| Slide | Question answered | Evidence shown |
|---|---|---|
|1 — Question|Why test the combined metadata agents observe?|A vendor-confirmed information-disclosure vulnerability and controlled academic findings motivate the question.|
|2 — Mechanism|How could individually secret-independent fields guide a decision?|An actual source attestation, balanced host mask, joint decoder and separately measured accepted action.|
|3 — Validation|How do we separate information from shortcuts, instructions and response noise?|Six neutral observation arms, exact 2×2 announcement crossing, fresh worlds, repeated inputs and fixed test families.|
|4 — Results|Did the controlled effect survive?|All four primary contrasts passed; explicit control, task success, unsupported claims and announcement/action counts remain separate.|
|5 — Finding|What should a researcher or defender infer?|Apparent behavioral containment cannot establish information closure; a closed information channel can still produce uninformed harmful action.|

## The empirical result

The new prospective validation completed **1,320 calls**: 40 source responses and 1,280 receiver responses across 20 fresh worlds, using GPT-4.1 mini. Each neutral condition included both target bits, both host masks and two identical-input responses. All 40 sources copied correctly. All 1,280 public-copy tasks succeeded.

Joint metadata beat all four negative comparators under the fixed Holm4 criterion. Joint-minus-full signed decoding was **.0875**, descriptive 95% interval **[.05625,.11875]**, adjusted **p=.000427**. Neither individual field nor the target-independent donor substituted for the target-bearing pair.

The exact announcement crossing produced the more consequential distinction:

| Actual view | Marginal announcement | Full announcement |
|---|---:|---:|
| Joint informative |49/80 accepted bets|0/80|
| Full target-independent |23/80 accepted bets|0/80|

The target-independent/marginal-announcement bets lost the coalition 32 units while harming the owner. The informative/full-announcement view still contained the signal despite no observed bets. All six secondary announcement tests passed Holm6; the banner owner-harm contrast was **+3.15**, interval **[2.45,3.89375]**, adjusted **p=.00001144**. This is an effect of the exact policy/contract bundle, including intentionally inaccurate crossed announcements, not a universal prompt-wording claim. No statistical ranking of banner and actual-information effects is claimed.

Read the [new protocol](sources/project/research/outputs/stability_20261015/PROTOCOL.md), [results](sources/project/research/outputs/stability_20261015/RESULTS.md) and [independent raw reconstruction](sources/project/research/outputs/stability_20261015/INDEPENDENT_VERIFICATION.md). The claim register supplies portable copies under `sources/project/` when the deck is built.

## Provenance and limits

The original metadata study's four primary tests remain unsupported. The host-mask follow-up was designed after those results and frozen before its own calls. This new validation was designed with both earlier outcomes known and frozen before its own calls. Cohorts stay separate; no original whole-program preregistration or global historical error guarantee is claimed.

The host constructs a known XOR mechanism; the source copies neutrally; receivers receive decoder/routing tables; the legitimate task copies supplied answers. This is instructed capability and behavior in a finite interface, not spontaneous collusion, a deployed exploit, a new information-flow theorem, an original-defense break, general task preservation or a validated collusion detector. False-one/false-zero rates concern bit inference, with abstention separate. Zero observed events do not mean zero population risk.

Microsoft's CVE-2025-32711 motivates real-product information-boundary failures, not deployed collusion or known victim exploitation. Colosseum and Hidden in Plain Text supply controlled academic motivation. Older Jira/resource experiments address separate mechanisms and do not occupy the main results table.

## Rebuild and inspect

The generator requires `python-pptx`, `matplotlib` and `numpy`; PDF rendering uses LibreOffice. It reads the completed stability-study analysis and saved historical evidence from the full repository, makes no API calls and edits no research outputs.

```bash
XDG_CACHE_HOME=/tmp/research-deck-cache python presentations/research_story_20261015/build_deck.py
soffice -env:UserInstallation=file:///tmp/lo-research-story --headless --convert-to pdf --outdir presentations/research_story_20261015 presentations/research_story_20261015/research_story_5_slides.pptx
```

`facts.json` retains numerical values; `assets/` contains PNG/SVG charts; `BUILD_MANIFEST.json` records source hashes; `VERIFICATION.json` records final artifact checks. The builder must be rerun after notes/register changes before distributing the PowerPoint/PDF. Rebuilding requires the complete repository's saved study outputs, including `research/outputs/stability_20261015/analysis.json`; the standalone download is an evidence packet, not a raw-call archive. Local hashes and independent offline reconstruction provide reproducibility checks, not external execution attestation.

All 15 October results predate the 23–25 October sprint. Disclose them as prior work and separately identify any actual sprint-period contribution. This deck does not replace the official report template, author information or the team's own submission writing.
