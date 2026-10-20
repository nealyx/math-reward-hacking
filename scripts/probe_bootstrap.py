"""Diagnose the recorded cross-platform difference without altering analysis.

Replays the one affected bootstrap using the frozen function's exact operations
and reports fingerprints before sampling, after sampling, and at the quantile.
"""
from __future__ import annotations

from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import platform
import statistics
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "case_studies/completion_budget_diagnostic"


def digest(value):
    return hashlib.sha256(value).hexdigest()


def main():
    spec = importlib.util.spec_from_file_location("public_reproduce_probe", PACKAGE / "reproduce.py")
    reproduction = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(reproduction)
    _, index, analysis = reproduction.verify(PACKAGE)
    expected = reproduction.load_json(PACKAGE / "results/model_diagnostics.json")[146]
    label = "model-diagnostic/{contrast}/{cap}/{policy}/{metric}".format(**expected)
    values = [
        analysis.metric(index[expected["model"], expected["cap"], i], expected["policy"], expected["metric"])
        - statistics.fmean(analysis.metric(index[ref, expected["cap"], i], expected["policy"], expected["metric"])
                           for ref in expected["references"])
        for i in range(500)
    ]
    counts = Counter(values)
    cats = sorted(counts)
    probabilities = [counts[c] / len(values) for c in cats]
    seed = int.from_bytes(hashlib.sha256(f"{analysis.BOOTSTRAP_SEED}:{label}".encode()).digest()[:8], "big")
    rng = np.random.default_rng(seed)
    initial_state = rng.bit_generator.state
    sampled = rng.multinomial(len(values), probabilities, size=analysis.BOOTSTRAP_DRAWS)
    means = (sampled * np.asarray(cats)).sum(axis=1) / len(values)
    ordered = np.sort(means)
    histogram = Counter(float(v) for v in means)
    report = {
        "python": sys.version, "platform": platform.platform(), "machine": platform.machine(),
        "numpy": np.__version__, "target": {k: expected[k] for k in ("contrast", "cap", "policy", "metric")},
        "label": label, "seed": seed, "categories": cats,
        "counts": [counts[c] for c in cats], "probabilities": probabilities,
        "paired_values_sha256": digest(np.asarray(values, dtype="<f8").tobytes()),
        "initial_bit_generator_state": initial_state,
        "first_10000_raw_uint64_sha256": digest(np.random.default_rng(seed).bit_generator.random_raw(10000).astype("<u8").tobytes()),
        "sampled_counts_sha256": digest(sampled.astype("<i8").tobytes()),
        "bootstrap_means_sha256": digest(means.astype("<f8").tobytes()),
        "final_bit_generator_state": rng.bit_generator.state,
        "bootstrap_mean_histogram": [[value, histogram[value]] for value in sorted(histogram)],
        "upper_quantile_neighbors": [[i, float(ordered[i])] for i in range(9745, 9755)],
        "saved_interval": expected["ci95"],
        "replayed_interval": [float(v) for v in np.quantile(means, [.025, .975])],
        "frozen_function_interval": analysis.interval(values, label)["ci95"],
    }
    print(json.dumps(report, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
