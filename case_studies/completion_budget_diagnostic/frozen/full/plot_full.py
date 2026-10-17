"""Render fixed-analysis figures from analyze_full.py outputs; no inference."""
import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter, PercentFormatter

HERE = Path(__file__).resolve().parent
CAPS = (128, 256, 512)
SEEDS = (201, 202, 203)
COLORS = {"robust": "#1764A0", "proxy": "#D96920", "Base": "#333940"}
STYLES = {201: "-", 202: "--", 203: ":"}
MARKERS = {201: "o", 202: "s", 203: "^"}


def read(path):
    return json.loads(path.read_text())


def save(fig, folder, name):
    for suffix in ("png", "svg"):
        fig.savefig(folder / f"{name}.{suffix}", dpi=180, facecolor="white", bbox_inches="tight")
    plt.close(fig)


def style_axis(ax):
    ax.spines[["top", "right"]].set_visible(False)
    ax.set_xticks([0, 1, 2], ["128", "256", "512"])
    ax.set_xlabel("Completion limit (new tokens)")
    ax.yaxis.set_major_formatter(PercentFormatter(1))
    ax.grid(axis="y", alpha=.18)
    ax.set_axisbelow(True)


def render(analysis, output):
    analysis = Path(analysis)
    output = Path(output)
    output.mkdir(exist_ok=False)
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10,
                         "axes.titlesize": 12, "axes.labelsize": 10, "svg.fonttype": "none"})
    cells = read(analysis / "cell_metrics.json")
    lookup = {(c["model"], c["cap"], c["policy"]): c for c in cells}
    models = ("Base", "robust_201", "proxy_201", "robust_202", "proxy_202", "robust_203", "proxy_203")
    fig, axes = plt.subplots(2, 2, figsize=(12.5, 8), sharex=True)
    panels = (("exact_correct", "Exact-answer accuracy"), ("mod10_correct", "Modulo-10 accuracy"),
              ("proxy_only_correct", "Modulo-correct, exact-incorrect"), ("accepted", "Accepted terminal answer"))
    for ax, (metric, title) in zip(axes.flat, panels):
        for model in models:
            rows = [lookup[model, cap, "terminal"] for cap in CAPS]
            if model == "Base":
                color, style, marker, label = COLORS[model], "-.", "D", "Untrained base"
            else:
                condition, raw_seed = model.rsplit("_", 1)
                seed = int(raw_seed)
                color, style, marker = COLORS[condition], STYLES[seed], MARKERS[seed]
                label = f"{'Exact' if condition == 'robust' else 'Modulo'} {seed}"
            values = [r[metric + "_rate"] for r in rows]
            ax.plot(range(3), values, color=color, ls=style, marker=marker, lw=1.7, ms=5, label=label)
            ax.vlines(range(3), [r[metric + "_ci_low"] for r in rows], [r[metric + "_ci_high"] for r in rows], color=color, alpha=.23, lw=1.2)
        ax.set_title(title, loc="left", weight="bold")
        ax.set_ylim(0, 1)
        style_axis(ax)
    handles, labels = axes[0, 0].get_legend_handles_labels()
    fig.legend(handles, labels, ncol=4, loc="lower center", frameon=False, bbox_to_anchor=(.5, .015))
    fig.suptitle("Longer completions change measured performance and answer coverage", x=.07, y=.99, ha="left", fontsize=16, weight="bold")
    fig.text(.07, .947, "Frozen terminal extractor · 500 shared development examples per cell · thin bars: 95% example-bootstrap intervals", fontsize=10, color="#444444")
    fig.subplots_adjust(top=.87, bottom=.17, hspace=.3, wspace=.22)
    save(fig, output, "accuracy_and_completion")

    contrasts = read(analysis / "condition_contrasts.json")
    pair_lookup = {(c["seed"], c["cap"], c["policy"], c["metric"]): c for c in contrasts["individual_pairs"]}
    avg_lookup = {(c["cap"], c["policy"], c["metric"]): c for c in contrasts["fixed_pair_average"]}
    fig, axes = plt.subplots(1, 3, figsize=(13, 4.8))
    for ax, (metric, title) in zip(axes, panels[:3]):
        for seed, offset in zip(SEEDS, (-.11, 0, .11)):
            rows = [pair_lookup[seed, cap, "terminal", metric] for cap in CAPS]
            xs = [i + offset for i in range(3)]
            color = {201: "#347BB2", 202: "#974B9F", 203: "#3E8460"}[seed]
            ax.errorbar(xs, [r["estimate"] for r in rows],
                        yerr=[[r["estimate"] - r["ci95"][0] for r in rows], [r["ci95"][1] - r["estimate"] for r in rows]],
                        color=color, marker=MARKERS[seed], capsize=3, ls=STYLES[seed], lw=1.4, label=f"Seed pair {seed}")
        avg = [avg_lookup[cap, "terminal", metric] for cap in CAPS]
        ax.plot(range(3), [r["estimate"] for r in avg], marker="D", color="#222222", lw=2, ms=4, label="Mean of three fixed pairs")
        ax.axhline(0, color="#666666", lw=1)
        ax.set_title(title, loc="left", weight="bold")
        style_axis(ax)
        ax.set_ylabel("Modulo − Exact (percentage points)")
        ax.yaxis.set_major_formatter(FuncFormatter(lambda value, pos: f"{100 * value:g}"))
    fig.suptitle("Reward-condition differences must be read across all three seed pairs", x=.06, y=1, ha="left", fontsize=15, weight="bold")
    fig.text(.06, .925, "Unconditional terminal scores · intervals resample shared examples and condition on these runs; they do not quantify new-run uncertainty", fontsize=9.5)
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, ncol=4, frameon=False, loc="lower center", bbox_to_anchor=(.5, -.01))
    fig.subplots_adjust(top=.8, bottom=.2, wspace=.32)
    save(fig, output, "all_seed_pair_differences")

    fig, axes = plt.subplots(1, 3, figsize=(12.8, 5.3), sharey=True)
    for ax, cap in zip(axes, CAPS):
        labels = []
        for n, model in enumerate(models):
            cell = lookup[model, cap, "terminal"]
            stop = cell["stopping_counts"]
            before = stop.get("eos_before_limit", 0) / 500
            at = stop.get("eos_at_limit", 0) / 500
            limited = stop.get("token_limit_without_eos", 0) / 500
            ax.barh(n, before, color="#5D9A83", label="EOS before limit" if n == 0 else None)
            ax.barh(n, at, left=before, color="#B4C98B", label="EOS at limit" if n == 0 else None)
            ax.barh(n, limited, left=before + at, color="#D98D61", label="Limit without EOS" if n == 0 else None)
            labels.append(model.replace("robust_", "Exact ").replace("proxy_", "Modulo ").replace("Base", "Base"))
            if limited > .07:
                ax.text(before + at + limited / 2, n, f"{limited:.0%}", ha="center", va="center", fontsize=9, color="#222222")
        ax.set_title(f"{cap} new tokens", loc="left", weight="bold")
        ax.set_xlim(0, 1)
        ax.set_yticks(range(len(models)), labels)
        ax.xaxis.set_major_formatter(PercentFormatter(1))
        ax.spines[["top", "right"]].set_visible(False)
        ax.grid(axis="x", alpha=.12)
        ax.set_axisbelow(True)
    axes[0].invert_yaxis()
    fig.suptitle("Actual stopping events separate token limits from EOS", x=.09, y=.99, ha="left", fontsize=15, weight="bold")
    fig.text(.09, .915, "Original generated token IDs · EOS at the final allowed token is EOS, not a token-limit stop · 500 completions per bar", fontsize=9.5)
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, ncol=3, frameon=False, loc="lower center", bbox_to_anchor=(.5, .01))
    fig.subplots_adjust(top=.82, bottom=.15, wspace=.16)
    save(fig, output, "actual_stopping_reasons")

    fig, axes = plt.subplots(1, 3, figsize=(12.5, 4.7), sharey=True)
    policy_colors = {"legacy": "#B87428", "terminal": "#206A95", "declared": "#8D5796"}
    for ax, cap in zip(axes, CAPS):
        for policy, offset in zip(("legacy", "terminal", "declared"), (-.16, 0, .16)):
            for pos, seed in enumerate(SEEDS):
                row = pair_lookup[seed, cap, policy, "exact_correct"]
                ax.errorbar(pos + offset, row["estimate"], yerr=[[row["estimate"] - row["ci95"][0]], [row["ci95"][1] - row["estimate"]]],
                            color=policy_colors[policy], marker="o", capsize=3, ms=5, label=policy if pos == 0 else None)
        ax.axhline(0, color="#666666", lw=1)
        ax.set_xticks(range(3), ["201", "202", "203"])
        ax.set_title(f"{cap} new tokens", loc="left", weight="bold")
        ax.set_xlabel("Paired training seed")
        ax.spines[["top", "right"]].set_visible(False)
        ax.yaxis.set_major_formatter(FuncFormatter(lambda value, pos: f"{100 * value:g}"))
        ax.grid(axis="y", alpha=.18)
    axes[0].set_ylabel("Exact accuracy: Modulo − Exact (pp)")
    fig.suptitle("Extraction policies can change the apparent condition difference", x=.08, y=.99, ha="left", fontsize=15, weight="bold")
    fig.text(.08, .91, "Same generated strings · declared-only is a format sensitivity, not a required answer format · 95% example-bootstrap intervals", fontsize=9.5)
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, ncol=3, frameon=False, loc="lower center", bbox_to_anchor=(.5, .01))
    fig.subplots_adjust(top=.79, bottom=.19, wspace=.15)
    save(fig, output, "extraction_policy_sensitivity")

    loo_lookup = {(r["omitted_seed"], r["cap"], r["policy"], r["metric"]): r for r in contrasts["leave_one_pair_out"]}
    fig, axes = plt.subplots(1, 3, figsize=(13, 4.9))
    for ax, (metric, title) in zip(axes, panels[:3]):
        for omitted, offset in zip((None, *SEEDS), (-.15, -.05, .05, .15)):
            rows = [(avg_lookup[cap, "terminal", metric] if omitted is None else
                     loo_lookup[omitted, cap, "terminal", metric]) for cap in CAPS]
            color = {None: "#222222", 201: "#347BB2", 202: "#974B9F", 203: "#3E8460"}[omitted]
            label = "All three pairs" if omitted is None else f"Omit pair {omitted}"
            ax.errorbar([i + offset for i in range(3)], [r["estimate"] for r in rows],
                        yerr=[[r["estimate"] - r["ci95"][0] for r in rows], [r["ci95"][1] - r["estimate"] for r in rows]],
                        marker="D" if omitted is None else MARKERS[omitted], color=color,
                        capsize=2, lw=1.5, ls="-" if omitted is None else STYLES[omitted], ms=4, label=label)
        ax.axhline(0, color="#666666", lw=1)
        ax.set_title(title, loc="left", weight="bold")
        style_axis(ax)
        ax.yaxis.set_major_formatter(FuncFormatter(lambda value, pos: f"{100 * value:g}"))
        ax.set_ylabel("Modulo − Exact (percentage points)")
    fig.suptitle("Leave-one-pair-out sensitivity exposes dependence on individual runs", x=.06, y=.99, ha="left", fontsize=15, weight="bold")
    fig.text(.06, .915, "Equal weight to retained fixed pairs · 95% paired-example intervals condition on these runs; three pairs do not establish training-run power", fontsize=9.5)
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, ncol=4, frameon=False, loc="lower center", bbox_to_anchor=(.5, .005))
    fig.subplots_adjust(top=.8, bottom=.2, wspace=.32)
    save(fig, output, "leave_one_pair_out")

    diagnostics = read(analysis / "model_diagnostics.json")
    special = {(r["cap"], r["metric"]): r for r in diagnostics
               if r["contrast"] == "Exact_202_minus_mean_Exact_201_203" and r["policy"] == "terminal"}
    metric_colors = {"exact_correct": "#1764A0", "mod10_correct": "#7C5797", "proxy_only_correct": "#CC7139"}
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    for ax, selected in zip(axes, (False, True)):
        for metric, label in panels[:3]:
            source_rows = [special[cap, metric] for cap in CAPS]
            rows = [r["common_accepted_eos"] if selected else r for r in source_rows]
            present = [(i, r) for i, r in enumerate(rows) if r["estimate"] is not None]
            if present:
                ax.errorbar([i for i, r in present], [r["estimate"] for i, r in present],
                            yerr=[[r["estimate"] - r["ci95"][0] for i, r in present], [r["ci95"][1] - r["estimate"] for i, r in present]],
                            marker="o", color=metric_colors[metric], lw=1.7, capsize=3, ms=5, label=label)
        ax.axhline(0, color="#666666", lw=1)
        ax.set_title("Common accepted + EOS subset" if selected else "Unconditional: all 500 examples", loc="left", weight="bold")
        style_axis(ax)
        ax.yaxis.set_major_formatter(FuncFormatter(lambda value, pos: f"{100 * value:g}"))
        ax.set_ylabel("Exact 202 − mean(Exact 201, 203), pp")
    selected_sizes = [special[cap, "exact_correct"]["common_accepted_eos"]["n"] for cap in CAPS]
    fig.suptitle("Does Exact seed 202 remain unusual after the controls?", x=.07, y=.99, ha="left", fontsize=15, weight="bold")
    fig.text(.07, .915, "Frozen terminal policy · bars: 95% paired-example intervals conditional on these models", fontsize=10)
    fig.text(.07, .865, f"Selected subset requires all three Exact responses accepted and EOS-terminated; N at 128/256/512: {' / '.join(map(str, selected_sizes))}. Selection changes the estimand.", fontsize=9.2)
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, ncol=3, frameon=False, loc="lower center", bbox_to_anchor=(.5, .005))
    fig.subplots_adjust(top=.76, bottom=.2, wspace=.3)
    save(fig, output, "exact_seed_202_diagnostic")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--analysis", type=Path, default=HERE / "analysis_001")
    parser.add_argument("--output", type=Path, default=HERE / "figures_001")
    args = parser.parse_args()
    render(args.analysis, args.output)
