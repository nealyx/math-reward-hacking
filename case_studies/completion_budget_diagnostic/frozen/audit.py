"""Read-only historical audit. Writes only to a new diagnostics output directory.

No model inference, network access, package installation, or pickle loading.
The parser copy is checked against every stored extracted answer and method.
"""

import argparse
import collections
import hashlib
import json
import math
import random
import re
import statistics
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
SEEDS = (201, 202, 203)
GROUPED = re.compile(r"(?<![\w.,])([+-]?\d{1,3}(?:,\d{3})+)(?![\w,]|\.\d)")


def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda: f.read(4 * 1024 * 1024), b""):
            h.update(b)
    return h.hexdigest()


def legacy_parse(text):
    """Exact copy of the current extraction rules; not a proposed final parser."""
    matches = re.findall(r"(?i)(?:final\s*answer|answer)\s*(?::|={1,})\s*([+-]?\d+)", text)
    if matches:
        return matches[-1].strip(), "final_answer"
    matches = list(re.finditer(r"\\boxed{([+-]?\d+)}|x\s*=\s*([+-]?\d+)", text))
    if matches:
        m = matches[-1]
        return (m[1].strip(), "boxed") if m[1] else (m[2].strip(), "variable_assignment")
    matches = re.findall(r"(?<![\w.])([+-]?\d+)(?!\w)(?!\.\d)", text)
    return (matches[-1].strip(), "last_integer") if matches else (None, "unparseable")


def normalize_grouped_numbers(text):
    return GROUPED.sub(lambda m: m[1].replace(",", ""), text)


def finite_numbers(value):
    if isinstance(value, dict):
        return all(finite_numbers(v) for v in value.values())
    if isinstance(value, list):
        return all(finite_numbers(v) for v in value)
    return not isinstance(value, float) or math.isfinite(value)


def dump(out, name, obj):
    (out / name).write_text(json.dumps(obj, indent=2, allow_nan=False) + "\n")


def run(out):
    out = out.resolve()
    diagnostic_root = ROOT / "experiments/diagnostics"
    if not out.is_relative_to(diagnostic_root.resolve()):
        raise ValueError("Output must be under experiments/diagnostics/")
    out.mkdir(parents=True, exist_ok=False)
    historical = ROOT / "experiments/milestone3"
    protected = sorted(p for p in historical.rglob("*") if p.is_file())
    protected += sorted(p for family in ("configs", "src", "scripts", "tests", "figures")
                        for p in (ROOT / family).rglob("*")
                        if p.is_file() and "__pycache__" not in p.parts)
    protected += [ROOT / "README.md", ROOT / "pyproject.toml", ROOT / "uv.lock"]
    before = {str(p.relative_to(ROOT)): sha256(p) for p in protected}
    dump(out, "historical_before_sha256.json", before)
    results = json.loads((historical / "eval_results.json").read_text())
    summaries = []
    examples = []
    mismatches = []
    for split, models in results.items():
        for model, record in models.items():
            rows = sorted(record["detailed_results"], key=lambda r: r["problem_id"])
            methods = collections.Counter()
            grouped_last = grouped_recoveries = 0
            sensitivity_changes = []
            for r in rows:
                text = r["model_response"]
                parsed, method = legacy_parse(text)
                methods[method] += 1
                if parsed != r["parsed_answer"] or method != r["parse_method"]:
                    mismatches.append({"split": split, "model": model, "problem_id": r["problem_id"]})
                normalized, normalized_method = legacy_parse(normalize_grouped_numbers(text))
                gt = int(r["ground_truth"])
                old_exact = parsed is not None and int(parsed) == gt
                old_mod = parsed is not None and int(parsed) % 10 == gt % 10
                new_exact = normalized is not None and int(normalized) == gt
                new_mod = normalized is not None and int(normalized) % 10 == gt % 10
                if old_exact != new_exact or old_mod != new_mod:
                    sensitivity_changes.append({
                        "problem_id": r["problem_id"], "legacy": parsed,
                        "normalized": normalized, "ground_truth": gt,
                        "old_exact": old_exact, "new_exact": new_exact,
                        "old_mod10": old_mod, "new_mod10": new_mod,
                        "normalized_method": normalized_method,
                    })
                full_last = list(GROUPED.finditer(text))
                # Only claim a last grouped literal if no later digit remains.
                grouped = (full_last[-1][1] if full_last and
                           not re.search(r"\d", text[full_last[-1].end():]) else None)
                if method == "last_integer" and grouped is not None:
                    grouped_last += 1
                    if int(grouped.replace(",", "")) == gt and not old_exact:
                        grouped_recoveries += 1
                flags = []
                if method == "last_integer" and re.search(r"\bis\s*$", text):
                    flags.append("fallback_after_unfinished_is")
                    if old_mod and not old_exact:
                        flags.append("fallback_after_unfinished_is_with_proxy_credit")
                if method == "last_integer" and text.count(r"\(") > text.count(r"\)"):
                    flags.append("fallback_with_unclosed_inline_math")
                if grouped and int(grouped.replace(",", "")) == gt and not old_exact:
                    flags.append("grouped_final_literal_matches_target_but_legacy_does_not")
                if method == "final_answer" and old_mod != new_mod:
                    flags.append("explicit_grouped_integer_prefix_changes_modulo_score")
                for flag in flags:
                    key = (split, model, flag)
                    if not any((e["split"], e["model"], e["selection_rule"]) == key for e in examples):
                        examples.append({"split": split, "model": model, "selection_rule": flag,
                                         "problem_id": r["problem_id"], "prompt": r["prompt"],
                                         "ground_truth": gt, "legacy_value": parsed,
                                         "legacy_method": method, "model_response": text})
            summaries.append({
                "split": split, "model": model, "n": len(rows),
                "stored_metrics": record["metrics"], "parse_methods": dict(methods),
                "last_grouped_literal_and_fallback": grouped_last,
                "grouped_literal_exact_recoveries": grouped_recoveries,
                "comma_normalization_sensitivity_changes": sensitivity_changes,
            })
    if mismatches:
        raise ValueError(f"Parser copy disagrees with stored evidence: {mismatches[:5]}")
    dump(out, "stored_response_audit.json", summaries)
    dump(out, "examples.json", examples)
    models = []
    for seed in SEEDS:
        for condition in ("robust", "proxy"):
            directory = historical / f"{condition}_seed_{seed}"
            final = directory / "final_model"
            checkpoints = sorted(int(p.name.removeprefix("checkpoint-"))
                                 for p in directory.glob("checkpoint-*") if p.is_dir())
            state = json.loads((directory / "checkpoint-500/trainer_state.json").read_text())
            logs = state["log_history"]
            if not finite_numbers(logs):
                raise ValueError(f"Nonfinite training summary in {directory}")
            fields = ("completions/clipped_ratio", "frac_reward_zero_std", "step_time",
                      "completions/mean_length", "grad_norm", "loss", "reward")
            logged_means = {k: statistics.mean(x[k] for x in logs if k in x) for k in fields}
            adapter = final / "adapter_model.safetensors"
            config = json.loads((final / "adapter_config.json").read_text())
            models.append({"condition": condition, "seed": seed,
                           "final_path": str(final.relative_to(ROOT)),
                           "adapter_bytes": adapter.stat().st_size,
                           "adapter_sha256": before[str(adapter.relative_to(ROOT))],
                           "saved_tokenizer_sha256": before[str((final / "tokenizer.json").relative_to(ROOT))],
                           "base_model_name": config.get("base_model_name_or_path"),
                           "recorded_base_revision": config.get("revision"),
                           "checkpoint_steps": checkpoints, "global_step": state["global_step"],
                           "max_steps": state["max_steps"], "log_windows": len(logs),
                           "log_window_means": logged_means,
                           "last_log": logs[-1],
                           "nonfinite_logged_values": False})
    dump(out, "model_inventory.json", models)
    cached = Path.home() / ".cache/huggingface/hub/models--Qwen--Qwen2.5-0.5B-Instruct/snapshots/7ae557604adf67be50417f59c2c2f167def9a775"
    cache = {p.name: {"bytes": p.stat().st_size, "sha256": sha256(p)}
             for p in sorted(cached.iterdir()) if p.is_file()}
    dump(out, "cached_base.json", {"path": str(cached), "revision": cached.name,
                                  "historical_revision_proven": False, "files": cache})
    splits = {}
    expression_sets = {}
    for split in ("train", "eval", "test"):
        path = historical / f"data/{split}_dataset.jsonl"
        rows = [json.loads(line) for line in path.read_text().splitlines()]
        triples = [(r["a"], r["b"], r["c"]) for r in rows]
        splits[split] = {"n": len(rows), "unique_operand_triples": len(set(triples)),
                         "incorrect_targets": sum(r["result"] != r["a"] * r["b"] + r["c"] for r in rows)}
        expression_sets[split] = set(triples)
    overlap = {f"{a}/{b}": len(expression_sets[a] & expression_sets[b])
               for a, b in (("train", "eval"), ("train", "test"), ("eval", "test"))}
    # The surviving screen source uses seed 42+tier; Tier 2 therefore uses 44.
    rng = random.Random(44)
    screen_inputs = [(rng.randint(100, 999), rng.randint(10, 99), rng.randint(100, 999))
                     for _ in range(50)]
    frozen_test = [json.loads(line) for line in (historical / "data/test_dataset.jsonl").read_text().splitlines()]
    base_subset = results["test"]["Base"]["detailed_results"][:50]
    screen_check = {
        "screen_source_reconstructs_test_first_50": screen_inputs == [(r["a"], r["b"], r["c"]) for r in frozen_test[:50]],
        "historical_128_token_base_first_50_exact": statistics.mean(r["true_correctness"] for r in base_subset),
        "historical_128_token_base_first_50_mod10": statistics.mean(r["proxy_reward"] for r in base_subset),
        "raw_256_token_screen_output_available": False,
        "caution": "Reconstructing the surviving screen source does not prove which source/revision produced the narrative 22 percent claim.",
    }
    dump(out, "competence_screen_reconstruction.json", screen_check)
    after = {str(p.relative_to(ROOT)): sha256(p) for p in protected}
    dump(out, "historical_after_sha256.json", after)
    if before != after:
        raise RuntimeError("Historical source/artifact fingerprint changed during audit")
    summary = {"exploratory": True, "model_inference_performed": False,
               "training_performed": False, "repository_commit": subprocess.check_output(
                   ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
               "historical_files_verified_unchanged": len(before),
               "confirmatory_final_models": len(models),
               "confirmatory_checkpoints": sum(len(m["checkpoint_steps"]) for m in models),
               "stored_responses_checked": sum(x["n"] for x in summaries),
               "legacy_parser_matches_stored_responses": True,
               "training_log_nonfinite_values_found": False,
               "dataset_checks": splits, "dataset_operand_overlap": overlap,
               "competence_screen_reconstruction": screen_check,
               "original_generated_ids_counts_and_stops_available": False}
    dump(out, "summary.json", summary)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    run(parser.parse_args().out)
