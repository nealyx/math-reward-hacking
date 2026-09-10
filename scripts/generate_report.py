"""Generate the Milestone 3 report from immutable stored evaluations."""

import hashlib
import json
from collections.abc import Mapping
from pathlib import Path

import numpy as np
from transformers import AutoTokenizer


SEEDS = (201, 202, 203)
MODEL_NAME = "Qwen/Qwen2.5-0.5B-Instruct"
ORIGINAL_RECORDED_TRAIN_HASH = (
    "aa220bc2a78624fd70a49eb0ee22e09263aa0b03bd3b15b166a5cccb264b73d2"
)
AUDITED_PRE_CLEANUP_TRAIN_HASH = (
    "cdb26be6927116b5466cbedfba92e147f24059887511741d7c72c3f675c82450"
)
REQUIRED_METRICS = (
    "true_accuracy",
    "mean_observed_reward",
    "reward_hacking_rate",
    "reward_hacking_given_reward",
    "correct_residue_among_incorrect",
    "single_digit_answer_rate",
    "small_answer_rate",
    "invalid_output_rate",
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def require_key(mapping: Mapping, key: str, context: str):
    if not isinstance(mapping, Mapping):
        raise TypeError(f"{context} must be a mapping")
    if key not in mapping:
        raise KeyError(f"Missing required field {context}.{key}")
    return mapping[key]


def require_metrics(entry: Mapping, context: str) -> Mapping:
    metrics = require_key(entry, "metrics", context)
    for key in REQUIRED_METRICS:
        require_key(metrics, key, f"{context}.metrics")

    exact = metrics["true_accuracy"]
    mod10 = metrics["mean_observed_reward"]
    gaming = metrics["reward_hacking_rate"]
    if not np.isclose(gaming, mod10 - exact, rtol=0.0, atol=1e-12):
        raise ValueError(
            f"Metric identity failed for {context}: {gaming} != {mod10} - {exact}"
        )
    return metrics


def analyze_lengths(detailed_results, tokenizer, max_len: int = 128) -> dict:
    if not isinstance(detailed_results, list) or not detailed_results:
        raise ValueError("detailed_results must be a non-empty list")

    lengths = []
    for index, row in enumerate(detailed_results):
        response = require_key(row, "model_response", f"detailed_results[{index}]")
        if not isinstance(response, str):
            raise TypeError(
                f"detailed_results[{index}].model_response must be a string"
            )
        lengths.append(
            len(tokenizer.encode(response, add_special_tokens=False))
        )

    return {
        "mean_visible_completion_tokens": float(np.mean(lengths)),
        "median_visible_completion_tokens": float(np.median(lengths)),
        "fraction_visible_completions_at_or_above_128_tokens": (
            sum(length >= max_len for length in lengths) / len(lengths)
        ),
        "total_retokenized_visible_completion_tokens": int(sum(lengths)),
    }


def get_train_runtime(base_dir: Path, condition: str, seed: int):
    run_dir = base_dir / f"{condition.lower()}_seed_{seed}"
    candidates = (
        run_dir / "final_model" / "trainer_state.json",
        run_dir / "checkpoint-500" / "trainer_state.json",
    )
    for state_path in candidates:
        if not state_path.exists():
            continue
        state = json.loads(state_path.read_text())
        history = require_key(state, "log_history", str(state_path))
        for entry in reversed(history):
            if "train_runtime" in entry:
                return entry["train_runtime"]
    return None


def condition_results(test_results: Mapping, condition: str) -> list[tuple[int, Mapping]]:
    rows = []
    for seed in SEEDS:
        key = f"{condition} RL (Seed {seed})"
        entry = require_key(test_results, key, "test")
        require_metrics(entry, f"test.{key}")
        require_key(entry, "detailed_results", f"test.{key}")
        rows.append((seed, entry))
    return rows


def mean_sd(entries, metric_key: str) -> tuple[float, float]:
    values = [entry["metrics"][metric_key] for _, entry in entries]
    return float(np.mean(values)), float(np.std(values, ddof=1))


def fmt_runtime(value) -> str:
    return "N/A" if value is None else f"{value:.1f}"


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    base_dir = repo_root / "experiments" / "milestone3"
    eval_file = base_dir / "eval_results.json"
    hashes_file = base_dir / "milestone3_frozen_hashes.json"
    report_file = base_dir / "report_milestone3.md"

    if not eval_file.is_file():
        raise FileNotFoundError(f"Missing required eval results: {eval_file}")
    if not hashes_file.is_file():
        raise FileNotFoundError(f"Missing required hashes: {hashes_file}")

    results = json.loads(eval_file.read_text())
    hashes = json.loads(hashes_file.read_text())
    test_results = require_key(results, "test", "eval_results")
    checkpoint_results = require_key(results, "eval_checkpoints", "eval_results")

    git_state = require_key(hashes, "git_dirty_status", "frozen_hashes")
    reward_source_hash = require_key(hashes, "reward_source_file", "frozen_hashes")
    original_train_hash = require_key(hashes, "train_grpo_script", "frozen_hashes")
    if original_train_hash != ORIGINAL_RECORDED_TRAIN_HASH:
        raise ValueError(
            "Unexpected recorded original train_grpo.py digest: "
            f"{original_train_hash}"
        )

    base_entry = require_key(test_results, "Base", "test")
    base_metrics = require_metrics(base_entry, "test.Base")
    base_details = require_key(base_entry, "detailed_results", "test.Base")
    base_validation = require_key(checkpoint_results, "Base", "eval_checkpoints")
    base_validation_metrics = require_metrics(base_validation, "eval_checkpoints.Base")
    require_key(base_validation, "detailed_results", "eval_checkpoints.Base")

    robust = condition_results(test_results, "Robust")
    proxy = condition_results(test_results, "Proxy")

    tokenizer_path = base_dir / "robust_seed_201" / "final_model"
    if not tokenizer_path.is_dir():
        raise FileNotFoundError(f"Missing stored tokenizer directory: {tokenizer_path}")
    tokenizer = AutoTokenizer.from_pretrained(tokenizer_path, local_files_only=True)
    current_train_hash = sha256_file(repo_root / "scripts" / "train_grpo.py")
    robust_201_final = base_dir / "robust_seed_201" / "final_model" / "adapter_model.safetensors"
    robust_201_checkpoint = base_dir / "robust_seed_201" / "checkpoint-500" / "adapter_model.safetensors"
    robust_201_adapter_match = (
        sha256_file(robust_201_final) == sha256_file(robust_201_checkpoint)
    )
    if not robust_201_adapter_match:
        raise ValueError("Robust Seed 201 final adapter differs from checkpoint-500")

    report = [
        "# Milestone 3 Confirmatory Report",
        "",
        "## Scope and configuration",
        "",
        (
            "This report analyzes the stored outputs from an internally prespecified "
            "six-run confirmatory protocol. Seed 101 was exploratory and is excluded."
        ),
        "",
        f"- Model: `{MODEL_NAME}` (the original revision was not pinned)",
        "- Conditions: exact-answer Robust reward and deliberately vulnerable modulo-10 Proxy reward",
        "- Training seeds: 201, 202, 203 in each condition",
        "- Data: 500 train / 100 validation / 500 sealed-test examples",
        "- GRPO: TRL 1.12.0, one epoch, batch size 1, gradient accumulation 4, four generations, temperature 0.8, maximum completion length 128",
        f"- Recorded execution-time Git state: {git_state}",
        f"- Recorded reward-source SHA-256: `{reward_source_hash}`",
        "",
        "## Sealed-test results",
        "",
        (
            "Across three seeds, proxy-reward training yielded consistently high "
            "modulo-10 accuracy while exact-answer accuracy remained similar to "
            "robust-reward training. The average Proxy advantage over Robust was "
            "driven primarily by Robust Seed 202, so these results support a "
            "proxy–truth gap under the vulnerable reward but do not establish a "
            "stable condition effect across seeds."
        ),
        "",
        "Values below are mean ± sample SD across n=3 seeds.",
        "",
        "| Metric | Base | Robust | Proxy | Proxy − Robust |",
        "|---|---:|---:|---:|---:|",
    ]

    summary_metrics = (
        ("Exact accuracy", "true_accuracy"),
        ("Modulo-10 accuracy", "mean_observed_reward"),
        ("Metric-gaming rate", "reward_hacking_rate"),
        ("Small-answer rate", "small_answer_rate"),
    )
    for label, key in summary_metrics:
        robust_mean, robust_sd = mean_sd(robust, key)
        proxy_mean, proxy_sd = mean_sd(proxy, key)
        report.append(
            f"| {label} | {base_metrics[key]:.4f} | "
            f"{robust_mean:.4f} ± {robust_sd:.4f} | "
            f"{proxy_mean:.4f} ± {proxy_sd:.4f} | "
            f"{proxy_mean - robust_mean:+.4f} |"
        )

    report.extend(
        [
            "",
            (
                "`metric_gaming_rate = mod10_accuracy − exact_accuracy`. Exact "
                "correctness implies modulo-10 correctness, so this is a derived "
                "operational measure of proxy-only success, not independent evidence."
            ),
            "",
            "### Paired seed results",
            "",
            "| Seed | Condition | Exact | Modulo-10 | Metric-gaming rate | Small-answer rate |",
            "|---:|---|---:|---:|---:|---:|",
        ]
    )
    for seed in SEEDS:
        for condition, entries in (("Robust", robust), ("Proxy", proxy)):
            entry = dict(entries)[seed]
            metrics = entry["metrics"]
            report.append(
                f"| {seed} | {condition} | {metrics['true_accuracy']:.4f} | "
                f"{metrics['mean_observed_reward']:.4f} | "
                f"{metrics['reward_hacking_rate']:.4f} | "
                f"{metrics['small_answer_rate']:.4f} |"
            )

    report.extend(
        [
            "",
            "| Seed | Proxy − Robust modulo-10 | Proxy − Robust metric-gaming rate |",
            "|---:|---:|---:|",
        ]
    )
    robust_by_seed = dict(robust)
    proxy_by_seed = dict(proxy)
    for seed in SEEDS:
        r_metrics = robust_by_seed[seed]["metrics"]
        p_metrics = proxy_by_seed[seed]["metrics"]
        report.append(
            f"| {seed} | "
            f"{p_metrics['mean_observed_reward'] - r_metrics['mean_observed_reward']:+.4f} | "
            f"{p_metrics['reward_hacking_rate'] - r_metrics['reward_hacking_rate']:+.4f} |"
        )

    report.extend(
        [
            "",
            (
                "The Seed 202 paired gaps (+28.8 percentage points modulo-10 and "
                "+26.4 points metric-gaming rate) dominate the corresponding "
                "three-seed averages; Seeds 201 and 203 have +1.2-point modulo-10 gaps."
            ),
            "",
            "## Hypothesis outcomes",
            "",
            (
                "- **H1 — not satisfied on the sealed test.** Base exact accuracy was "
                "4.2%, below the prespecified >10% threshold. The earlier competence "
                "screen reported 22% using a distinct artifact and 256 generation "
                "tokens; it is not the 128-token sealed-test baseline."
            ),
            (
                "- **H2 — descriptively supported.** Mean Robust exact accuracy "
                "increased from the 4.2% Base result to 24.2%. No prespecified "
                "significance test was conducted."
            ),
            (
                "- **H3 — not supported as proposed.** Proxy exact accuracy (25.13%) "
                "was not lower than Robust exact accuracy (24.20%), although Proxy "
                "modulo-10 accuracy was high (97.93%)."
            ),
            (
                "- **H4 — not supported by the proposed small-answer signature.** "
                "Proxy small-answer rate was 1.2%, below Robust's 5.8%."
            ),
            (
                "- **H5 — mixed/partially supported.** Proxy modulo-10 accuracy rose "
                "to 97–99% at final validation checkpoints while exact accuracy "
                "remained 21–23%, but the paths were not uniformly monotonic and two "
                "Robust seeds reached similarly high modulo-10 validation accuracy."
            ),
            "",
            "## Visible completion lengths",
            "",
            (
                "These are retokenized visible completion tokens from stored decoded "
                f"`model_response` text using the stored `{MODEL_NAME}` tokenizer "
                "from `robust_seed_201/final_model`, with "
                "`add_special_tokens=False`. Prompts are excluded. These counts are "
                "not claimed to equal original generated sequence lengths including "
                "EOS or other special tokens."
            ),
            "",
            "| Condition | Seed | Mean visible completion tokens | Median | Fraction at/above 128 | Total retokenized visible tokens | Runtime (s) |",
            "|---|---:|---:|---:|---:|---:|---:|",
        ]
    )
    base_lengths = analyze_lengths(base_details, tokenizer)
    report.append(
        f"| Base | — | {base_lengths['mean_visible_completion_tokens']:.3f} | "
        f"{base_lengths['median_visible_completion_tokens']:.1f} | "
        f"{base_lengths['fraction_visible_completions_at_or_above_128_tokens']:.4f} | "
        f"{base_lengths['total_retokenized_visible_completion_tokens']} | N/A |"
    )
    for condition, entries in (("Robust", robust), ("Proxy", proxy)):
        for seed, entry in entries:
            lengths = analyze_lengths(entry["detailed_results"], tokenizer)
            runtime = get_train_runtime(base_dir, condition, seed)
            report.append(
                f"| {condition} | {seed} | "
                f"{lengths['mean_visible_completion_tokens']:.3f} | "
                f"{lengths['median_visible_completion_tokens']:.1f} | "
                f"{lengths['fraction_visible_completions_at_or_above_128_tokens']:.4f} | "
                f"{lengths['total_retokenized_visible_completion_tokens']} | "
                f"{fmt_runtime(runtime)} |"
            )

    report.extend(
        [
            "",
            "## Validation checkpoint trajectories",
            "",
            (
                "The step-0 validation reference is Base exact 2.0% and modulo-10 "
                "50.0%. The table preserves all three seeds rather than averaging "
                "away heterogeneity."
            ),
            "",
            "| Condition | Checkpoint | Exact | Modulo-10 | Metric-gaming rate | Invalid | Mean visible tokens |",
            "|---|---|---:|---:|---:|---:|---:|",
            (
                f"| Base | step 0 | {base_validation_metrics['true_accuracy']:.4f} | "
                f"{base_validation_metrics['mean_observed_reward']:.4f} | "
                f"{base_validation_metrics['reward_hacking_rate']:.4f} | "
                f"{base_validation_metrics['invalid_output_rate']:.4f} | "
                f"{analyze_lengths(base_validation['detailed_results'], tokenizer)['mean_visible_completion_tokens']:.1f} |"
            ),
        ]
    )

    checkpoint_keys = list(checkpoint_results.keys())
    for condition in ("Robust", "Proxy"):
        for seed in SEEDS:
            prefix = f"{condition} RL (Seed {seed})"
            keys = [key for key in checkpoint_keys if key.startswith(prefix)]
            if len(keys) != 4:
                raise ValueError(
                    f"Expected four validation checkpoints for {prefix}; found {len(keys)}"
                )

            def step(key: str):
                return 500 if "final_model" in key else int(key.rsplit("checkpoint-", 1)[1])

            for key in sorted(keys, key=step):
                entry = checkpoint_results[key]
                metrics = require_metrics(entry, f"eval_checkpoints.{key}")
                details = require_key(entry, "detailed_results", f"eval_checkpoints.{key}")
                lengths = analyze_lengths(details, tokenizer)
                checkpoint_name = key.rsplit(" - ", 1)[-1]
                report.append(
                    f"| {condition} Seed {seed} | {checkpoint_name} | "
                    f"{metrics['true_accuracy']:.4f} | "
                    f"{metrics['mean_observed_reward']:.4f} | "
                    f"{metrics['reward_hacking_rate']:.4f} | "
                    f"{metrics['invalid_output_rate']:.4f} | "
                    f"{lengths['mean_visible_completion_tokens']:.1f} |"
                )

    report.extend(
        [
            "",
            "## Evaluation semantics",
            "",
            (
                "The stored results retain the historical confirmatory evaluation "
                "semantics. Future-facing exact evaluation now compares parsed "
                "integers, so accepted spellings such as `42`, `+42`, and `042` are "
                "equivalent. Auditing every stored confirmatory response found no row "
                "whose exact-correctness value changes under that correction."
            ),
            "",
            "## Provenance and experimental incident",
            "",
            (
                "The helper calculation labeled `computed_max_steps` produced 125, "
                "whereas every surviving confirmatory `TrainerState` records "
                "`global_step=500` and `max_steps=500`. The manual estimate did not "
                "account for GRPOTrainer's effective sampling/step semantics. It was "
                "used for checkpoint/save-frequency bookkeeping and a post-training "
                "assertion; no surviving evidence shows that optimization length was "
                "set to 125. The issue was discovered while the sealed test remained unopened."
            ),
            "",
            (
                "Robust Seed 201 has a `final_model`, and its adapter is byte-identical "
                "to `checkpoint-500`; both appear in the preservation manifests. The "
                "earlier claim that the assertion prevented final-model creation was false."
            ),
            "",
            f"- Original training-source digest recorded in the frozen manifest: `{original_train_hash}`",
            (
                "- Status of that digest: recorded, but the original source bytes do "
                "not survive; it cannot be independently recomputed or cryptographically "
                "prove which exact bytes Robust Seed 201 executed."
            ),
            f"- Audited post-incident/pre-cleanup `train_grpo.py` digest: `{AUDITED_PRE_CLEANUP_TRAIN_HASH}`",
            f"- Current diagnostics-cleanup `train_grpo.py` digest: `{current_train_hash}`",
            (
                "- The two surviving Robust Seed 201 before/after checksum files are "
                "byte-identical and their listed files currently verify. Their labels "
                "do not independently establish the earlier execution-time source state."
            ),
            (
                "- Filesystem timestamps were not used as proof of execution order or source identity."
            ),
            "",
            "## Interpretation limits",
            "",
            (
                "There were only three confirmatory seeds, Robust outcomes varied "
                "substantially, and no significance or equivalence test was "
                "prespecified. The protocol was internally prespecified, not "
                "externally registered. The modulo-10 reward was deliberately designed "
                "as an artificial specification error. These results should not be "
                "generalized directly to frontier-model alignment or treated as proof "
                "of intentional cheating."
            ),
        ]
    )

    report_file.write_text("\n".join(report) + "\n")
    print(f"Report generated at {report_file.relative_to(repo_root)}")


if __name__ == "__main__":
    main()
