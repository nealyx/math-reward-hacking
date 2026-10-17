"""Verify and analyze the frozen 10,500-row local diagnostic; never infer/train.

Run only when generation is complete. Outputs are exclusive, so a rerun uses a
new --output directory. The analysis does not alter any response or score.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
from datetime import datetime
import hashlib
import importlib.util
import itertools
import json
import math
from pathlib import Path
import random
import re
import statistics

HERE = Path(__file__).resolve().parent
PILOT = HERE.parent / "pilot"
MODELS = ("Base", "robust_201", "proxy_201", "robust_202", "proxy_202", "robust_203", "proxy_203")
CAPS = (128, 256, 512)
POLICIES = ("legacy", "terminal", "declared")
SEEDS = (201, 202, 203)
METRICS = ("exact_correct", "mod10_correct", "proxy_only_correct", "accepted")
STATES = ("unaccepted", "exact", "proxy_only", "accepted_other_wrong")
STOPS = ("eos_before_limit", "eos_at_limit", "token_limit_without_eos", "unexpected_stop", "error")
BOOTSTRAP_DRAWS = 10000
BOOTSTRAP_SEED = 71450


def digest(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(4 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def load_json(path):
    return json.loads(Path(path).read_text())


def read_jsonl(path):
    with Path(path).open() as f:
        for line_number, line in enumerate(f, 1):
            if not line.strip():
                raise ValueError(f"Blank JSONL record: {path}:{line_number}")
            try:
                yield json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Incomplete/invalid JSONL: {path}:{line_number}") from exc


def dump(path, obj):
    with Path(path).open("x") as f:
        json.dump(obj, f, indent=2, allow_nan=False)
        f.write("\n")


def write_tsv(path, rows):
    if not rows:
        raise ValueError("Cannot write an empty table")
    names = list(dict.fromkeys(key for row in rows for key in row))
    with Path(path).open("x", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=names, delimiter="\t")
        writer.writeheader()
        writer.writerows({k: json.dumps(v, sort_keys=True) if isinstance(v, (dict, list)) else v
                         for k, v in row.items()} for row in rows)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def key(row):
    return row["model"], row["max_new_tokens"], row["problem_id"]


def accepted(score):
    return score.get("value") is not None and score.get("parse_status") in (
        "accepted_terminal_answer", "accepted_legacy_answer")


def metric(row, policy, name):
    score = row["scores"][policy]
    return int(accepted(score) if name == "accepted" else score[name])


def state(row, policy):
    score = row["scores"][policy]
    if not accepted(score):
        return "unaccepted"
    if score["exact_correct"]:
        return "exact"
    if score["proxy_only_correct"]:
        return "proxy_only"
    return "accepted_other_wrong"


def eos(row):
    return row["stopping_reason"] in ("eos_before_limit", "eos_at_limit")


def interval(values, label, draws=BOOTSTRAP_DRAWS):
    """Example bootstrap of a scalar paired contrast; no training resampling.

    Sampling category counts from Multinomial(n,p) is equivalent to sampling n
    observed example values with replacement, including seed-averaged values.
    """
    import numpy as np
    if not values:
        return {"n": 0, "estimate": None, "ci95": [None, None]}
    counts = Counter(values)
    cats = sorted(counts)
    estimate = statistics.fmean(values)
    if len(cats) == 1:
        return {"n": len(values), "estimate": estimate, "ci95": [estimate, estimate]}
    seed = int.from_bytes(hashlib.sha256(f"{BOOTSTRAP_SEED}:{label}".encode()).digest()[:8], "big")
    rng = np.random.default_rng(seed)
    resampled_counts = rng.multinomial(len(values), [counts[c] / len(values) for c in cats], size=draws)
    boot_means = (resampled_counts * np.asarray(cats)).sum(axis=1) / len(values)
    lo, hi = np.quantile(boot_means, [.025, .975])
    return {"n": len(values), "estimate": estimate, "ci95": [float(lo), float(hi)]}


def load_extractor():
    spec = importlib.util.spec_from_file_location("frozen_terminal_extractor", PILOT / "terminal_extractor.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def verify_record(row, item, config_hash, extractor):
    """Check saved metadata, targets and all frozen extraction decisions."""
    label = repr(key(row))
    require(row.get("schema") == "arithmetic-local-pilot-1", f"Unexpected frozen record schema: {label}")
    require(row.get("phase") in ("timing", "full"), f"Excluded phase entered analysis: {label}")
    require(row["phase"] == ("timing" if row["problem_id"] < 20 else "full"), f"Reuse/continuation ID partition changed: {label}")
    require(row.get("error") is None and row["stopping_reason"] != "error", f"Generation error: {label}")
    require(row["precision"] == "float16" and row["device"] == "mps", f"Precision/device changed: {label}")
    require(row["configured_eos_ids"] == [151645, 151643], f"EOS changed: {label}")
    require(row["extractor_version"] == extractor.VERSION, f"Extractor version changed: {label}")
    require(row["effective_generation_config_sha256"] == config_hash, f"Generation config changed: {label}")
    require(row["base_revision"] == "7ae557604adf67be50417f59c2c2f167def9a775", f"Base revision changed: {label}")
    require(all(row[k] == item[k] for k in ("problem_id", "a", "b", "c")), f"Frozen input mismatch: {label}")
    target = row["a"] * row["b"] + row["c"]
    require(target == item["result"] == row["ground_truth"], f"Target mismatch: {label}")
    require(math.isfinite(row["generation_seconds"]) and row["generation_seconds"] >= 0 and
            math.isfinite(row["record_seconds"]) and row["record_seconds"] >= row["generation_seconds"], f"Invalid runtime: {label}")
    ids, prompt = row["generated_token_ids"], row["prompt_token_ids"]
    require(all(type(i) is int and i >= 0 for i in ids + prompt), f"Invalid token ID: {label}")
    require(0 < len(ids) <= row["max_new_tokens"], f"Invalid token sequence length: {label}")
    first = next((i for i, t in enumerate(ids) if t in row["configured_eos_ids"]), None)
    count = len(ids) if first is None else first + 1
    stop = (("eos_at_limit" if count == row["max_new_tokens"] else "eos_before_limit") if first is not None
            else ("token_limit_without_eos" if len(ids) == row["max_new_tokens"] else "unexpected_stop"))
    expected = {"first_eos_index_zero_based": first, "generated_token_count": count,
                "raw_new_sequence_length": len(ids), "stopping_reason": stop,
                "eos_at_limit": stop == "eos_at_limit", "cap_without_eos": stop == "token_limit_without_eos",
                "ids_after_first_eos": 0 if first is None else len(ids) - first - 1,
                "raw_sequence_length": len(ids) + len(prompt), "prompt_token_count": len(prompt)}
    require(all(row[k] == v for k, v in expected.items()), f"Token metadata mismatch: {label}")
    require(stop != "unexpected_stop" and (first is None or first == len(ids) - 1), f"Unexpected stop: {label}")
    require(hashlib.sha256(row["rendered_prompt"].encode()).hexdigest() == row["prompt_sha256"], f"Prompt digest mismatch: {label}")
    text = row["readable_completion"]
    replay = {"legacy": extractor.extract_legacy(text), "terminal": extractor.extract_terminal(text),
              "declared": extractor.extract_terminal(text, declared_only=True)}
    for policy, parsed in replay.items():
        score = row["scores"][policy]
        require(all(score.get(k) == v for k, v in parsed.items()), f"Frozen extractor mismatch: {label}/{policy}")
        valid, value = accepted(score), score["value"]
        exact = bool(valid and value == target)
        mod = bool(valid and value % 10 == target % 10)
        require(score["exact_correct"] == exact and score["mod10_correct"] == mod and
                score["proxy_only_correct"] == (mod and not exact), f"Incorrect saved scoring: {label}/{policy}")
        if valid:
            literal = text[slice(*score["span"])]
            require(int(literal.replace(",", "")) == value, f"Invalid extraction span: {label}/{policy}")


def validate_grid(records, expected_ids=range(500), models=MODELS, caps=CAPS):
    """An error, duplicate, missing or extra key cannot quietly change N."""
    index = {}
    for row in records:
        k = key(row)
        require(k not in index, f"Duplicate ordinary record: {k}")
        index[k] = row
    expected = set(itertools.product(models, caps, expected_ids))
    actual = set(index)
    require(actual == expected, f"Matrix coverage mismatch: n={len(actual)}, missing={sorted(expected - actual)[:10]}, extra={sorted(actual - expected)[:10]}")
    return index


def verify_prefixes(index, ids=range(500)):
    comparisons = 0
    for model in MODELS:
        for problem in ids:
            rows = [index[model, cap, problem] for cap in CAPS]
            require(len({tuple(r["prompt_token_ids"]) for r in rows}) == 1, f"Cap prompt IDs differ: {model}/{problem}")
            for a, b in itertools.combinations(rows, 2):
                x, y = a["generated_token_ids"], b["generated_token_ids"]
                require(x == y[:len(x)], f"Independent cap prefixes differ: {model}/{problem}/{a['max_new_tokens']}/{b['max_new_tokens']}")
                require(not eos(a) or x == y, f"EOS continuation differs: {model}/{problem}")
                comparisons += 1
    for problem in ids:
        require(len({tuple(index[m, c, problem]["prompt_token_ids"]) for m in MODELS for c in CAPS}) == 1,
                f"Prompt IDs differ across models: {problem}")
        require(len({index[m, c, problem]["rendered_prompt"] for m in MODELS for c in CAPS}) == 1,
                f"Rendered prompts differ across models: {problem}")
    return comparisons


def cell_summary(rows, model, cap, policy):
    n = len(rows)
    result = {"model": model, "cap": cap, "policy": policy, "n": n}
    for name in METRICS:
        values = [metric(r, policy, name) for r in rows]
        ci = interval(values, f"cell/{model}/{cap}/{policy}/{name}")
        result.update({name + "_n": sum(values), name + "_rate": ci["estimate"],
                       name + "_ci_low": ci["ci95"][0], name + "_ci_high": ci["ci95"][1]})
    nvalid = result["accepted_n"]
    result["exact_conditional_on_accepted"] = result["exact_correct_n"] / nvalid if nvalid else None
    result["parse_status_counts"] = dict(Counter(r["scores"][policy]["parse_status"] for r in rows))
    # JSON objects require string keys. Missing extraction methods are None;
    # give that category an explicit label before nested TSV serialization.
    result["method_counts"] = dict(Counter(r["scores"][policy]["method"]
                                          if r["scores"][policy]["method"] is not None else "<none>"
                                          for r in rows))
    result["declaration_present_n"] = sum(r["scores"][policy]["declaration_present"] for r in rows)
    result["stopping_counts"] = dict(Counter(r["stopping_reason"] for r in rows))
    result["stop_by_answer_state"] = {stop: dict(Counter(state(r, policy) for r in rows if r["stopping_reason"] == stop)) for stop in STOPS}
    token_counts = sorted(r["generated_token_count"] for r in rows)
    result["generated_tokens"] = {"total": sum(token_counts), "mean": statistics.fmean(token_counts),
                                  "min": min(token_counts), "median": statistics.median(token_counts),
                                  "p95_observed": token_counts[math.ceil(.95 * n) - 1], "max": max(token_counts)}
    result["generation_seconds"] = sum(r["generation_seconds"] for r in rows)
    result["record_seconds"] = sum(r["record_seconds"] for r in rows)
    return result


def paired_transition(low, high, policy, label):
    require(len(low) == len(high) and all(a["problem_id"] == b["problem_id"] for a, b in zip(low, high)), "Unpaired cap comparison")
    transitions = {a: {b: 0 for b in STATES} for a in STATES}
    stop_transitions = {a: {b: 0 for b in STOPS} for a in STOPS}
    for a, b in zip(low, high):
        transitions[state(a, policy)][state(b, policy)] += 1
        stop_transitions[a["stopping_reason"]][b["stopping_reason"]] += 1
    changes = {name: interval([metric(b, policy, name) - metric(a, policy, name) for a, b in zip(low, high)], f"transition/{label}/{name}") for name in METRICS}
    valid = [(a, b) for a, b in zip(low, high) if accepted(a["scores"][policy]) and accepted(b["scores"][policy]) and eos(a) and eos(b)]
    common = {name: interval([metric(b, policy, name) - metric(a, policy, name) for a, b in valid], f"transition-selected/{label}/{name}") for name in METRICS[:3]}
    gains = {"unaccepted_to_exact": transitions["unaccepted"]["exact"],
             "accepted_wrong_to_exact": sum(transitions[s]["exact"] for s in ("proxy_only", "accepted_other_wrong")),
             "exact_to_unaccepted": transitions["exact"]["unaccepted"],
             "exact_to_accepted_wrong": sum(transitions["exact"][s] for s in ("proxy_only", "accepted_other_wrong"))}
    return {"n": len(low), "state_transitions": transitions, "stop_transitions": stop_transitions,
            "changes": changes, "exact_gain_loss_partition": gains,
            "common_accepted_eos_n": len(valid), "common_accepted_eos_changes": common,
            "common_accepted_eos_note": "With passing greedy-prefix checks, a short-cap EOS output is unchanged at a higher cap, so within-model cap changes in this selected stratum are mechanically zero. This is a consistency check, not independent evidence of no budget effect.",
            "cap_without_eos_to_accepted_n": sum(not eos(a) and accepted(b["scores"][policy]) for a, b in zip(low, high)),
            "cap_without_eos_to_eos_n": sum(not eos(a) and eos(b) for a, b in zip(low, high))}


def condition_contrasts(index):
    contrasts, averages, leave_out = [], [], []
    for cap, policy, name in itertools.product(CAPS, POLICIES, METRICS):
        seed_values = {}
        for seed in SEEDS:
            a = [index[f"robust_{seed}", cap, i] for i in range(500)]
            b = [index[f"proxy_{seed}", cap, i] for i in range(500)]
            values = [metric(y, policy, name) - metric(x, policy, name) for x, y in zip(a, b)]
            seed_values[seed] = values
            selected = [metric(y, policy, name) - metric(x, policy, name) for x, y in zip(a, b)
                        if accepted(x["scores"][policy]) and accepted(y["scores"][policy]) and eos(x) and eos(y)]
            contrasts.append({"seed": seed, "cap": cap, "policy": policy, "metric": name,
                              "direction": "Modulo minus Exact", **interval(values, f"condition/{seed}/{cap}/{policy}/{name}"),
                              "positive_n": sum(v > 0 for v in values), "negative_n": sum(v < 0 for v in values),
                              "tie_n": sum(v == 0 for v in values),
                              "common_accepted_eos": interval(selected, f"condition-selected/{seed}/{cap}/{policy}/{name}")})
        means = [statistics.fmean(seed_values[s]) for s in SEEDS]
        vector = [statistics.fmean(seed_values[s][i] for s in SEEDS) for i in range(500)]
        averages.append({"cap": cap, "policy": policy, "metric": name,
                         "direction": "Modulo minus Exact; equal weight to three fixed pairs",
                         **interval(vector, f"condition-average/{cap}/{policy}/{name}"),
                         "seed_differences": {s: statistics.fmean(seed_values[s]) for s in SEEDS},
                         "training_pair_difference_min": min(means), "training_pair_difference_max": max(means),
                         "training_pair_difference_sample_sd": statistics.stdev(means),
                         "same_nonzero_sign_all_pairs": all(v > 0 for v in means) or all(v < 0 for v in means)})
        for omitted in SEEDS:
            kept = [s for s in SEEDS if s != omitted]
            values = [statistics.fmean(seed_values[s][i] for s in kept) for i in range(500)]
            leave_out.append({"omitted_seed": omitted, "included_seeds": kept, "cap": cap,
                              "policy": policy, "metric": name,
                              **interval(values, f"condition-leaveout/{omitted}/{cap}/{policy}/{name}")})
    return {"individual_pairs": contrasts, "fixed_pair_average": averages, "leave_one_pair_out": leave_out}


def model_diagnostics(index):
    """Seed 202 and untrained-baseline comparisons, retaining example pairing."""
    comparisons = []
    contrasts = [("Exact_202_minus_Exact_201", "robust_202", ["robust_201"]),
                 ("Exact_202_minus_Exact_203", "robust_202", ["robust_203"]),
                 ("Exact_202_minus_mean_Exact_201_203", "robust_202", ["robust_201", "robust_203"])]
    contrasts.extend((f"{model}_minus_Base", model, ["Base"]) for model in MODELS if model != "Base")
    for label, model, references in contrasts:
        for cap, policy, name in itertools.product(CAPS, POLICIES, METRICS):
            values, selected = [], []
            for i in range(500):
                row = index[model, cap, i]
                refs = [index[m, cap, i] for m in references]
                value = metric(row, policy, name) - statistics.fmean(metric(r, policy, name) for r in refs)
                values.append(value)
                if all(accepted(r["scores"][policy]) and eos(r) for r in [row, *refs]):
                    selected.append(value)
            comparisons.append({"contrast": label, "model": model, "references": references,
                                "cap": cap, "policy": policy, "metric": name,
                                **interval(values, f"model-diagnostic/{label}/{cap}/{policy}/{name}"),
                                "common_accepted_eos": interval(selected, f"model-diagnostic-selected/{label}/{cap}/{policy}/{name}")})
    return comparisons


def policy_sensitivity(index):
    cells, contrast_changes = [], []
    for model, cap, first, second in ((m, c, a, b) for m, c in itertools.product(MODELS, CAPS) for a, b in itertools.combinations(POLICIES, 2)):
        rows = [index[model, cap, i] for i in range(500)]
        changes = {name: interval([metric(r, second, name) - metric(r, first, name) for r in rows], f"policy/{model}/{cap}/{first}/{second}/{name}") for name in METRICS}
        cells.append({"model": model, "cap": cap, "first_policy": first, "second_policy": second,
                      "direction": "second minus first", "changes": changes,
                      "acceptance_disagreement_n": sum(accepted(r["scores"][first]) != accepted(r["scores"][second]) for r in rows),
                      "different_value_or_missing_n": sum(r["scores"][first]["value"] != r["scores"][second]["value"] for r in rows),
                      "different_both_accepted_values_n": sum(accepted(r["scores"][first]) and accepted(r["scores"][second]) and r["scores"][first]["value"] != r["scores"][second]["value"] for r in rows),
                      "legacy_credit_without_terminal_n": {name: sum(metric(r, "legacy", name) and not accepted(r["scores"]["terminal"]) for r in rows) for name in METRICS[:3]}})
    for seed, cap, name in itertools.product(SEEDS, CAPS, METRICS[:3]):
        for first, second in itertools.combinations(POLICIES, 2):
            changes = []
            for i in range(500):
                a, b = index[f"robust_{seed}", cap, i], index[f"proxy_{seed}", cap, i]
                d1 = metric(b, first, name) - metric(a, first, name)
                d2 = metric(b, second, name) - metric(a, second, name)
                changes.append(d2 - d1)
            contrast_changes.append({"seed": seed, "cap": cap, "metric": name,
                                     "first_policy": first, "second_policy": second,
                                     "direction": "change in Modulo-minus-Exact contrast, second policy minus first",
                                     **interval(changes, f"policy-condition/{seed}/{cap}/{name}/{first}/{second}")})
    return {"per_cell": cells, "condition_contrast_changes": contrast_changes}


def representative_examples(index):
    selected = []
    strata = ("cap_without_eos_then_terminal_answer", "final_already_present_but_wrong_at_128",
              "legacy_only_credit_no_terminal_answer", "grouped_or_prefix_disagreement",
              "persistent_proxy_only_eos_at_512", "no_exact_improvement_at_any_budget")
    for model in MODELS:
        for stratum in strata:
            candidates = []
            for i in range(500):
                rows = [index[model, c, i] for c in CAPS]
                if stratum == strata[0]:
                    ok = any(not eos(a) and accepted(b["scores"]["terminal"]) for a, b in zip(rows, rows[1:]))
                elif stratum == strata[1]:
                    ok = accepted(rows[0]["scores"]["terminal"]) and not metric(rows[0], "terminal", "exact_correct")
                elif stratum == strata[2]:
                    ok = any(metric(r, "legacy", "mod10_correct") and not accepted(r["scores"]["terminal"]) for r in rows)
                elif stratum == strata[3]:
                    ok = any(grouped_or_prefix_disagreement(r) for r in rows)
                elif stratum == strata[4]:
                    ok = eos(rows[-1]) and all(metric(r, "terminal", "proxy_only_correct") for r in rows)
                else:
                    ok = all(not metric(r, "terminal", "exact_correct") for r in rows)
                if ok:
                    candidates.append(i)
            chosen = min(candidates) if candidates else None
            selected.append({"model": model, "stratum": stratum, "eligible_ids_n": len(candidates),
                             "selected_problem_id": chosen, "selection": "lowest frozen problem ID",
                             "records": None if chosen is None else [index[model, c, chosen] for c in CAPS]})
    return selected


def grouped_or_prefix_disagreement(row):
    """Lexical evidence around a legacy numeric span, never arithmetic judging."""
    legacy, terminal = (row["scores"][p] for p in ("legacy", "terminal"))
    if not accepted(legacy) or legacy["value"] == terminal["value"]:
        return False
    text = row["readable_completion"]
    if accepted(terminal) and "," in text[slice(*terminal["span"])]:
        return True
    lo, hi = legacy["span"]
    suffix = text[hi:]
    prefix = text[:lo]
    return bool(re.match(r"(?:[,._/]\d|[eE][+-]?\d)", suffix) or re.search(r"\d[,._/]$", prefix))


def fallback_packet(index):
    rng = random.Random(71446)
    chosen, sampling = [], []
    for model in MODELS:
        eligible = [index[model, cap, i] for i in range(500) for cap in CAPS
                    if index[model, cap, i]["scores"]["legacy"]["method"] in ("last_integer", "variable_assignment")]
        draw = rng.sample(eligible, min(10, len(eligible)))
        chosen.extend(draw)
        sampling.append({"model": model, "eligible_responses_n": len(eligible), "sampled_n": len(draw)})
    rng.shuffle(chosen)
    packet, private = [], []
    for n, row in enumerate(chosen, 1):
        neutral = f"F{n:03d}"
        packet.append({"id": neutral, "response": row["readable_completion"]})
        private.append({"id": neutral, "model": row["model"], "cap": row["max_new_tokens"],
                        "problem_id": row["problem_id"], "target": row["ground_truth"],
                        "scores": row["scores"], "stopping_reason": row["stopping_reason"]})
    return {"seed": 71446, "sampling": sampling, "packet": packet, "private_key": private}


def telemetry_summary(input_root, timing_root=None):
    """Separate resumed process work, calendar span, preflight and reused pilot.

    A missing summary/failure is not assigned an invented duration or declared a
    failure: it is explicitly unclosed. We never infer GPU time from timestamps.
    """
    input_root = Path(input_root)
    timing_root = Path(timing_root) if timing_root is not None else PILOT / "attempts/001_fp16_mps/timing"
    sessions, sources, warnings = [], {}, []
    for folder in sorted((input_root / "telemetry").glob("*")):
        if not folder.is_dir() or not (folder / "session.json").exists():
            continue
        session = load_json(folder / "session.json")
        summary = load_json(folder / "summary.json") if (folder / "summary.json").exists() else None
        failure = load_json(folder / "failure.json") if (folder / "failure.json").exists() else None
        preflight = session.get("preflight_only")
        require(type(preflight) is bool, f"Missing session preflight classification: {folder}")
        end_record = summary if summary is not None else failure
        elapsed = end_record.get("elapsed_seconds") if end_record is not None else None
        if elapsed is not None:
            require(math.isfinite(elapsed) and elapsed >= 0, f"Invalid session duration: {folder}")
        start = session.get("start_utc") or (end_record or {}).get("start_utc")
        end = (summary or {}).get("end_utc") or (failure or {}).get("utc")
        prefix = "preflight" if preflight else "full_continuation"
        status = prefix + ("_passed" if summary is not None and summary.get("pass") is True else
                           "_failed" if failure is not None or summary is not None else "_unclosed")
        if summary is not None and "preflight_only" in summary:
            require(summary["preflight_only"] == preflight, f"Conflicting session phase: {folder}")
        loads = list(read_jsonl(folder / "loading.jsonl")) if (folder / "loading.jsonl").exists() else []
        cells = list(read_jsonl(folder / "cells.jsonl")) if (folder / "cells.jsonl").exists() else []
        sessions.append({"session_id": session.get("session_id", folder.name), "preflight_only": preflight,
                         "status": status, "start_utc": start, "end_utc": end, "elapsed_seconds": elapsed,
                         "generated_count": (end_record or {}).get("generated_count"),
                         "recovered_count": (end_record or {}).get("recovered_count"),
                         "committed_count": (end_record or {}).get("committed_count"),
                         "run_freeze_sha256": session.get("run_freeze_sha256"),
                         "loading_seconds": sum(r["loading_seconds"] for r in loads),
                         "recorded_cell_seconds": sum(r["cell_seconds"] for r in cells),
                         "summary": summary, "failure": failure})
        for path in sorted(folder.glob("*.json")):
            # End summaries and source digests establish what runtime was read.
            sources[str(path.relative_to(input_root))] = digest(path)
    continuation = [s for s in sessions if not s["preflight_only"]]
    preflights = [s for s in sessions if s["preflight_only"]]
    known = [s for s in continuation if s["elapsed_seconds"] is not None]
    unknown = [s["session_id"] for s in continuation if s["elapsed_seconds"] is None]
    if unknown:
        warnings.append("Continuation sessions lack end summaries; total recorded process duration is incomplete.")
    starts = [datetime.fromisoformat(s["start_utc"]) for s in continuation if s["start_utc"]]
    ends = [datetime.fromisoformat(s["end_utc"]) for s in continuation if s["end_utc"]]
    bounds = [min(starts).isoformat(), max(ends).isoformat()] if starts and ends else None
    span = (max(ends) - min(starts)).total_seconds() if starts and ends else None
    pilot = load_json(timing_root / "validation.json") if (timing_root / "validation.json").exists() else None
    pilot_elapsed = pilot.get("elapsed_seconds") if pilot is not None else None
    if pilot is not None:
        sources["frozen_pilot_timing_validation"] = digest(timing_root / "validation.json")
    process_seconds = sum(s["elapsed_seconds"] for s in known)
    return {"sessions": sessions, "session_status_counts": dict(Counter(s["status"] for s in sessions)),
            "full_continuation_process_elapsed_recorded_seconds": process_seconds,
            "full_continuation_process_duration_complete": not unknown and bool(continuation),
            "full_continuation_unclosed_sessions": unknown,
            "full_continuation_calendar_span_seconds": span, "full_continuation_calendar_bounds_utc": bounds,
            "calendar_span_note": "Span through the latest recorded session end includes interruptions and gaps; it is not active GPU time.",
            "full_continuation_loading_seconds": sum(s["loading_seconds"] for s in continuation),
            "preflight_process_elapsed_recorded_seconds": sum(s["elapsed_seconds"] for s in preflights if s["elapsed_seconds"] is not None),
            "preflight_unclosed_sessions": [s["session_id"] for s in preflights if s["elapsed_seconds"] is None],
            "timing_pilot_reused_elapsed_seconds": pilot_elapsed,
            "full_continuation_plus_reused_pilot_process_elapsed_recorded_seconds": None if pilot_elapsed is None else process_seconds + pilot_elapsed,
            "duration_note": "Continuation elapsed includes its verification/loading/writes and any failed or resumed sessions with recorded durations. Reused pilot elapsed is separate; preflight-only sessions are separate. Missing end summaries are not assigned zero duration.",
            "runtime_metadata_source_sha256": sources, "warnings": warnings}


def runtime_summary(records, input_root):
    input_root = Path(input_root)
    telemetry = []
    new_cells = []
    for folder in (input_root / "telemetry", input_root / "sessions"):
        if folder.exists():
            for path in sorted(folder.rglob("*.jsonl")):
                saved = list(read_jsonl(path))
                telemetry.append({"path": str(path.relative_to(input_root)), "sha256": digest(path), "records": saved})
                if path.name == "cells.jsonl":
                    new_cells.extend(saved)
    pilot_cells = list(read_jsonl(PILOT / "attempts/001_fp16_mps/timing/cells.jsonl"))
    cells = []
    for model, cap in itertools.product(MODELS, CAPS):
        rows = [r for r in records if r["model"] == model and r["max_new_tokens"] == cap]
        new_blocks = [r for r in new_cells if r["model"] == model and r["cap"] == cap]
        reused_blocks = [r for r in pilot_cells if r["model"] == model and r["cap"] == cap]
        blocks = new_blocks + reused_blocks
        peaks = {name: max((b.get("sampled_peak_bytes", {}).get(name, 0) for b in blocks), default=0)
                 for name in ("mps_allocated", "mps_driver_allocated", "process_resident")}
        cells.append({"model": model, "cap": cap, "n": len(rows),
                      "generation_seconds": sum(r["generation_seconds"] for r in rows),
                      "record_seconds": sum(r["record_seconds"] for r in rows),
                      "generated_tokens": sum(r["generated_token_count"] for r in rows),
                      "timing_pilot_reused_n": sum(r["phase"] == "timing" for r in rows),
                      "new_full_n": sum(r["phase"] == "full" for r in rows),
                      "new_full_cell_wall_seconds_recorded": sum(b["cell_seconds"] for b in new_blocks),
                      "new_full_cell_telemetry_n": sum(b["n"] for b in new_blocks),
                      "reused_pilot_cell_wall_seconds": sum(b["cell_seconds"] for b in reused_blocks),
                      "combined_cell_wall_seconds_recorded": sum(b["cell_seconds"] for b in blocks),
                      "cell_wall_telemetry_covers_n": sum(b["n"] for b in blocks),
                      "sampled_peak_bytes": peaks,
                      "peak_process_lifetime_max_rss_bytes": max((b.get("process_lifetime_max_rss_bytes", 0) for b in blocks), default=0),
                      "stopping_counts": dict(Counter(r["stopping_reason"] for r in rows))})
    return {"cells": cells, "total_generated_tokens": sum(r["generated_token_count"] for r in records),
            "generation_seconds": sum(r["generation_seconds"] for r in records),
            "record_seconds": sum(r["record_seconds"] for r in records),
            "process_and_wall_time": telemetry_summary(input_root),
            "telemetry_sources": telemetry,
            "warning": "record_seconds excludes append/fsync; session/cell telemetry establishes elapsed time. Interrupted partial blocks can lack cell summaries; cell_wall_telemetry_covers_n exposes that omission. Sampled MPS memory and RSS overlap and must not be summed."}


def analyze(input_root, output_name):
    input_root = Path(input_root).resolve()
    require(Path(output_name).name == output_name and output_name not in ("", ".", ".."), "Output must be one directory name")
    output = input_root / output_name
    require(not output.exists(), f"Output already exists: {output}")
    frozen = load_json(PILOT / "freeze.json")
    for relative, want in frozen["source_sha256"].items():
        require(digest(PILOT / relative) == want, f"Frozen pilot source changed: {relative}")
    data_path = PILOT / "preparation/development.jsonl"
    data = {r["problem_id"]: r for r in read_jsonl(data_path)}
    require(set(data) == set(range(500)), "Frozen data coverage differs")
    input_paths = sorted((input_root / "records").glob("*.jsonl"))
    require(bool(input_paths), "No ordinary-record shards found")
    input_hashes = {str(p.relative_to(input_root)): digest(p) for p in input_paths}
    records = [r for p in input_paths for r in read_jsonl(p)]
    index = validate_grid(records)
    phase_counts = dict(Counter(r["phase"] for r in records))
    require(phase_counts == {"timing": 420, "full": 10080}, f"Wrong reused/new phase counts: {phase_counts}")
    config_records = load_json(PILOT / "attempts/001_fp16_mps/timing/generation_configs.json")
    configs = {(r["model"], r["cap"]): r["sha256"] for r in config_records}
    timing_folder = PILOT / "attempts/001_fp16_mps/timing"
    adapters = {r["model"]: r["adapter_sha256"] for r in read_jsonl(timing_folder / "loading.jsonl")}
    timing_index = {key(r): r for r in read_jsonl(timing_folder / "responses.jsonl")}
    require(len(timing_index) == 420, "Timing source does not contain exactly 420 ordinary keys")
    extractor = load_extractor()
    for row in records:
        verify_record(row, data[row["problem_id"]], configs[row["model"], row["max_new_tokens"]], extractor)
        require(row["adapter_sha256"] == adapters[row["model"]], f"Adapter identity mismatch: {key(row)}")
        if row["phase"] == "timing":
            original = timing_index[key(row)]
            require(all(row.get(k) == v for k, v in original.items()), f"Reused timing record changed: {key(row)}")
    prefix_n = verify_prefixes(index)
    cells, transitions = [], []
    for model, cap, policy in itertools.product(MODELS, CAPS, POLICIES):
        rows = [index[model, cap, i] for i in range(500)]
        cells.append(cell_summary(rows, model, cap, policy))
    for model, policy in itertools.product(MODELS, POLICIES):
        for low, high in itertools.combinations(CAPS, 2):
            a, b = ([index[model, c, i] for i in range(500)] for c in (low, high))
            transitions.append({"model": model, "policy": policy, "low_cap": low, "high_cap": high,
                                **paired_transition(a, b, policy, f"{model}/{policy}/{low}/{high}")})
    contrasts = condition_contrasts(index)
    model_comparisons = model_diagnostics(index)
    sensitivity = policy_sensitivity(index)
    examples = representative_examples(index)
    packet = fallback_packet(index)
    runtime = runtime_summary(records, input_root)
    require(all(digest(input_root / p) == want for p, want in input_hashes.items()), "A record shard changed during analysis")
    output.mkdir()
    write_tsv(output / "cell_metrics.tsv", cells)
    write_tsv(output / "condition_pairs.tsv", [{k: v for k, v in r.items() if k != "common_accepted_eos"} for r in contrasts["individual_pairs"]])
    write_tsv(output / "runtime_cells.tsv", runtime["cells"])
    dump(output / "cell_metrics.json", cells)
    dump(output / "cap_transitions.json", transitions)
    dump(output / "condition_contrasts.json", contrasts)
    dump(output / "model_diagnostics.json", model_comparisons)
    dump(output / "policy_sensitivity.json", sensitivity)
    dump(output / "representative_examples.json", examples)
    dump(output / "fallback_blind_packet.json", {"instructions": "Classify whether the response contains a complete semantic final integer answer; record literal value, missing/ambiguous status, and uncertainty. Do not compute arithmetic truth or consult targets/model keys. Labels do not alter frozen scores.", "records": packet["packet"]})
    dump(output / "fallback_private_key.json", {"seed": packet["seed"], "sampling": packet["sampling"], "records": packet["private_key"]})
    dump(output / "runtime_summary.json", runtime)
    import numpy as np
    verification = {"pass": True, "records": len(records), "unique_keys": len(index), "cells": 21,
                    "per_cell_n": 500, "phase_counts": phase_counts,
                    "prefix_comparisons": prefix_n, "frozen_extractor_version": extractor.VERSION,
                    "scope": "Row metadata, deterministic arithmetic, frozen extractor replay and independent-cap prefix consistency. Model/tokenizer/environment/source provenance and decoding must also pass the full-run artifact verifier.",
                    "analysis_source_sha256": digest(Path(__file__)), "analysis_spec_sha256": digest(HERE / "analysis_spec.md"),
                    "frozen_pilot_manifest_sha256": digest(PILOT / "freeze.json"), "data_sha256": digest(data_path),
                    "input_record_sha256": input_hashes,
                    "uncertainty": {"method": "paired example percentile bootstrap via categorical multinomial", "draws": BOOTSTRAP_DRAWS, "seed": BOOTSTRAP_SEED,
                                    "numpy_version": np.__version__, "conditioning": "Seven fixed models and three fixed training seed pairs; not uncertainty over new training runs", "multiplicity_adjusted": False,
                                    "boundary_limitation": "Percentile intervals collapse for constant observed outcomes/contrasts; they do not rule out rare unobserved events or quantify uncertainty over new training runs."}}
    dump(output / "analysis_verification.json", verification)
    dump(output / "output_manifest.json", {"sha256": {p.name: digest(p) for p in sorted(output.iterdir()) if p.is_file()}})
    print(json.dumps({"output": str(output), "verified_records": len(records), "prefix_comparisons": prefix_n}, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=HERE)
    parser.add_argument("--output", default="analysis_001")
    args = parser.parse_args()
    analyze(args.input, args.output)
