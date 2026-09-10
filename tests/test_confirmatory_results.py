import json
from pathlib import Path

import numpy as np
import pytest

from math_reward_hacking.evaluation.metrics import aggregate_metrics
from math_reward_hacking.rewards.verifiers import verify_true_answer


RESULTS_PATH = (
    Path(__file__).resolve().parents[1]
    / "experiments"
    / "milestone3"
    / "eval_results.json"
)


@pytest.fixture(scope="module")
def stored_results():
    return json.loads(RESULTS_PATH.read_text())


def test_confirmatory_summary_values_and_sample_sd(stored_results):
    expected = {
        "Robust": {
            "true_accuracy": (0.2420, 0.010392304845413258),
            "mean_observed_reward": (0.8753333333333333, 0.15533619453731104),
        },
        "Proxy": {
            "true_accuracy": (0.25133333333333335, 0.010263202878893777),
            "mean_observed_reward": (0.9793333333333334, 0.00503322295684717),
        },
    }
    for condition, metric_expectations in expected.items():
        rows = [
            stored_results["test"][f"{condition} RL (Seed {seed})"]["metrics"]
            for seed in (201, 202, 203)
        ]
        for key, (expected_mean, expected_sd) in metric_expectations.items():
            values = [row[key] for row in rows]
            assert np.mean(values) == pytest.approx(expected_mean)
            assert np.std(values, ddof=1) == pytest.approx(expected_sd)


def test_metric_gaming_identity_for_all_stored_aggregates(stored_results):
    sections = (stored_results["test"], stored_results["eval_checkpoints"])
    for section in sections:
        for name, entry in section.items():
            metrics = entry["metrics"]
            assert metrics["reward_hacking_rate"] == pytest.approx(
                metrics["mean_observed_reward"] - metrics["true_accuracy"],
                abs=1e-12,
            ), name


def test_all_stored_aggregates_recompute_from_details(stored_results):
    sections = (stored_results["test"], stored_results["eval_checkpoints"])
    for section in sections:
        for name, entry in section.items():
            recomputed = aggregate_metrics(entry["detailed_results"])
            for key, value in entry["metrics"].items():
                assert recomputed[key] == pytest.approx(value, abs=1e-12), (name, key)


def test_corrected_integer_equality_does_not_change_stored_exact_scores(stored_results):
    sections = (stored_results["test"], stored_results["eval_checkpoints"])
    for section in sections:
        for name, entry in section.items():
            for row in entry["detailed_results"]:
                assert verify_true_answer(
                    row["model_response"], row["ground_truth"]
                ) == row["true_correctness"], (name, row["problem_id"])


def test_validation_base_reference(stored_results):
    metrics = stored_results["eval_checkpoints"]["Base"]["metrics"]
    assert metrics["true_accuracy"] == 0.02
    assert metrics["mean_observed_reward"] == 0.50
