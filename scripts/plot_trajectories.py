"""Plot validation dynamics and paired sealed-test outcomes from stored data."""

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


SEEDS = (201, 202, 203)
CONDITION_COLORS = {"Robust": "#35618f", "Proxy": "#c66b2b"}
METRIC_STYLES = {
    "Exact": ("true_accuracy", "-", "o"),
    "Modulo-10": ("mean_observed_reward", "--", "s"),
}


def required(mapping, key, context):
    if key not in mapping:
        raise KeyError(f"Missing required field {context}.{key}")
    return mapping[key]


def checkpoint_step(key: str) -> int:
    if "final_model" in key:
        return 500
    if "checkpoint-" not in key:
        raise ValueError(f"Cannot determine checkpoint step from {key!r}")
    return int(key.rsplit("checkpoint-", 1)[1])


def load_results(repo_root: Path):
    path = repo_root / "experiments" / "milestone3" / "eval_results.json"
    if not path.is_file():
        raise FileNotFoundError(path)
    results = json.loads(path.read_text())
    required(results, "test", "eval_results")
    required(results, "eval_checkpoints", "eval_results")
    return results


def validation_series(checkpoints, condition: str, seed: int, metric_key: str):
    base_entry = required(checkpoints, "Base", "eval_checkpoints")
    base_metrics = required(base_entry, "metrics", "eval_checkpoints.Base")
    values = [(0, required(base_metrics, metric_key, "eval_checkpoints.Base.metrics"))]

    prefix = f"{condition} RL (Seed {seed})"
    keys = [key for key in checkpoints if key.startswith(prefix)]
    if len(keys) != 4:
        raise ValueError(f"Expected four checkpoints for {prefix}; found {len(keys)}")
    for key in sorted(keys, key=checkpoint_step):
        metrics = required(checkpoints[key], "metrics", f"eval_checkpoints.{key}")
        values.append((checkpoint_step(key), required(metrics, metric_key, f"{key}.metrics")))
    return np.asarray(values, dtype=float)


def plot_validation_trajectories(results, output_path: Path) -> None:
    checkpoints = results["eval_checkpoints"]
    base_metrics = required(checkpoints["Base"], "metrics", "eval_checkpoints.Base")
    if base_metrics["true_accuracy"] != 0.02 or base_metrics["mean_observed_reward"] != 0.50:
        raise ValueError("Stored validation Base metrics do not match 2.0% exact / 50.0% modulo-10")

    fig, axes = plt.subplots(1, 3, figsize=(15.5, 5.2), sharex=True, sharey=True)
    for ax, seed in zip(axes, SEEDS):
        for condition in ("Robust", "Proxy"):
            for metric_label, (metric_key, linestyle, marker) in METRIC_STYLES.items():
                series = validation_series(checkpoints, condition, seed, metric_key)
                ax.plot(
                    series[:, 0] / 5,
                    series[:, 1] * 100,
                    color=CONDITION_COLORS[condition],
                    linestyle=linestyle,
                    marker=marker,
                    linewidth=2,
                    markersize=5,
                    label=f"{condition} · {metric_label}",
                )
        ax.set_title(f"Seed {seed}", fontsize=12, weight="bold")
        ax.set_xlabel("Training progress (%)")
        ax.set_xticks((0, 25, 50, 75, 100))
        ax.set_ylim(0, 103)
        ax.set_yticks((0, 20, 40, 60, 80, 100))
        ax.grid(axis="y", color="#d7d7d7", linewidth=0.8)
        ax.spines[["top", "right"]].set_visible(False)

    axes[0].set_ylabel("Validation accuracy (%)")
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=4, frameon=False)
    fig.suptitle("Validation checkpoint trajectories", fontsize=15, weight="bold")
    fig.text(
        0.5,
        0.92,
        "Step 0 uses the validation Base result (2.0% exact; 50.0% modulo-10)",
        ha="center",
        fontsize=10,
        color="#4a4a4a",
    )
    fig.tight_layout(rect=(0, 0.10, 1, 0.90))
    fig.savefig(output_path, dpi=300, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def final_metric(test_results, condition: str, seed: int, metric_key: str) -> float:
    key = f"{condition} RL (Seed {seed})"
    entry = required(test_results, key, "test")
    metrics = required(entry, "metrics", f"test.{key}")
    return required(metrics, metric_key, f"test.{key}.metrics")


def plot_sealed_test_comparison(results, output_path: Path) -> None:
    test_results = results["test"]
    metrics = (
        ("Exact accuracy", "true_accuracy"),
        ("Modulo-10 accuracy", "mean_observed_reward"),
        ("Proxy-only success\n(metric-gaming rate)", "reward_hacking_rate"),
    )
    x = np.arange(len(SEEDS))
    width = 0.34
    fig, axes = plt.subplots(1, 3, figsize=(14.5, 4.8), sharey=True)

    for ax, (title, metric_key) in zip(axes, metrics):
        robust = [final_metric(test_results, "Robust", seed, metric_key) * 100 for seed in SEEDS]
        proxy = [final_metric(test_results, "Proxy", seed, metric_key) * 100 for seed in SEEDS]
        robust_bars = ax.bar(
            x - width / 2,
            robust,
            width,
            label="Robust",
            color=CONDITION_COLORS["Robust"],
        )
        proxy_bars = ax.bar(
            x + width / 2,
            proxy,
            width,
            label="Proxy",
            color=CONDITION_COLORS["Proxy"],
        )
        ax.bar_label(robust_bars, fmt="%.1f", padding=2, fontsize=8)
        ax.bar_label(proxy_bars, fmt="%.1f", padding=2, fontsize=8)
        ax.set_title(title, fontsize=11, weight="bold")
        ax.set_xticks(x, [str(seed) for seed in SEEDS])
        ax.set_xlabel("Paired training seed")
        ax.set_ylim(0, 105)
        ax.grid(axis="y", color="#d7d7d7", linewidth=0.8)
        ax.set_axisbelow(True)
        ax.spines[["top", "right"]].set_visible(False)

    axes[0].set_ylabel("Sealed-test rate (%)")
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=2, frameon=False)
    fig.suptitle("Final sealed-test paired seed comparison", fontsize=15, weight="bold")
    fig.tight_layout(rect=(0, 0.10, 1, 0.92))
    fig.savefig(output_path, dpi=300, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    figures_dir = repo_root / "figures"
    figures_dir.mkdir(exist_ok=True)
    results = load_results(repo_root)

    validation_path = figures_dir / "validation_trajectories.png"
    sealed_path = figures_dir / "sealed_test_seed_comparison.png"
    plot_validation_trajectories(results, validation_path)
    plot_sealed_test_comparison(results, sealed_path)
    print(f"Saved {validation_path.relative_to(repo_root)}")
    print(f"Saved {sealed_path.relative_to(repo_root)}")


if __name__ == "__main__":
    main()
