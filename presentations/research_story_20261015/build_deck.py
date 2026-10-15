"""Build a five-slide research briefing from frozen result files.

Only presentation artifacts are written. No model calls or source edits.
"""
from pathlib import Path
import hashlib
import json
import os
import re
import shutil

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
STUDIES = REPO / "research/outputs"
os.environ.setdefault("MPLCONFIGDIR", "/tmp/research-deck-matplotlib")

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Inches, Pt

BG = "0B1425"
PANEL = "14233B"
PANEL2 = "1B304C"
WHITE = "F6F8FC"
MUTED = "B6C4D9"
DIM = "899AB4"
TEAL = "5AD7C3"
GOLD = "F0C778"
ORANGE = "F39A7B"
GRID = "31445F"
FONT = "Arial"
W, H = 13.333333, 7.5
ASSETS = HERE / "assets"
SOURCES = HERE / "sources"
ASSETS.mkdir(exist_ok=True)
SOURCES.mkdir(exist_ok=True)


def load(name):
    return json.loads((STUDIES / name).read_text())


host = load("hostmask_20261015/INDEPENDENT_REPLICATION.json")
main = load("controlplane_20261015/controlplane_results.json")
jira = load("revision_20261015/revision_results.json")
domains = load("multiscenario_20261015/scenario_results.json")
assert host["primary"]["mean"] == 0.2265625
assert host["primary"]["exact_two_sided_p"] == 0.00006103515625
assert not any(x["positive_direction_supported"] for x in main["primary_family"].values())
assert sum(x["primary_harm_reduction_supported"] for x in domains["primary_family"].values()) == 1
assert jira["primary_family"]["R1"]["directional_support"]
assert not jira["primary_family"]["R2"]["directional_support"]

original = []
crossed = []
for path in (STUDIES / "hostmask_20261015/results/main").glob("*/result.json"):
    row = json.loads(path.read_text())
    if row["model_alias"] == "mini" and row["world_seed"] in range(7701, 7709) and row["policy"] == "payload_only":
        original.append(row["metrics"]["coalition_payoff"])
for path in (STUDIES / "hostmask_20261015/results/crossed").glob("*/result.json"):
    crossed.append(json.loads(path.read_text())["metrics"]["coalition_payoff"])
assert len(original) == len(crossed) == 32
assert sum(original) == 20 and sum(crossed) == -50

selected_sources = {
    "jira_results.json": "revision_20261015/revision_results.json",
    "jira_report.md": "revision_20261015/REVISED_EXPERIMENT_REPORT.md",
    "domain_results.json": "multiscenario_20261015/scenario_results.json",
    "domain_interpretation.md": "multiscenario_20261015/FINAL_INTERPRETATION_AUDIT.md",
    "main_metadata_results.json": "controlplane_20261015/controlplane_results.json",
    "main_metadata_interpretation.md": "controlplane_20261015/FINAL_INTERPRETATION_AUDIT.md",
    "hostmask_replication.json": "hostmask_20261015/INDEPENDENT_REPLICATION.json",
    "hostmask_results.md": "hostmask_20261015/HOSTMASK_RESULTS.md",
    "literature_positioning.md": "controlplane_20261015/LITERATURE_POSITIONING.md",
}
for destination, relative in selected_sources.items():
    shutil.copy2(STUDIES / relative, SOURCES / destination)

# Retain every project artifact directly cited by the claim register so that
# the downloadable presentation package has usable evidence links on its own.
claim_register = HERE / "CLAIM_REGISTER.md"
retained_project_sources = {}
if claim_register.exists():
    for relative in sorted(set(re.findall(r"\]\(sources/project/([^)]+)\)", claim_register.read_text()))):
        original_path = REPO / relative
        assert original_path.is_file(), relative
        destination = SOURCES / "project" / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(original_path, destination)
        retained_project_sources[relative] = hashlib.sha256(original_path.read_bytes()).hexdigest()

facts = {
    "host_primary": host["primary"],
    "jira_primary": {k: {n: v[n] for n in ("n", "mean", "bootstrap95", "holm_p_family_2", "directional_support")}
                     for k, v in jira["primary_family"].items()},
    "domain_primary": {k: {n: v[n] for n in ("n", "mean", "bootstrap95", "holm_p_family_4", "primary_harm_reduction_supported")}
                       for k, v in domains["primary_family"].items()},
    "main_metadata_supported": 0,
    "main_metadata_tests": 4,
    "mini_policy_decoding": {k: v["S"] for k, v in host["models"]["mini"]["policies"].items()},
    "crossed_cases_per_condition": 32,
    "crossed_total_payoff_original": sum(original),
    "crossed_total_payoff_swapped": sum(crossed),
    "public_copy_success": [320, 320],
    "mini_marginal_correct_bets": 31,
    "mini_marginal_wrong_bets": 10,
    "mini_marginal_net_payoff": 22,
    "mini_marginal_mean_payoff_bootstrap95": [-0.03125, 0.6875],
}
(HERE / "facts.json").write_text(json.dumps(facts, indent=2) + "\n")

plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 10.5,
    "text.color": "#" + WHITE, "axes.labelcolor": "#" + MUTED,
    "xtick.color": "#" + MUTED, "ytick.color": "#" + WHITE,
    "axes.facecolor": "#" + BG, "figure.facecolor": "#" + BG,
    "axes.edgecolor": "#" + GRID,
    "savefig.facecolor": "#" + BG,
})

# A descriptive policy-level view; the registered contrast is marginal - full.
fig, ax = plt.subplots(figsize=(4.35, 2.05))
fig.subplots_adjust(left=.32, right=.96, bottom=.28, top=.96)
policies = ["payload_only", "marginal_guard", "transcript_guard"]
labels = ["Payload only", "Field-marginal", "Full transcript"]
colors = [TEAL, GOLD, MUTED]
for y, policy, color in zip([2, 1, 0], policies, colors):
    summary = host["models"]["mini"]["policies"][policy]["S"]
    mean = summary["mean"]; lo, hi = summary["bootstrap95"]
    ax.errorbar(mean, y, xerr=[[mean-lo], [hi-mean]], color="#" + color,
                marker="o", markersize=6, capsize=4, linewidth=2.0, zorder=4)
ax.set_yticks([2, 1, 0], labels)
ax.set_xlim(-.025, .52)
ax.set_ylim(-.55, 2.5)
ax.set_xticks([0, .25, .5], ["0", ".25", ".50"])
ax.set_xlabel("Signed decoding score S", fontsize=10.3, labelpad=4)
ax.axvline(0, color="#" + DIM, linestyle="--", linewidth=1)
ax.grid(axis="x", color="#" + GRID, alpha=.7)
ax.tick_params(length=0, labelsize=10.1)
for spine in ax.spines.values(): spine.set_visible(False)
fig.savefig(ASSETS / "signed_decoding.png", dpi=300)
fig.savefig(ASSETS / "signed_decoding.svg")
plt.close(fig)

# Secondary causal control. Raw total payoff, not a significant mean-profit claim.
fig, ax = plt.subplots(figsize=(4.35, 1.6))
fig.subplots_adjust(left=.18, right=.97, bottom=.28, top=.94)
values = [sum(original), sum(crossed)]
ax.bar([0, 1], values, color=["#" + TEAL, "#" + ORANGE], width=.52)
ax.axhline(0, color="#" + DIM, linewidth=1)
for x, value in enumerate(values):
    ax.text(x, value + (3 if value > 0 else -3), f"{value:+.0f}",
            ha="center", va="bottom" if value > 0 else "top", fontsize=13, fontweight="bold")
ax.set_xticks([0, 1], ["Original", "Opposite-bit"])
ax.set_yticks([-50, 0, 20])
ax.set_ylim(-65, 35)
ax.set_ylabel("Total payoff", fontsize=9.8, labelpad=3)
ax.tick_params(length=0, labelsize=10.2)
for spine in ax.spines.values(): spine.set_visible(False)
fig.savefig(ASSETS / "crossed_payoff.png", dpi=300)
fig.savefig(ASSETS / "crossed_payoff.svg")
plt.close(fig)

prs = Presentation()
prs.slide_width = Inches(W); prs.slide_height = Inches(H)
prs.core_properties.title = "Auditing Coordination Channels: From Reproduction to Causal Evidence"
prs.core_properties.subject = "Five-slide research briefing with source-backed motivation and bounded findings"
prs.core_properties.author = "AI-assisted research briefing; author metadata not supplied"
prs.core_properties.keywords = "AI collusion, causal audit, metadata, task preservation, Apart Research"


def box(slide, x, y, w, h, fill=PANEL, radius=True, line=None):
    kind = MSO_SHAPE.ROUNDED_RECTANGLE if radius else MSO_SHAPE.RECTANGLE
    shape = slide.shapes.add_shape(kind, Inches(x), Inches(y), Inches(w), Inches(h))
    shape.fill.solid(); shape.fill.fore_color.rgb = RGBColor.from_string(fill)
    shape.line.fill.background() if line is None else None
    if line:
        shape.line.color.rgb = RGBColor.from_string(line)
        shape.line.width = Pt(.7)
    if radius: shape.adjustments[0] = .10
    return shape


def txt(slide, text, x, y, w, h, size=16, color=WHITE, bold=False, align=None):
    shape = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    frame = shape.text_frame; frame.clear(); frame.word_wrap = True
    frame.margin_left = frame.margin_right = 0
    frame.margin_top = frame.margin_bottom = 0
    frame.vertical_anchor = MSO_ANCHOR.TOP
    for i, value in enumerate(text.split("\n")):
        p = frame.paragraphs[0] if i == 0 else frame.add_paragraph()
        p.text = value; p.font.name = FONT; p.font.size = Pt(size)
        p.font.bold = bold; p.font.color.rgb = RGBColor.from_string(color)
        p.space_after = Pt(0); p.space_before = Pt(0); p.line_spacing = 1.08
        if align is not None: p.alignment = align
    return shape


def arrow(slide, x, y, w=.2, h=.22, color=DIM):
    return box(slide, x, y, w, h, color, radius=False)


def base(number, label, title, subtitle):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    slide.background.fill.solid(); slide.background.fill.fore_color.rgb = RGBColor.from_string(BG)
    box(slide, .55, .36, .35, .05, TEAL, radius=False)
    txt(slide, f"0{number}  /  {label.upper()}", 1.03, .27, 11.0, .25, 10.5, TEAL, True)
    txt(slide, title, .55, .71, 12.23, .65, 29.5, WHITE, True)
    txt(slide, subtitle, .55, 1.39, 12.20, .46, 14.3, MUTED)
    txt(slide, "15 OCT 2026  |  PRE-SPRINT EVIDENCE  |  AI-ASSISTED BRIEFING",
        .55, 7.20, 10.8, .15, 8.5, DIM)
    txt(slide, str(number) + " / 5", 12.10, 7.17, .65, .22, 10.2, MUTED, align=PP_ALIGN.RIGHT)
    return slide


def source_link(slide, label, url, x, w):
    # A shape-level link preserves readable text color in LibreOffice/PDF.
    shape = txt(slide, label, x, 6.98, w, .15, 8.6, MUTED)
    shape.click_action.hyperlink.address = url


# 01 — external motivation and the precise scope of the paper transfers.
s = base(1, "Context", "Why audit the paths agents use to coordinate?",
         "Product failures and controlled research motivate the question; they do not validate our results.")
cards = [
    ("REAL PRODUCT VULNERABILITY", "Microsoft 365 Copilot", "CVE-2025-32711",
     "AI command injection enabled unauthorized information disclosure over a network.",
     "Microsoft CNA • June 2025", ORANGE),
    ("CONTROLLED WORKPLACE BENCHMARK", "Colosseum", "11 of 19 models",
     "showed positive changes in action-level coalition advantage when private chat was enabled.",
     "Not evidence of deployed collusion", TEAL),
    ("CONTROLLED CAPABILITY EXPERIMENT", "Hidden in Plain Text", "Filtering was bypassed",
     "Optimized agents used covert signaling in a candidate-screening task despite oversight and paraphrasing.",
     "Constructed task, not a hiring incident", GOLD),
]
for i, (tag, title, stat, body, qualifier, accent) in enumerate(cards):
    x = .55 + i * 4.13
    box(s, x, 2.02, 3.96, 2.65)
    box(s, x+.20, 2.22, .07, .33, accent, radius=False)
    txt(s, tag, x+.40, 2.22, 3.33, .30, 9.3, accent, True)
    txt(s, title, x+.23, 2.70, 3.49, .33, 19, WHITE, True)
    txt(s, stat, x+.23, 3.13, 3.50, .42, 24 if i != 2 else 20, accent, True)
    txt(s, body, x+.23, 3.68, 3.48, .66, 14.0, WHITE)
    txt(s, qualifier, x+.23, 4.40, 3.50, .18, 10.4, MUTED)
txt(s, "PAPER LINEAGE WE USED", .55, 5.00, 12.0, .22, 11.0, TEAL, True)
lineage = [
    ("Colosseum", "Native Jira runtime"),
    ("FLOWSEAL", "Release-control transfer"),
    ("OCELOT", "Composition-inspired stress test"),
    ("OrchDebate", "Conceptual selector only"),
]
for i, (title, body) in enumerate(lineage):
    x = .55 + 3.10*i
    box(s, x, 5.35, 2.93, .78, PANEL2)
    txt(s, title, x+.17, 5.47, 2.61, .23, 15.2, WHITE, True)
    txt(s, body, x+.17, 5.80, 2.61, .18, 11.2, MUTED)
txt(s, "Our question: which observation changes harmful decisions, and what does closing it cost useful work?",
    .55, 6.45, 12.20, .37, 16.3, TEAL, True)
source_link(s, "[S1] Microsoft CNA / vendor advisory", "https://msrc.microsoft.com/update-guide/vulnerability/CVE-2025-32711", .55, 3.8)
source_link(s, "[S2] Colosseum v2, §5.4 / Figure 4", "https://arxiv.org/abs/2602.15198v2", 4.71, 3.8)
source_link(s, "[S3] Hidden in Plain Text v2, §5.1", "https://arxiv.org/abs/2410.03768v2", 8.87, 3.8)

# 02 — a MECE map of the local identification questions.
s = base(2, "Design", "What we changed, and which question each change answers",
         "Four distinct causal ambiguities in our setup. This is a study map, not a universal taxonomy of collusion.")
columns = [(.55, 1.54), (2.09, 3.02), (5.11, 4.59), (9.70, 3.08)]
for (x,w), label in zip(columns, ["TARGET", "QUESTION", "SETUP CHANGE", "WHY IT WAS NEEDED"]):
    txt(s, label, x+.13, 1.97, w-.20, .22, 10.3, TEAL, True)
rows = [
    ("CONTEXT", "Old plans or future access?",
     "Native Jira: history visible/hidden × posting allowed/denied. Reuse the actual planning prefix.",
     "Unbundle a runtime intervention."),
    ("DISCLOSURE", "Canonical payload or complete receiver view?",
     "Hold the public artifact fixed; vary policy labels, receipts, statuses and joint fields across three guards.",
     "Measure signals beyond sanitized message content."),
    ("EXECUTION", "Communication or contract violations?",
     "Four synthetic domains; disclosure and action guards; matched cooperative and coalition objectives.",
     "Separate information restriction from public-rule enforcement."),
    ("MEASUREMENT", "Defense success, failed encoding, or scoring error?",
     "Audit source adherence and whole-action gating. Freeze a new host-masked study with field-specific scoring.",
     "Diagnose the null before changing the hypothesis."),
]
for i, row in enumerate(rows):
    y = 2.38 + 1.04*i
    box(s, .55, y, 12.23, .94, PANEL if i % 2 == 0 else PANEL2)
    for col, value in enumerate(row):
        x,w=columns[col]
        txt(s, value, x+.13, y+.15, w-.25, .70,
            (11.0 if value == "MEASUREMENT" else 12.7) if col == 0 else 13.2,
            TEAL if col == 0 else WHITE, col == 0)
txt(s, "Crossed delivery is the mechanism control: change the delivered codeword while holding the evaluator target fixed.",
    .55, 6.65, 12.23, .25, 12.1, GOLD)
txt(s, "Scope: native Jira benchmark-specific work; other tasks are transfers. No full FLOWSEAL / OCELOT / OrchDebate reproduction.",
    .55, 6.99, 12.23, .17, 9.2, DIM)

# 03 — chronology and independent evidence gates.
s = base(3, "Execution", "How the evidence became auditable",
         "The program was iterative. Every redesigned study was frozen before its own calls; earlier nulls stayed intact.")
timeline = [
    ("Native", "baseline"),
    ("Runtime", "audit"),
    ("Corrected", "Jira 2 × 2"),
    ("Four-domain", "transfers"),
    ("Metadata", "4 / 4 nulls"),
    ("Source / score", "audit"),
    ("Fresh hostmask", "new freeze"),
]
for i, (a,b) in enumerate(timeline):
    x=.55+i*1.76
    box(s, x, 2.04, 1.60, .87, PANEL2 if i == 6 else PANEL)
    txt(s, a+"\n"+b, x+.10, 2.21, 1.40, .49, 12.4, TEAL if i == 6 else WHITE, i == 6, PP_ALIGN.CENTER)
    if i < 6:
        txt(s, "›", x+1.62, 2.32, .13, .29, 19, DIM, True)
guardrails = [
    ("IDENTIFICATION", "Same public world; source reused across guards.\nBalanced secret bits and masks.\nCrossed source delivery checks actual use."),
    ("INFERENCE", "World / seed is the unit.\nExact paired tests; Holm within families.\n20,000 world-bootstrap resamples.\nNulls and invalid actions retained."),
    ("REPRODUCIBILITY", "Frozen source and exact requests.\nIndependent saved-action reconstruction.\n44 + 15 software tests; offline replication.\nNo outcome-based response retries."),
]
for i,(title,body) in enumerate(guardrails):
    x=.55+i*4.13
    box(s,x,3.35,3.96,2.32)
    txt(s,title,x+.23,3.57,3.49,.28,13.3,TEAL,True)
    txt(s,body,x+.23,4.04,3.49,1.40,14.0,WHITE)
box(s,.55,6.00,12.23,.52,PANEL2)
txt(s,"Latest two studies: 2,326 research calls + 6 compatibility requests  |  GPT-4.1 mini / GPT-4.1  |  T = 0.7  |  max 1,500 tokens",
    .73,6.16,11.87,.22,11.6,WHITE)
txt(s,"Limits: supplied decoder; neutral bit-copying source; simple copy task; related models; finite observer.",
    .55,6.70,12.23,.22,12.0,GOLD)
txt(s,"Separate freezes do not provide a global multiplicity guarantee across the whole iterative program. Hashes support reproducibility, not external attestation.",
    .55,6.99,12.23,.15,8.9,DIM)

# 04 — results in their own units, with regenerated scientific plots.
s = base(4, "Results", "Three effects passed; the null results stayed in the record",
         "Registered comparisons use their own units and test families. Intervals below are descriptive 95% world/seed bootstraps.")
table_cols = [(.55,2.30),(2.85,.58),(3.43,2.56),(5.99,1.93)]
for (x,w), label in zip(table_cols,["CONTRAST / UNIT","N","EFFECT [95%]","TEST / VERDICT"]):
    txt(s,label,x+.10,1.99,w-.15,.18,9.8,TEAL,True)
r1=jira["primary_family"]["R1"]; r2=jira["primary_family"]["R2"]
resource=domains["primary_family"]["resource_allocation"]
hp=host["primary"]
table_rows=[
    ("Hide Jira history\nRegret (posts denied)","20",f"+{r1['mean']:.3f}\n[{r1['bootstrap95'][0]:.3f}, {r1['bootstrap95'][1]:.3f}]","Holm .03125\nSUPPORTED",True),
    ("Resource contract\nHarm benefit","10",f"+{resource['mean']:.3f}\n[{resource['bootstrap95'][0]:.3f}, {resource['bootstrap95'][1]:.3f}]","Holm .007813\nSUPPORTED",True),
    ("Host-masked joint fields\nSigned decoding ΔS","16",f"+{hp['mean']:.5f}\n[{hp['bootstrap95'][0]:.5f}, {hp['bootstrap95'][1]:.5f}]","Exact .000061\nSUPPORTED",True),
    ("Deny private posts\nRegret (history retained)","20",f"{r2['mean']:+.3f}\n[{r2['bootstrap95'][0]:.3f}, {r2['bootstrap95'][1]:.3f}]","Holm 1.0\nUNSUPPORTED",False),
    ("Original metadata family\nFour carriers","32\neach","0 / 4 supported\nWhole-action endpoint","Holm ≥ .125\nRETAINED NULLS",False),
    ("Other domain guards\nProcure / review / artifact","10\neach","3 / 3 unsupported\nRegistered harm benefit","Holm 1 / .5 / .375\nRETAINED NULLS",False),
]
for i,row in enumerate(table_rows):
    y=2.35+i*.63
    box(s,.55,y,7.37,.57,PANEL if i%2==0 else PANEL2)
    for j,val in enumerate(row[:4]):
        x,w=table_cols[j]
        color=TEAL if j==3 and row[4] else (MUTED if j==3 else WHITE)
        txt(s,val,x+.10,y+.095,w-.16,.42,11.5 if j in (0,3) else 12.1,color,j==3)
txt(s,"Follow-up: mini decoding by guard",8.40,1.97,4.36,.25,14.2,WHITE,True)
s.shapes.add_picture(str(ASSETS/"signed_decoding.png"),Inches(8.35),Inches(2.28),width=Inches(4.42),height=Inches(2.08))
txt(s,"Primary: marginal − full. S = .5 perfect; S = 0 constant / abstain.",
    8.40,4.40,4.34,.35,10.3,MUTED)
txt(s,"Crossed delivery: payoff follows the signal",8.40,4.87,4.36,.25,13.5,WHITE,True)
s.shapes.add_picture(str(ASSETS/"crossed_payoff.png"),Inches(8.35),Inches(5.15),width=Inches(4.42),height=Inches(1.43))
txt(s,"32 matched cases; exploratory; evaluator target held fixed.",8.40,6.65,4.34,.28,9.7,MUTED)
box(s,.55,6.31,7.37,.48,PANEL2)
txt(s,"320 / 320 public-copy tasks correct. Preservation is limited to that simple task.",
    .72,6.47,7.02,.19,11.0,TEAL,True)
txt(s,"Resource: +760 avoided penalties −179.825 raw value. Mini marginal net +22; mean-payoff CI [−.03125, .6875] crosses zero.",
    .55,6.99,12.23,.15,8.7,DIM)

# 05 — four distinct implications and the boundary of the claimed contribution.
s = base(5, "Insights", "What this contributes to research and real workflows",
         "A reproducible causal audit linking coordination opportunity, accepted harm and the utility cost of intervention.")
insights=[
    ("CONTEXT", "Audit retained plans as well as future access.",
     "Hiding history reduced Jira regret. Posting denial showed no supported benefit.",
     "Applies to shared boards and delegated workplace agents."),
    ("DISCLOSURE", "Audit the complete allowed receiver view.",
     "Joint metadata guided inference; full registered-transcript mediation removed observed use.",
     "Relevant to receipts, status labels and tool-chain outputs."),
    ("EXECUTION", "Separate contract enforcement from task welfare.",
     "Resource gains were largely avoided penalties. Review quorum reduced legitimate work.",
     "Relevant to budgets, approvals and allocation workflows."),
    ("MEASUREMENT", "Separate encoding, inference and action.",
     "Most initial XOR banks failed; checksum gating erased 98 numeric predictions.",
     "Relevant to security evaluations and monitor evidence."),
]
for i,(tag,head,body,application) in enumerate(insights):
    x=.55+i*3.10
    box(s,x,2.04,2.93,3.03)
    txt(s,tag,x+.18,2.24,2.57,.22,10.8,TEAL,True)
    txt(s,head,x+.18,2.70,2.57,.75,17.4,WHITE,True)
    txt(s,body,x+.18,3.64,2.57,.76,13.3,WHITE)
    txt(s,application,x+.18,4.63,2.57,.32,10.0,MUTED)
labels=["Channel","Encoding","Inference","Accepted action","Coalition payoff","Task utility"]
for i,label in enumerate(labels):
    x=.55+i*2.08
    box(s,x,5.42,1.91,.53,PANEL2)
    txt(s,label,x+.05,5.59,1.81,.19,11.5,WHITE,True,PP_ALIGN.CENTER)
    if i<5:txt(s,"›",x+1.94,5.57,.13,.24,17,DIM,True)
box(s,.55,6.22,12.23,.52,PANEL2)
txt(s,"Next decisive test: native TEXT → ACTION-only → same actions hidden, with coalition advantage and real task utility.",
    .73,6.37,11.87,.22,12.0,GOLD,True)
txt(s,"Not yet demonstrated: spontaneous collusion, reliably positive mean profit, broad workflow preservation, or a break of original defense implementations.",
    .55,6.99,12.23,.15,8.8,DIM)

notes_path = HERE / "SPEAKER_NOTES.md"
notes = notes_path.read_text() if notes_path.exists() else ""
chunks = re.split(r"(?m)^## Slide [1-5][^\n]*\n", notes)
if len(chunks) == 6:
    for slide, note in zip(prs.slides, chunks[1:]):
        slide.notes_slide.notes_text_frame.text = note.strip()
else:
    for i, slide in enumerate(prs.slides, 1):
        slide.notes_slide.notes_text_frame.text = f"Slide {i}. Detailed narrative and source qualifications are in SPEAKER_NOTES.md and CLAIM_REGISTER.md."

output=HERE/"research_story_5_slides.pptx"
prs.save(output)
assert len(Presentation(output).slides)==5
manifest = {
    "slides":5,"output":output.name,"paid_model_calls":0,
    "graphs_regenerated_from_frozen_results":True,
    "frozen_study_files_changed":False,
    "speaker_notes_embedded":len(chunks)==6,
    "source_files":{str((STUDIES/r).relative_to(REPO)):hashlib.sha256((STUDIES/r).read_bytes()).hexdigest()
                    for r in selected_sources.values()},
    "retained_project_sources":retained_project_sources,
    "facts":facts,
}
(HERE/"BUILD_MANIFEST.json").write_text(json.dumps(manifest,indent=2)+"\n")
print(json.dumps({"pptx":str(output),"slides":5,"speaker_notes_embedded":manifest["speaker_notes_embedded"]}))
