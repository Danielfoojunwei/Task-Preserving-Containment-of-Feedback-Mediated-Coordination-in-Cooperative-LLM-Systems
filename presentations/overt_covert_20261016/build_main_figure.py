#!/usr/bin/env python3
"""Build a main-only figure after explicit numerical release; no API calls."""
import argparse
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build(analysis_path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    analysis_path = Path(analysis_path).resolve()
    data = json.loads(analysis_path.read_bytes())
    if not data.get("inference_eligible") or not data["primary"]["primary_complete"]:
        raise ValueError("Complete released main analysis required")
    conditions = ["notes_on__audit_public__fine_12", "notes_off__audit_public__fine_12"]
    metric, loss = [], []
    for c in conditions:
        worlds = [s for s in data["sessions"] if s["phase"] == "validation" and s["condition"] == c]
        if len(worlds) != 20:
            raise ValueError("Both arms must contain twenty worlds")
        metric.append(sum(s["primary_exact"]["value"] for s in worlds) / 20)
        loss.append(data["summary"][c]["net_owner_loss"])
    contrast = data["primary"]["contrasts"][3]
    if abs((metric[0] - metric[1]) - contrast["mean_difference"]["value"]) > 1e-12:
        raise ValueError("Figure differs from the primary matched contrast")
    plt.rcParams.update({"font.family":"DejaVu Sans", "font.size":13})
    fig, axes = plt.subplots(1, 2, figsize=(12.3, 3.0), layout="constrained")
    labels = ["Peer text delivered", "Peer text withheld"]
    for ax, values, title, ylabel in zip(axes, (metric, loss),
            ("Retained mutual benefit", "Owner loss"),
            ("Mean normalized M, rounds 2–4", "Total net units, all four rounds")):
        bars = ax.bar(labels, values, color=["#008575", "#ba6344"], width=.5)
        ax.set_title(title, loc="left", weight="bold")
        ax.set_ylabel(ylabel)
        ax.set_ylim(0, max(values) * 1.3)
        ax.spines[["top", "right"]].set_visible(False)
        ax.bar_label(bars, labels=[f"{v:.3f}" if max(values) < 1 else f"{v:g}" for v in values], padding=5)
    axes[0].text(.02, .94, "Primary Holm4 p = 0.015625", transform=axes[0].transAxes, va="top", fontsize=11)
    axes[1].text(.02, .94, "Descriptive payment totals", transform=axes[1].transAxes, va="top", fontsize=11)
    files = [HERE / "main_note_delivery.png", HERE / "main_note_delivery.svg"]
    for p in files:
        fig.savefig(p, dpi=180, facecolor="white")
    plt.close(fig)
    manifest = {"scope":"Released main only; public-report audit and fine 12. No continuation or secondary execution results.",
                "analysis_sha256":sha(analysis_path), "sealed_review_sha256":data["review_release"]["sha256"],
                "builder_sha256":sha(Path(__file__)), "worlds_per_arm":20,
                "metric_rounds":[2,3,4], "owner_loss_rounds":[1,2,3,4],
                "mean_M":dict(zip(conditions, metric)), "net_owner_loss":dict(zip(conditions, loss)),
                "output_sha256":{p.name:sha(p) for p in files}, "api_calls":0}
    (HERE / "MAIN_FIGURE_MANIFEST.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--analysis", type=Path, default=HERE.parents[1] / "research/outputs/overt_covert_relaunch_20261016/ANALYSIS.json")
    parser.add_argument("--release", action="store_true")
    args = parser.parse_args()
    if not args.release:
        parser.error("Explicit numerical release is required before opening main analysis")
    print(json.dumps(build(args.analysis), indent=2, sort_keys=True))
