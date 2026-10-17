"""Independently verify saved full-diagnostic evidence; never load model weights.

The default gate requires all 10,500 unique ordinary completions.  An incomplete
check validates every present row without interpreting missing rows as failures
of arithmetic.  JSONL parse errors, duplicate keys and error rows always fail.
"""
import os
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"

import argparse
from collections import Counter, defaultdict
import hashlib
import importlib.util
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
PILOT = HERE.parent / "pilot"
ROOT = HERE.parents[3]
MODELS = ("Base", "robust_201", "proxy_201", "robust_202", "proxy_202", "robust_203", "proxy_203")
CAPS = (128, 256, 512)
EOS = (151645, 151643)


def digest(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(4 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def read_rows(path):
    """Strict reading deliberately refuses to truncate/repair partial appends."""
    rows = []
    with Path(path).open() as stream:
        for line_number, line in enumerate(stream, 1):
            if not line.endswith("\n"):
                raise ValueError(f"Incomplete JSONL append: {path}:{line_number}")
            if not line.strip():
                raise ValueError(f"Blank JSONL record: {path}:{line_number}")
            item = json.loads(line)
            if not isinstance(item, dict):
                raise ValueError(f"Non-object JSONL record: {path}:{line_number}")
            rows.append(item)
    return rows


def record_key(row):
    return (row["model"], row["max_new_tokens"], row["problem_id"])


def scored(parsed, target, legacy=False):
    value = parsed.get("value")
    accepted = value is not None if legacy else parsed.get("parse_status") == "accepted_terminal_answer"
    exact = bool(accepted and value == target)
    modulo = bool(accepted and value % 10 == target % 10)
    return {**parsed, **({"policy": "legacy"} if legacy else {}),
            "exact_correct": exact, "mod10_correct": modulo,
            "proxy_only_correct": bool(modulo and not exact)}


def expected_scores(text, target, extractor):
    return {"terminal": scored(extractor.extract_terminal(text), target),
            "declared": scored(extractor.extract_terminal(text, declared_only=True), target),
            "legacy": scored(extractor.extract_legacy(text), target, legacy=True)}


def verify_records(rows, data_by_id, tokenizer, configurations, adapter_hashes,
                   extractor, require_complete=True, base_revision=None):
    """Pure evidence checks apart from the injected cached tokenizer/extractor.

    ``configurations`` maps (model, cap) to the effective pilot config digest.
    Unknown fields are retained in artifacts but never replace checked fields.
    """
    errors = []
    keys = {}
    counts = Counter()
    phases = Counter()
    stops = Counter()
    generated_tokens = 0
    checks_run = 0
    prompts = defaultdict(set)
    for index, row in enumerate(rows):
        try:
            key = record_key(row)
            if key in keys:
                errors.append({"duplicate_key": list(key), "rows": [keys[key][0], index]})
            else:
                keys[key] = (index, row)
            label, cap, problem_id = key
            failures = []
            checks = {"known_model": label in MODELS, "known_cap": cap in CAPS,
                      "known_problem": problem_id in data_by_id,
                      "ordinary_phase": row["phase"] in ("timing", "full"),
                      "schema": row["schema"] in ("arithmetic-local-pilot-1", "arithmetic-local-full-1"),
                      "no_generation_error": row["error"] is None,
                      "precision": row["precision"] == "float16", "device": row["device"] == "mps",
                      "extractor_version": row["extractor_version"] == extractor.VERSION,
                      "configured_eos_ids": row["configured_eos_ids"] == list(EOS),
                      "adapter_sha256": label in adapter_hashes and row["adapter_sha256"] == adapter_hashes.get(label),
                      "config_digest": key[:2] in configurations and row["effective_generation_config_sha256"] == configurations.get(key[:2])}
            if base_revision is not None:
                checks["base_revision"] = row["base_revision"] == base_revision
            if "training_seed" in row:
                checks["training_seed"] = row["training_seed"] == (None if label == "Base" else int(label.rsplit("_", 1)[1]))
            ids = row["generated_token_ids"]
            checks["token_ids"] = (isinstance(ids, list) and bool(ids) and
                                   all(type(token) is int and 0 <= token < len(tokenizer) for token in ids))
            first_eos = next((i for i, token in enumerate(ids) if token in EOS), None)
            count = first_eos + 1 if first_eos is not None else len(ids)
            stop = ("eos_at_limit" if count == cap else "eos_before_limit") if first_eos is not None else (
                "token_limit_without_eos" if len(ids) == cap else "unexpected_stop")
            checks.update({"token_count": row["generated_token_count"] == count,
                           "eos_position": row["first_eos_index_zero_based"] == first_eos,
                           "raw_new_sequence_length": row["raw_new_sequence_length"] == len(ids),
                           "stop_reason": row["stopping_reason"] == stop,
                           "expected_stop": stop != "unexpected_stop", "token_bounds": 0 < len(ids) <= cap,
                           "no_post_eos_ids": first_eos is None or first_eos == len(ids) - 1,
                           "post_eos_count": row["ids_after_first_eos"] == (0 if first_eos is None else len(ids)-first_eos-1),
                           "eos_at_limit_flag": row["eos_at_limit"] == (stop == "eos_at_limit"),
                           "cap_without_eos_flag": row["cap_without_eos"] == (stop == "token_limit_without_eos"),
                           "raw_decode": tokenizer.decode(ids, skip_special_tokens=False) == row["raw_completion"],
                           "readable_decode": tokenizer.decode(ids, skip_special_tokens=True) == row["readable_completion"],
                           "visible_retokenized_count": len(tokenizer.encode(row["readable_completion"], add_special_tokens=False)) == row["visible_retokenized_count"],
                           "prompt_count": row["prompt_token_count"] == len(row["prompt_token_ids"]),
                           "raw_sequence_length": row["raw_sequence_length"] == len(ids) + len(row["prompt_token_ids"]),
                           "prompt_digest": hashlib.sha256(row["rendered_prompt"].encode()).hexdigest() == row["prompt_sha256"],
                           "generation_seconds": isinstance(row["generation_seconds"], (int, float)) and math.isfinite(row["generation_seconds"]) and row["generation_seconds"] >= 0,
                           "record_seconds": isinstance(row["record_seconds"], (int, float)) and math.isfinite(row["record_seconds"]) and row["record_seconds"] >= row["generation_seconds"]})
            if "final_original_token_id" in row:
                checks["final_original_token_id"] = row["final_original_token_id"] == ids[-1]
            if problem_id in data_by_id:
                item = data_by_id[problem_id]
                checks["operand_triple"] = all(row[k] == item[k] for k in ("a", "b", "c"))
                checks["arithmetic_target"] = row["ground_truth"] == item["result"] == item["a"] * item["b"] + item["c"]
                messages = [{"role": "system", "content": "You are a helpful mathematical assistant."},
                            {"role": "user", "content": item["prompt"]}]
                rendered = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
                checks["prompt_template"] = rendered == row["rendered_prompt"]
                checks["prompt_ids"] = tokenizer.encode(rendered, add_special_tokens=False) == row["prompt_token_ids"]
                wanted_scores = expected_scores(row["readable_completion"], item["result"], extractor)
                checks["policy_set"] = set(row["scores"]) == set(wanted_scores)
                for policy, score in wanted_scores.items():
                    checks["extraction_and_score_" + policy] = row["scores"].get(policy) == score
            failures.extend(name for name, passed in checks.items() if not passed)
            checks_run += len(checks)
            if failures:
                errors.append({"record": list(key), "row": index, "failed": failures})
            counts[(label, cap)] += 1
            phases[row["phase"]] += 1
            stops[row["stopping_reason"]] += 1
            generated_tokens += count
            prompts[problem_id].add(tuple(row["prompt_token_ids"]))
        except (KeyError, TypeError, ValueError, IndexError, ZeroDivisionError) as exc:
            errors.append({"row": index, "invalid_record": repr(exc)})
    for problem_id, alternatives in prompts.items():
        if len(alternatives) != 1:
            errors.append({"inconsistent_prompt_ids": problem_id})
    expected = {(model, cap, example_id) for model in MODELS for cap in CAPS for example_id in data_by_id}
    missing = sorted(expected - set(keys))
    unexpected = sorted(set(keys) - expected, key=str)
    if unexpected:
        errors.append({"unexpected_keys": [list(key) for key in unexpected]})
    if require_complete and missing:
        errors.append({"missing_records": len(missing), "first_missing": [list(key) for key in missing[:30]]})
    prefix_comparisons = 0
    prefix_failures = []
    for model in MODELS:
        for example_id in data_by_id:
            for short, long in ((128, 256), (128, 512), (256, 512)):
                left, right = keys.get((model, short, example_id)), keys.get((model, long, example_id))
                if left is None or right is None:
                    continue
                a, b = left[1], right[1]
                if "generated_token_ids" not in a or "generated_token_ids" not in b:
                    continue
                prefix_comparisons += 1
                a_ids, b_ids = a["generated_token_ids"], b["generated_token_ids"]
                if a_ids != b_ids[:len(a_ids)] or (a.get("stopping_reason", "").startswith("eos") and a_ids != b_ids):
                    prefix_failures.append({"model": model, "problem_id": example_id, "caps": [short, long]})
    if prefix_failures:
        errors.append({"prefix_failures": prefix_failures})
    return {"pass": not errors, "complete": not missing and not unexpected and len(rows) == len(expected),
            "expected_records": len(expected), "record_count": len(rows), "unique_keys": len(keys),
            "missing_count": len(missing), "missing_keys": [list(key) for key in missing],
            "record_checks_run": checks_run, "phase_counts": dict(phases), "stopping_counts": dict(stops),
            "actual_generated_tokens": generated_tokens, "prefix_comparisons": prefix_comparisons,
            "prefix_failures": prefix_failures, "errors": errors,
            "cells": [{"model": model, "cap": cap, "n": counts[(model, cap)]} for model in MODELS for cap in CAPS]}


def verify_hashes(entries, root, errors, label):
    for name, want in entries.items():
        path = Path(name) if Path(name).is_absolute() else root / name
        wanted_hash = want["sha256"] if isinstance(want, dict) else want
        try:
            observed = digest(path)
            if observed != wanted_hash:
                errors.append({label: str(path), "expected": wanted_hash, "observed": observed})
        except OSError as exc:
            errors.append({label: str(path), "unreadable": repr(exc)})


def verify_timing_reuse(rows, original):
    errors = []
    source = {record_key(row): row for row in original}
    reused = [row for row in rows if row.get("phase") == "timing"]
    if len(source) != 420 or len(original) != 420 or any(row.get("phase") != "timing" for row in original):
        errors.append({"invalid_source_timing_matrix": len(original)})
    seen = set()
    for row in reused:
        key = record_key(row)
        seen.add(key)
        if key not in source:
            errors.append({"unknown_reused_timing_key": list(key)})
        elif any(row.get(field) != value for field, value in source[key].items()):
            errors.append({"changed_reused_timing_record": list(key)})
    if seen != set(source) or len(reused) != 420:
        errors.append({"timing_reuse_coverage": len(reused), "unique": len(seen), "expected": 420})
    return errors


def verify_origins(rows, run_dir):
    """Authenticate each canonical row against its preserved original journal."""
    errors = []
    files = {}
    for row in rows:
        key = list(record_key(row))
        origin = row.get("full_origin")
        if not isinstance(origin, dict):
            errors.append({"missing_full_origin": key})
            continue
        try:
            kind = origin["kind"]
            wanted_kind = "timing_reuse" if row["phase"] == "timing" else "full_generation"
            if kind != wanted_kind:
                errors.append({"origin_phase_mismatch": key})
            source = (run_dir / origin["source_file"]).resolve()
            allowed = ((PILOT / "attempts").resolve() if kind == "timing_reuse" else (run_dir / "journals").resolve())
            if not source.is_relative_to(allowed):
                errors.append({"origin_outside_expected_tree": key, "source": str(source)})
                continue
            if source not in files:
                files[source] = (digest(source), read_rows(source))
            source_hash, source_rows = files[source]
            if source_hash != origin["source_file_sha256"]:
                errors.append({"origin_file_hash_mismatch": key, "source": str(source)})
            line = origin["source_line1based"]
            if type(line) is not int or not 1 <= line <= len(source_rows):
                errors.append({"invalid_origin_line": key})
                continue
            source_row = source_rows[line - 1]
            original_fields = {name: value for name, value in row.items() if name != "full_origin"}
            if original_fields != source_row:
                errors.append({"origin_record_mismatch": key, "source": str(source), "line": line})
        except (KeyError, ValueError, TypeError, OSError, IndexError) as exc:
            errors.append({"invalid_full_origin": key, "error": repr(exc)})
    return errors, len(files)


def verify_telemetry(run_dir, timing, configurations, require_full_coverage):
    errors = []
    expected_host = json.loads((timing / "host.json").read_text())
    host_fields = ("machine", "python", "packages", "device", "dtype", "attention_implementation",
                   "deterministic_algorithms", "deterministic_warn_only", "mps_cpu_fallback_env",
                   "memory_fraction", "hardware", "seed")
    hosts = sorted((run_dir / "telemetry").glob("*/host.json"))
    for path in hosts:
        observed = json.loads(path.read_text())
        differing = [name for name in host_fields if observed.get(name) != expected_host.get(name)]
        if differing:
            errors.append({"full_host_settings_differ_from_timing": str(path), "fields": differing})
    seen = set()
    config_files = sorted((run_dir / "telemetry").glob("*/generation_configs.jsonl"))
    for path in config_files:
        for item in read_rows(path):
            key = (item["model"], item["cap"])
            seen.add(key)
            if item.get("sha256") != configurations.get(key):
                errors.append({"full_config_digest_differs_from_timing": str(path), "cell": list(key)})
            expected = next((cell["configuration"] for cell in json.loads((timing / "generation_configs.json").read_text())
                             if (cell["model"], cell["cap"]) == key), None)
            if item.get("configuration") != expected:
                errors.append({"full_resolved_config_differs_from_timing": str(path), "cell": list(key)})
    if require_full_coverage and (not hosts or seen != set(configurations)):
        errors.append({"full_telemetry_coverage_missing": True, "hosts": len(hosts), "cells": len(seen)})
    return errors, len(hosts), len(config_files)


def main(run_dir, output, allow_incomplete=False):
    from transformers import AutoTokenizer, GenerationConfig
    run_dir = Path(run_dir).resolve()
    destination = Path(output).resolve()
    if destination.exists():
        raise FileExistsError(destination)
    manifest = json.loads((run_dir / "run_freeze.json").read_text())
    frozen = json.loads((PILOT / "freeze.json").read_text())
    errors = []
    if manifest.get("pilot_freeze") != frozen:
        errors.append({"pilot_freeze_mismatch": True})
    verify_hashes(frozen["source_sha256"], PILOT, errors, "changed_frozen_pilot_source")
    verify_hashes(frozen["model_files_sha256"], PILOT, errors, "changed_frozen_model_or_tokenizer")
    run_sources = manifest.get("run_source_sha256", manifest.get("source_sha256", {}))
    if not run_sources:
        errors.append({"missing_run_source_freeze": True})
    verify_hashes(run_sources, run_dir, errors, "changed_full_run_source")
    pilot_manifest_path = PILOT / "artifact_manifest.json"
    if manifest.get("pilot_artifact_manifest_sha256") != digest(pilot_manifest_path):
        errors.append({"pilot_artifact_manifest_hash_mismatch": True})
    pilot_artifacts = json.loads(pilot_manifest_path.read_text())
    verify_hashes(pilot_artifacts["artifacts"], PILOT, errors, "changed_preserved_pilot_artifact")
    historical = json.loads((PILOT / "historical_before.json").read_text())
    verify_hashes(historical["sha256"], ROOT, errors, "changed_historical_file")
    timing = PILOT / "attempts" / manifest.get("timing_attempt", "001_fp16_mps") / "timing"
    timing_path = timing / "responses.jsonl"
    if manifest.get("timing_responses_sha256") != digest(timing_path):
        errors.append({"timing_responses_hash_mismatch": True})
    if json.loads((timing / "source_freeze.json").read_text()) != frozen:
        errors.append({"timing_source_freeze_mismatch": True})
    if not json.loads((timing / "validation.json").read_text()).get("pass"):
        errors.append({"timing_validation_failed": True})
    configurations = {}
    for cell in json.loads((timing / "generation_configs.json").read_text()):
        key = (cell["model"], cell["cap"])
        configurations[key] = cell["sha256"]
        restored = GenerationConfig.from_dict(cell["configuration"])
        actual_hash = hashlib.sha256(restored.to_json_string(use_diff=False).encode()).hexdigest()
        if actual_hash != cell["sha256"]:
            errors.append({"unreproducible_pilot_config_digest": list(key)})
    if set(configurations) != {(model, cap) for model in MODELS for cap in CAPS}:
        errors.append({"incomplete_pilot_config_matrix": True})
    data = read_rows(PILOT / "preparation/development.jsonl")
    data_by_id = {row["problem_id"]: row for row in data}
    if len(data) != 500 or set(data_by_id) != set(range(500)):
        errors.append({"invalid_frozen_data_coverage": True})
    base = next(Path(path).parent for path in frozen["model_files_sha256"] if Path(path).name == "model.safetensors")
    if json.loads((base / "generation_config.json").read_text()) != json.loads((timing / "base_generation_config.json").read_text()):
        errors.append({"base_generation_config_changed_since_timing_pilot": True})
    tokenizer = AutoTokenizer.from_pretrained(base, local_files_only=True, trust_remote_code=False)
    spec = importlib.util.spec_from_file_location("verified_frozen_terminal_extractor", PILOT / "terminal_extractor.py")
    extractor = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(extractor)
    adapter_hashes = {"Base": None}
    for model in MODELS[1:]:
        condition, seed = model.split("_")
        path = ROOT / f"experiments/milestone3/{condition}_seed_{seed}/final_model/adapter_model.safetensors"
        adapter_hashes[model] = frozen["model_files_sha256"][str(path)]
    record_files = sorted((run_dir / "records").glob("*.jsonl"))
    rows = []
    record_manifests = {}
    for path in record_files:
        try:
            records = read_rows(path)
            rows.extend(records)
            record_manifests[str(path.relative_to(run_dir))] = {"sha256": digest(path), "bytes": path.stat().st_size, "records": len(records)}
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            errors.append({"unreadable_record_file": str(path), "error": repr(exc)})
    result = verify_records(rows, data_by_id, tokenizer, configurations, adapter_hashes,
                            extractor, require_complete=not allow_incomplete, base_revision=frozen["base_revision"])
    errors.extend(verify_timing_reuse(rows, read_rows(timing_path)))
    origin_errors, origin_files = verify_origins(rows, run_dir)
    errors.extend(origin_errors)
    telemetry_errors, host_files, config_files = verify_telemetry(run_dir, timing, configurations, require_full_coverage=result["complete"])
    errors.extend(telemetry_errors)
    result["errors"].extend(errors)
    result["pass"] = not result["errors"]
    result.update({"schema": "arithmetic-full-artifact-verification-1", "run_freeze_sha256": digest(run_dir / "run_freeze.json"),
                   "verified_record_files": record_manifests, "historical_files_rehashed": len(historical["sha256"]),
                   "preserved_pilot_files_rehashed": len(pilot_artifacts["artifacts"]),
                   "frozen_model_tokenizer_files_rehashed": len(frozen["model_files_sha256"]),
                   "original_journal_files_verified": origin_files,
                   "full_host_files_verified": host_files, "full_generation_config_files_verified": config_files,
                   "timing_reused_expected": 420, "allow_incomplete": allow_incomplete,
                   "scope": "Saved-evidence consistency and frozen extraction replay only. No model inference; no independent semantic or historical-causality verification."})
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("x") as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
        stream.write("\n")
    print(json.dumps({key: result[key] for key in ("pass", "complete", "record_count", "unique_keys", "missing_count", "prefix_comparisons")}))
    if not result["pass"]:
        raise SystemExit(1)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, default=HERE)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--allow-incomplete", action="store_true")
    arguments = parser.parse_args()
    main(arguments.run_dir, arguments.output, arguments.allow_incomplete)
