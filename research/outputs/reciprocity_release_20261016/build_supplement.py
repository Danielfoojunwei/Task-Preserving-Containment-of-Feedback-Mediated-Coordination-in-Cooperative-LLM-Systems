#!/usr/bin/env python3
"""Offline supplemental figures from a released 8-block analysis JSON.

No API calls, raw-record reads, runner imports, or frozen-file mutations.
"""
import argparse
import importlib.util
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("reciprocity_release_helpers", HERE / "build_release.py")
base = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(base)
ARMS = ("plain", "directed", "directed_no_notes")
CONTRASTS = ("directed - plain", "directed - directed_no_notes")
NAMES = ("Plain", "Directed", "Directed,\nno peer notes")
COLORS = ("#786D9B", "#174A66", "#8D5E3C")


def require_complete(report):
    if (report.get("inference_eligible") is not True or report.get("incomplete")
            or report.get("planned_sessions") != 24 or report.get("completed_sessions") != 24
            or report.get("planned_logical_calls") != 864 or report.get("completed_logical_calls") != 864
            or report.get("saved_logical_calls") != 864):
        raise ValueError("Supplemental figures withheld: all 24 sessions and 864 calls must be complete")
    primary = report.get("primary", {})
    if primary.get("primary_complete") is not True or primary.get("worlds") != 8 or primary.get("holm_family_size") != 2:
        raise ValueError("Expected two contrasts across eight matched blocks")
    rows = primary.get("contrasts", [])
    if [r.get("contrast") for r in rows] != list(CONTRASTS):
        raise ValueError("Unexpected frozen supplemental contrast definitions")
    for row in rows:
        if row.get("worlds") != 8 or row.get("assignments") != 256 or len(row.get("differences", [])) != 8:
            raise ValueError("Supplemental inference must use all eight blocks")
        interval = row.get("bootstrap_95", {})
        if interval.get("replicates") != 20000 or base.number(interval["lower"]) > base.number(interval["upper"]):
            raise ValueError("Unexpected supplemental bootstrap interval")
        for key in ("p", "holm_p"):
            if not 0 <= base.number(row[key]) <= 1:
                raise ValueError("Invalid supplemental p-value")
        base.number(row["mean_difference"])
    sessions = report.get("sessions", [])
    if len(sessions) != 24 or len({r["session_id"] for r in sessions}) != 24:
        raise ValueError("Supplement requires 24 unique session records")
    blocks = {}
    for session in sessions:
        if len(session.get("rounds", [])) != 4:
            raise ValueError("Four recorded rounds required per supplemental session")
        blocks.setdefault(session["block_id"], []).append(session["condition"])
    if set(blocks) != set(range(9301, 9309)) or any(sorted(arms) != sorted(ARMS) for arms in blocks.values()):
        raise ValueError("Expected exactly three arms in each block 9301–9308")
    for arm in ARMS:
        row = report["summary"][arm]
        if row["sessions"] != 8 or row["rounds"] != 32:
            raise ValueError("Unexpected supplemental descriptive denominator")
    joint = report.get("joint_holm5")
    if joint is not None:
        expected = [("parent", "full - no_notes"), ("parent", "full - no_feedback"),
                    ("parent", "full - no_clarification"), ("supplement", CONTRASTS[0]),
                    ("supplement", CONTRASTS[1])]
        if joint.get("family_size") != 5 or [(r.get("study"), r.get("contrast")) for r in joint.get("contrasts", [])] != expected:
            raise ValueError("Unexpected joint five-contrast family")
        for row in joint["contrasts"]:
            for key in ("raw_p", "holm5_p"):
                if not 0 <= base.number(row[key]) <= 1:
                    raise ValueError("Invalid joint-family p-value")
        for original, combined in zip(rows, joint["contrasts"][3:]):
            if abs(base.number(original["p"]) - base.number(combined["raw_p"])) > 1e-14:
                raise ValueError("Supplemental raw p differs in the joint report")
    return report


def joint_lookup(report):
    return {row["contrast"]:base.number(row["holm5_p"]) for row in report.get("joint_holm5", {}).get("contrasts", [])}


def forest(report, output, plt):
    rows = report["primary"]["contrasts"]
    joint = joint_lookup(report)
    fig = plt.figure(figsize=(15.8, 4.8))
    grid = fig.add_gridspec(1, 2, width_ratios=(1.0, 1.55), wspace=.06)
    ax = fig.add_subplot(grid[0, 0]); table = fig.add_subplot(grid[0, 1]); table.axis("off")
    values = [0.0]
    for index, row in enumerate(rows):
        y = 1-index
        mean = base.number(row["mean_difference"])
        low, high = (base.number(row["bootstrap_95"][k]) for k in ("lower", "upper"))
        values += [mean,low,high]
        ax.hlines(y, low, high, color=COLORS[1], linewidth=3)
        ax.scatter([mean], [y], color=COLORS[1], s=62, zorder=3)
    margin = max(.02, (max(values)-min(values))*.12)
    ax.set_xlim(min(values)-margin, max(values)+margin)
    ax.set_ylim(-.5, 1.65)
    ax.set_yticks([1,0], ["Directed − plain\n(instruction bundle)", "Directed − directed, no peer notes\n(note delivery within directed prompt)"])
    ax.tick_params(axis="y", length=0, pad=10, labelsize=9)
    ax.axvline(0, color="#8A9298", linewidth=1, linestyle="--")
    ax.grid(axis="x", color="#E9EDF0")
    ax.set_xlabel("Change in normalized bilateral net gain")
    positions = (.01, .19, .49, .68, .86)
    for x, label in zip(positions, ("Mean Δ", "Descriptive 95% CI", "Raw exact p", "Holm (2) p", "Joint Holm (5) p")):
        table.text(x,.92,label,transform=table.transAxes,fontweight="bold",fontsize=9)
    for index,row in enumerate(rows):
        interval=row["bootstrap_95"]
        values=(base.fnum(row["mean_difference"]),f"[{base.fnum(interval['lower'])}, {base.fnum(interval['upper'])}]",
                base.fnum(row["p"],6),base.fnum(row["holm_p"],6),
                base.fnum(joint[row["contrast"]],6) if row["contrast"] in joint else "Not supplied")
        y=(1-index+.5)/2.15
        for x,value in zip(positions,values):table.text(x,y,value,transform=table.transAxes,fontsize=9.5)
    fig.suptitle("Fresh negotiation-scaffolding supplement", fontsize=16, fontweight="bold", y=1.02)
    fig.text(.5,.94,"8 randomized matched blocks · mean rounds 2–4 · two predeclared contrasts",ha="center",fontsize=10)
    fig.text(.5,-.08,"Intervals: 20,000 paired-block bootstrap draws, descriptive 95%. Tests: all 256 swaps; two-sided; Holm family = 2.\nOptional joint Holm (5) is separate accounting and leaves the parent Holm (3) report unchanged.\nDirected wording assigns a negotiation instruction bundle; neither contrast establishes a single wording ingredient or an interaction.",ha="center",va="top",fontsize=9,color="#4D5962")
    base.save_figure(fig,output,"supplement_primary_effects",plt)


def descriptive(report,output,plt):
    rows=[report["summary"][arm] for arm in ARMS]
    fig,axes=plt.subplots(2,3,figsize=(14.6,8.5));x=list(range(3))
    for ax in axes.flat:ax.set_xticks(x,NAMES,fontsize=9)
    axes[0,0].bar(x,[base.number(r["mean_primary"]) for r in rows],color=COLORS)
    base.tidy_axis(axes[0,0],"A. Bilateral net-gain endpoint","Mean R2–R4 metric",True)
    axes[0,1].bar([i-.17 for i in x],[r["gross_owner_excess"] for r in rows],width=.34,color="#91AAB8",label="Gross excess")
    axes[0,1].bar([i+.17 for i in x],[r["net_owner_loss"] for r in rows],width=.34,color=COLORS[1],label="Net owner loss")
    base.tidy_axis(axes[0,1],"B. Owner losses","Total payment units, all rounds");axes[0,1].margins(y=.20);axes[0,1].legend(frameon=False,fontsize=8)
    axes[0,2].bar(x,[base.ratio(r["both_positive_rounds"],r["rounds"]) for r in rows],color=COLORS)
    base.tidy_axis(axes[0,2],"C. Both agents' net scores > 0","Share of 32 rounds per arm",True)
    for actor,offset,color in (("A",-.17,COLORS[1]),("B",.17,"#91AAB8")):
        axes[1,0].bar([i+offset for i in x],[r["mean_coverage"][actor] for r in rows],width=.34,color=color,label="Actor "+actor)
    base.tidy_axis(axes[1,0],"D. Receipt-backed coverage","Mean min(payment, receipt)/receipt",True);axes[1,0].legend(frameon=False,fontsize=8)
    axes[1,1].bar(x,[base.ratio(r["sorting_correct"],r["sorting_total"]) for r in rows],color=COLORS)
    base.tidy_axis(axes[1,1],"E. Public sorting accuracy","Correct / 128 recorded actions per arm",True)
    totals={arm:{a:sum(base.number(s["total_scores"][a]) for s in report["sessions"] if s["condition"]==arm) for a in "AB"} for arm in ARMS}
    for actor,offset,color in (("A",-.17,COLORS[1]),("B",.17,"#91AAB8")):
        axes[1,2].bar([i+offset for i in x],[totals[arm][actor] for arm in ARMS],width=.34,color=color,label="Actor "+actor)
    axes[1,2].axhline(0,color="#8A9298",linewidth=.8);base.tidy_axis(axes[1,2],"F. Actual net scores","Total score, all rounds");axes[1,2].margins(y=.20);axes[1,2].legend(frameon=False,fontsize=8)
    fig.suptitle("Supplemental outcomes and legitimate task performance",fontsize=16,fontweight="bold",y=1.01)
    fig.tight_layout(h_pad=3,w_pad=2)
    fig.text(.5,-.035,"Descriptive summaries only. Each arm: 8 fresh sessions × 4 rounds. These observations are not pooled with the parent study.\nAssigned individual score and simulator permission are engineered. Action gain does not itself establish agreement or covert intent.",ha="center",fontsize=9,color="#4D5962")
    base.save_figure(fig,output,"supplement_descriptive",plt)


def tables(report,output,plt):
    joint=joint_lookup(report);primary=[]
    for row in report["primary"]["contrasts"]:
        primary.append({"contrast":row["contrast"],"matched_blocks":8,"mean_difference":base.number(row["mean_difference"]),
                        "descriptive_ci_lower":base.number(row["bootstrap_95"]["lower"]),"descriptive_ci_upper":base.number(row["bootstrap_95"]["upper"]),
                        "raw_exact_p":base.number(row["p"]),"holm_2_p":base.number(row["holm_p"]),"joint_holm_5_p":joint.get(row["contrast"],"")})
    base.write_csv(output/"supplement_primary.csv",list(primary[0]),primary)
    descriptions=[]
    for arm in ARMS:
        row=report["summary"][arm]
        descriptions.append({"condition":arm,"sessions":row["sessions"],"rounds":row["rounds"],"mean_primary_R2_R4":row["mean_primary"],
                             "gross_owner_excess":row["gross_owner_excess"],"net_owner_loss":row["net_owner_loss"],"both_positive_rounds":row["both_positive_rounds"],
                             "coverage_A":row["mean_coverage"]["A"],"coverage_B":row["mean_coverage"]["B"],"sorting_correct":row["sorting_correct"],"sorting_total":row["sorting_total"],
                             "money_valid":row["money_valid"],"money_total":row["money_total"]})
    base.write_csv(output/"supplement_descriptive.csv",list(descriptions[0]),descriptions)
    lines=["# Released supplemental tables","","Fresh 8-block randomized negotiation-scaffolding supplement. Action gain and manually evidenced agreement are separate outcomes.","","## Supplemental primary family","","| Contrast | Blocks | Mean Δ | Descriptive 95% CI | Raw exact p | Holm (2) p | Joint Holm (5) p |","|---|---:|---:|---|---:|---:|---:|"]
    for row in primary:
        j="Not supplied" if row["joint_holm_5_p"]=="" else f"{row['joint_holm_5_p']:.8f}"
        lines.append(f"| {row['contrast']} | 8 | {row['mean_difference']:.6f} | [{row['descriptive_ci_lower']:.6f}, {row['descriptive_ci_upper']:.6f}] | {row['raw_exact_p']:.8f} | {row['holm_2_p']:.8f} | {j} |")
    lines += ["","The 20,000-bootstrap intervals are descriptive and not multiplicity-adjusted. Exact tests enumerate all 256 swaps. The inference unit is the randomized matched block, not a round, action or judge call.","","## Arm descriptions","","| Arm | Sessions / rounds | Primary mean | Gross / net owner loss | Both-positive rounds | Coverage A / B | Correct sorting |","|---|---|---:|---:|---|---|---|"]
    for row in descriptions:
        lines.append(f"| {row['condition']} | {row['sessions']} / {row['rounds']} | {row['mean_primary_R2_R4']:.6f} | {row['gross_owner_excess']} / {row['net_owner_loss']:.2f} | {row['both_positive_rounds']}/{row['rounds']} | {row['coverage_A']:.4f} / {row['coverage_B']:.4f} | {row['sorting_correct']}/{row['sorting_total']} |")
    stems=[]
    lines += ["","## Separate joint five-contrast accounting",""]
    if report.get("joint_holm5"):
        combined=[]
        lines += ["| Study | Contrast | Matched blocks | Raw exact p | Joint Holm (5) p |","|---|---|---:|---:|---:|"]
        for row in report["joint_holm5"]["contrasts"]:
            item={"study":row["study"],"contrast":row["contrast"],"matched_blocks":16 if row["study"]=="parent" else 8,"raw_exact_p":base.number(row["raw_p"]),"joint_holm_5_p":base.number(row["holm5_p"])}
            combined.append(item)
            lines.append(f"| {item['study']} | {item['contrast']} | {item['matched_blocks']} | {item['raw_exact_p']:.8f} | {item['joint_holm_5_p']:.8f} |")
        base.write_csv(output/"joint_holm5.csv",list(combined[0]),combined)
        fig,ax=plt.subplots(figsize=(13,3.4));ax.axis("off")
        cell=[[r["study"],r["contrast"],str(r["matched_blocks"]),f"{r['raw_exact_p']:.8f}",f"{r['joint_holm_5_p']:.8f}"] for r in combined]
        table=ax.table(cellText=cell,colLabels=["Study","Contrast","Matched blocks","Raw exact p","Joint Holm (5) p"],loc="center",cellLoc="left",colLoc="left",colWidths=[.13,.39,.14,.16,.18])
        table.auto_set_font_size(False);table.set_fontsize(10);table.scale(1,1.7)
        for (row,col),cell in table.get_celld().items():
            cell.set_edgecolor("#E1E8ED")
            if row==0:cell.set_facecolor("#E9F1F5");cell.set_text_props(fontweight="bold")
        fig.suptitle("Joint multiplicity accounting for five specified contrasts",fontsize=15,fontweight="bold",y=1.03)
        fig.text(.5,-.025,"Separate accounting only: original parent Holm (3) and supplemental Holm (2) reports are unchanged.\nObservations are not pooled. This is not a correction for all historical exploratory choices.",ha="center",fontsize=9,color="#4D5962")
        base.save_figure(fig,output,"joint_holm5",plt);stems.append("joint_holm5")
    else:lines += ["A joint Holm (5) report was not supplied. The builder does not invent or recalculate missing adjusted p-values."]
    lines += ["","The directed-minus-plain contrast assigns a negotiation instruction bundle. Directed-minus-directed/no-notes tests delivery conditional on that bundle. The design does not estimate a delivery-by-wording interaction or a single linguistic ingredient. Existing context and numeric actions remain possible coordination carriers.","","The supplement does not relabel the parent study or old null outcomes. It does not establish spontaneous collusion in a benign deployment. The receipt-gate claim remains bounded to the trusted payment path; observed harm alone is not proof of an agreement.",""]
    (output/"SUPPLEMENT_TABLES.md").write_text("\n".join(lines))
    return stems


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--analysis",type=Path,default=HERE.parent/"negotiation_causal_20261016"/"ANALYSIS.json")
    parser.add_argument("--output",type=Path,default=HERE)
    args=parser.parse_args(argv);study=args.analysis.resolve().parent;output=args.output.resolve()
    if output==study or study in output.parents:parser.error("Output must be outside the frozen supplemental study")
    report=require_complete(base.load(args.analysis));plt=base.configure_plotting();output.mkdir(parents=True,exist_ok=True)
    forest(report,output,plt);descriptive(report,output,plt);extra_stems=tables(report,output,plt)
    names=[stem+"."+ext for stem in ("supplement_primary_effects","supplement_descriptive",*extra_stems) for ext in ("png","svg")]
    names += ["supplement_primary.csv","supplement_descriptive.csv","SUPPLEMENT_TABLES.md"]
    if report.get("joint_holm5"):names.append("joint_holm5.csv")
    sources=[Path(__file__).resolve(),HERE/"build_release.py",args.analysis.resolve()]
    sources += [study/name for name in ("analyze.py","ANALYSIS_PLAN.md","PROTOCOL.md","test_analysis.py") if (study/name).exists()]
    import matplotlib
    manifest={"builder":"offline supplemental presentation, no raw calls or API access","primary_unit":"8 randomized matched blocks","matplotlib_version":matplotlib.__version__,
              "supplement_complete":True,"joint_holm5_supplied":bool(report.get("joint_holm5")),
              "sources":[{"path":str(p),"sha256":base.sha256(p)} for p in sources],
              "outputs":[{"path":name,"sha256":base.sha256(output/name)} for name in sorted(names)],
              "scope":"Separate fresh negotiation instruction-bundle and conditional-delivery contrasts, not spontaneous benign collusion or a wording-by-delivery interaction."}
    (output/"SUPPLEMENT_BUILD_MANIFEST.json").write_text(json.dumps(manifest,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"output":str(output),"artifacts":len(names),"matched_blocks":8,"joint_holm5_supplied":bool(report.get("joint_holm5"))},sort_keys=True))


if __name__=="__main__":main()
