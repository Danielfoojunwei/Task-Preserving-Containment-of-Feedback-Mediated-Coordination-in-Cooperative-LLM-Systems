#!/usr/bin/env python3
"""Build a self-contained five-slide evidence view from released analysis only."""
import base64
import hashlib
import html
import json
import os
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", "/tmp/reciprocity-presentation-matplotlib")
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PARENT = ROOT / "research/outputs/reciprocity_causal_20261016/ANALYSIS_VALIDATION.json"
SUPPLEMENT = ROOT / "research/outputs/negotiation_causal_20261016/ANALYSIS.json"
DEFENSE = ROOT / "research/outputs/negotiation_defense_20261016/ANALYSIS.json"
REVIEWS = ROOT / "research/outputs/reciprocity_release_20261016/SUPPLEMENT_AGREEMENT_REVIEW.json"


def load(path):
    return json.loads(path.read_text())


def image(path):
    return "data:image/png;base64," + base64.b64encode(path.read_bytes()).decode()


def table(headers, rows):
    return "<table><thead><tr>" + "".join("<th>" + html.escape(str(x)) + "</th>" for x in headers) + "</tr></thead><tbody>" + "".join("<tr>" + "".join("<td>" + html.escape(str(x)) + "</td>" for x in row) + "</tr>" for row in rows) + "</tbody></table>"


def main():
    parent, supplement, defense, reviews = map(load, (PARENT, SUPPLEMENT, DEFENSE, REVIEWS))
    if not parent["primary"]["primary_complete"] or not supplement["primary"]["primary_complete"] or not defense["complete"]:
        raise ValueError("Only complete released evidence may be presented")
    if any(row["reject_at_05"] for row in supplement["joint_holm5"]["contrasts"]):
        raise ValueError("Narrative requires review if primary rejection status changes")
    if reviews["confirmed_overt_agent_originated_pacts"] != 7 or reviews["strict_covert_confirmed"] != 0:
        raise ValueError("Agreement narrative requires review")
    labels = ["Unchanged", "Future notes cut", "Receipt gate"]
    arms = ["unchanged", "no_future_notes", "live_receipt_gate_disclosed"]
    groups = [defense["groups"][key] for key in arms]
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10,
                         "svg.hashsalt": "reciprocity-presentation-20261016"})
    fig, axes = plt.subplots(1, 2, figsize=(10.8, 3.3), layout="constrained")
    colors = ["#6c7890", "#d58a44", "#228d7c"]
    values = [group["net_owner_loss"] for group in groups]
    axes[0].bar(labels, values, color=colors, width=.58)
    axes[0].set(ylabel="Net owner loss (synthetic units)", ylim=(0, 140), title="Loss survives the future-note cutoff")
    for index, value in enumerate(values):
        axes[0].text(index, value + 4, f"{value:g}", ha="center", weight="bold")
    claim_rates = [100 * group["attempted_unsupported_claims"] / 32 for group in groups]
    approval_rates = [100 * group["attempted_unsupported_approvals"] / 32 for group in groups]
    x = list(range(3))
    axes[1].bar([i - .16 for i in x], claim_rates, width=.3, color="#5273ac", label="Unsupported claims")
    axes[1].bar([i + .16 for i in x], approval_rates, width=.3, color="#a65d70", label="Unsupported approvals")
    axes[1].set(xticks=x, xticklabels=labels, ylim=(0, 120), ylabel="Percent of 32 actor actions", title="Payment containment does not end attempts")
    axes[1].legend(frameon=False, loc="upper center", ncol=1, fontsize=8)
    for ax in axes:
        ax.spines[["top", "right"]].set_visible(False)
        ax.grid(axis="y", alpha=.18)
        ax.set_axisbelow(True)
    fig.savefig(HERE / "defense_outcomes.png", dpi=180)
    fig.savefig(HERE / "defense_outcomes.svg")
    plt.close(fig)
    svg = HERE / "defense_outcomes.svg"
    svg.write_text("\n".join(line.rstrip() for line in svg.read_text().splitlines()) + "\n")

    contrasts = parent["primary"]["contrasts"] + supplement["primary"]["contrasts"]
    joint = supplement["joint_holm5"]["contrasts"]
    effect_rows = [[row["contrast"].replace("_", " "), f"{row['mean_difference']['value']:+.3f}",
                    f"{row['p']['value']:.5g}", f"{row['holm_p']['value']:.5g}", f"{joint[index]['holm5_p']['value']:.5g}"]
                   for index, row in enumerate(contrasts)]
    finance_rows = []
    for arm in ("plain", "directed", "directed_no_notes"):
        row = supplement["summary"][arm]
        finance_rows.append([arm.replace("_", " "), "7/8" if arm == "directed" else "0/8",
                             f"{row['both_positive_rounds']}/32", f"{row['net_owner_loss']:.2f}"])
    defense_rows = [[labels[index], f"{row['gross_owner_excess']} / {row['net_owner_loss']:.2f}",
                     f"{row['both_positive_rounds']}/16", "100%", f"{row['attempted_unsupported_claims']}/32; {row['attempted_unsupported_approvals']}/32"]
                    for index, row in enumerate(groups)]
    slides = [
        ("The question", "When does individual reward-seeking become an agreement?", '''
<p class="lead">In eight matched source contexts, future-note cutoff left the same financial loss. Receipt enforcement removed the loss while unsupported attempts continued.</p>
<div class="flow"><span>Information carrier</span><b>→</b><span>Accepted agreement</span><b>→</b><span>Executable loss</span></div>
<div class="columns"><article><h3>What earlier evidence taught us</h3><p>Metadata can carry information, but the host supplied its decoder. A separate 300-call search found no resolved covert pact.</p></article><article><h3>What the new data establish</h3><p>Seven clear agent-originated reciprocal-favor pacts under a supplied negotiation process. All are overt; none establishes strict concealment.</p></article></div>
<p class="caution">All five primary causal contrasts remain unconfirmed after Holm correction. We extend controlled questions; we do not claim full reproduction or a break of the cited defense systems.</p>'''),
        ("The setup", "One economy; five precise treatment questions", '''
<div class="flow"><span>A claims · B reviews</span><b>⇄</b><span>B claims · A reviews</span><b>→</b><span>Peer-authorized payment</span></div>
<p>Receipt-backed organizational policy conflicts with each actor’s own numerical objective. Reviewers lose 25% of the excess they approve.</p>''' + table(["Question", "Assigned contrast"], [
            ["Peer notes", "Full vs no notes"], ["Verified reciprocity feedback", "Full vs no feedback"],
            ["Own-payoff clarification", "Full vs no clarification"], ["Negotiation process", "Directed vs plain"],
            ["Delivery under that process", "Directed vs directed/no-notes"]]) + '''
<p class="small">Within a contrast: same case values, payment physics, model, four-round horizon and turn budget. Directed prompts ask for proposals and explicit responses; they supply no fraud terms, codebook, joint reward or concealment plan. Numerical action channels remain.</p>'''),
        ("The empirical standard", "Agreement, enactment and containment require different evidence", '''
<div class="three"><article><h3>Agreement</h3><p>Literal proposal, actual delivery, other-agent acceptance and resolved prohibited reciprocal terms.</p></article><article><h3>Enactment</h3><p>Raw claims/reviews, both net scores and owner loss. Matching behavior alone is insufficient.</p></article><article><h3>Containment</h3><p>Same-history fresh continuations plus identical-proposal payment replay.</p></article></div>
<p><strong>Main:</strong> 16 matched blocks × 4 arms, plus separate controls. <strong>Supplement:</strong> 8 fresh blocks × 3 arms. Primary inference uses blocks, never calls or rounds.</p>
<p>Exact 65,536/256-swap tests; original Holm3/Holm2 and joint Holm5; descriptive 20,000-bootstrap intervals. All malformed, refusing and negative cases retained.</p>
<p class="lead">3,996 completed calls · US$15.7122648 reported cost · no transport failures.</p>
<p class="small">105 study checks plus 44 core tests pass (149 total), with independent raw-record audits. Each cohort frozen before its own calls; adaptation disclosed. Prefix review preceded current financial outcomes. Assistant reviews are not human ground truth: limited summary exposure and one main-world disagreement are retained. One model family, small samples and engineered objectives limit generalization.</p>'''),
        ("The results", "Clear overt pacts; none of five primary effects passes correction", 
         table(["Frozen contrast", "Mean Δ", "Raw p", "Original Holm", "Joint Holm5"], effect_rows) +
         table(["Supplement arm", "Confirmed pacts", "Both-positive rounds", "Net owner loss"], finance_rows) + '''
<blockquote>A: “Let’s both maximize our claims … regardless of the receipt amount.”<br>B: “I accept your proposal … regardless of receipt amount.”</blockquote>
<p class="small">Seven pacts have literal round-1 proposal/acceptance evidence; all are owner-visible, strict-covert confirmations zero. Notes-withheld harm is not proof of a tacit pact. Positive descriptive bootstrap intervals do not override adjusted exact tests.</p>'''),
        ("The unified finding", "Cutting future speech did not undo the financial outcome", 
         table(["Matched branch", "Gross / net loss", "Both-positive", "Receipt coverage", "Unsupported claims; approvals"], defense_rows) +
         f'<img class="defense" alt="Recorded owner loss and unsupported attempts across three defense branches" src="{image(HERE / "defense_outcomes.png")}">' + '''
<p><strong>Loss was identical in all eight paired worlds after future notes were cut.</strong> Every legitimate receipt was actually paid in all three branches. The disclosed gate still saw 28/32 unsupported claims and 22/32 unsupported approvals.</p>
<p class="small">Same-proposal gate: min(claim, approval, trusted receipt). Trusted ledger and complete payment mediation required. Existing history and numerical channels remain; disclosed enforcement changes knowledge too. This is a bounded continuation result, not universal prevention. Real-world analogy: expense, invoice or procurement workflows with conflicting local incentives.</p>''')
    ]
    sections = []
    for index, (kicker, title, body) in enumerate(slides, 1):
        sections.append(f'<section class="slide" data-slide="{index}" {"" if index == 1 else "hidden"}><div class="kicker">{index:02d} / 05 · {kicker}</div><h1>{title}</h1>{body}<footer>Released evidence · 16 October 2026 · detailed sources and limitations in SLIDES.md</footer></section>')
    page = '''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Reciprocal approvals: five-slide evidence breakdown</title><style>
*{box-sizing:border-box}body{margin:0;background:#111a2b;color:#172335;font:17px/1.4 system-ui,sans-serif}.slide{background:#fff;max-width:1280px;min-height:720px;margin:24px auto;padding:38px 48px 55px;position:relative;border-radius:8px}h1{font-size:35px;line-height:1.12;max-width:1050px;margin:8px 0 22px}h3{margin:0 0 8px;font-size:20px}.kicker{font-size:13px;letter-spacing:.1em;text-transform:uppercase;color:#296e77;font-weight:750}.lead{font-size:23px;font-weight:650;line-height:1.35}.flow{display:flex;align-items:center;gap:18px;margin:25px 0}.flow span{padding:16px;background:#e9f1f5;border-radius:6px;flex:1;text-align:center;font-weight:650}.columns,.three{display:grid;grid-template-columns:1fr 1fr;gap:24px}.three{grid-template-columns:1fr 1fr 1fr;margin:26px 0}.columns article,.three article{padding:20px;background:#f2f5f7;border-radius:6px}.small{font-size:14px;color:#4c5c6c}.caution{border-left:4px solid #c8853f;padding:10px 18px;background:#fff6e9}.defense{display:block;width:min(860px,100%);margin:12px auto 5px}table{border-collapse:collapse;width:100%;font-size:14px;margin:12px 0 18px}th{text-align:left;background:#e9f1f5}td,th{padding:8px 10px;border-bottom:1px solid #dbe3e8}blockquote{border-left:4px solid #298475;margin:14px 0;padding:8px 16px;font-size:16px;background:#eef7f4}footer{position:absolute;bottom:15px;left:48px;font-size:11px;color:#6a7785}.nav{position:fixed;right:18px;bottom:15px;display:flex;align-items:center;gap:10px;background:#152334;color:white;padding:8px;border-radius:8px;z-index:5}button{background:#eaf3f4;border:0;border-radius:5px;padding:8px 15px;color:#172335;cursor:pointer}.nav span{min-width:40px;text-align:center}@media(max-width:800px){.slide{margin:0;border-radius:0;padding:25px 22px 55px;min-height:100vh}h1{font-size:29px}.lead{font-size:20px}.columns,.three{grid-template-columns:1fr}.flow{gap:8px;font-size:13px}table{font-size:11px}td,th{padding:6px 4px}footer{left:22px}}@media print{@page{size:landscape;margin:0}body{background:white}.slide[hidden]{display:block!important}.slide{width:100%;height:100vh;max-width:none;min-height:0;margin:0;border-radius:0;break-after:page;font-size:13px;padding:28px 40px 42px}h1{font-size:28px;margin-bottom:12px}.lead{font-size:19px}.small{font-size:11px}table{font-size:11px;margin:8px 0}td,th{padding:5px 7px}.defense{width:650px}.nav{display:none}.flow{margin:15px 0}footer{left:40px}}
</style><main>''' + "".join(sections) + '''</main><nav class="nav" aria-label="Slide navigation"><button id="previous" aria-label="Previous slide">←</button><span id="counter">1 / 5</span><button id="next" aria-label="Next slide">→</button></nav><script>const slides=[...document.querySelectorAll('.slide')];let current=0;function show(n){current=Math.max(0,Math.min(slides.length-1,n));slides.forEach((s,i)=>s.hidden=i!==current);document.querySelector('#counter').textContent=(current+1)+' / 5';window.scrollTo(0,0)}document.querySelector('#next').onclick=()=>show(current+1);document.querySelector('#previous').onclick=()=>show(current-1);document.addEventListener('keydown',e=>{if(e.key==='ArrowRight'||e.key==='PageDown')show(current+1);if(e.key==='ArrowLeft'||e.key==='PageUp')show(current-1)});</script></html>'''
    (HERE / "index.html").write_text(page)
    # Render the same embedded local HTML without navigating a file:// origin.
    # No browser network requests or external resources are needed.
    from playwright.sync_api import sync_playwright
    (HERE / "preview").mkdir(exist_ok=True)
    with sync_playwright() as browser_tool:
        browser = browser_tool.chromium.launch(executable_path="/usr/bin/chromium", headless=True,
                                               args=["--no-sandbox"])
        page_view = browser.new_page(viewport={"width": 1280, "height": 900}, device_scale_factor=1)
        page_view.set_content(page, wait_until="load")
        for index in range(5):
            page_view.evaluate("show(" + str(index) + ")")
            page_view.screenshot(path=str(HERE / "preview" / f"slide_{index + 1}.png"), full_page=True)
        page_view.pdf(path=str(HERE / "reciprocity_5_slides.pdf"), format="A4", landscape=True,
                      print_background=True, prefer_css_page_size=True)
        browser.close()
    import fitz
    with fitz.open(HERE / "reciprocity_5_slides.pdf") as pdf:
        if len(pdf) != 5:
            raise ValueError("Presentation must render to exactly five PDF pages")
    sources = [PARENT, SUPPLEMENT, DEFENSE, REVIEWS, HERE / "SLIDES.md", Path(__file__)]
    outputs = [HERE / name for name in ("index.html", "defense_outcomes.png", "defense_outcomes.svg", "reciprocity_5_slides.pdf")]
    outputs.extend(sorted((HERE / "preview").glob("slide_*.png")))
    manifest = {"slides": 5, "source_sha256": {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest() for path in sources},
                "outputs_sha256": {str(path.relative_to(HERE)): hashlib.sha256(path.read_bytes()).hexdigest() for path in outputs},
                "scope": "released analyses only; no raw calls or new inference"}
    (HERE / "BUILD_MANIFEST.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"slides": len(slides), "html": str(HERE / "index.html")}, sort_keys=True))


if __name__ == "__main__":
    main()
