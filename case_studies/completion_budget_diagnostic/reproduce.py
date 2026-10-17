"""Verify or reanalyze the packaged, saved diagnostic responses; never infer.

Verification uses only Python's standard library. Reanalysis imports the frozen
analysis functions and NumPy; optional figures additionally import Matplotlib.
This packaging adapter does not change the frozen parser or scientific methods.
"""
from __future__ import annotations

import argparse
from collections import Counter
import gzip
import hashlib
import importlib.util
import itertools
import json
from pathlib import Path, PurePosixPath
import re
import sys

HERE = Path(__file__).resolve().parent
MODELS = ("Base", "robust_201", "proxy_201", "robust_202", "proxy_202", "robust_203", "proxy_203")
CAPS = (128, 256, 512)
POLICIES = ("legacy", "terminal", "declared")
BASE_REVISION = "7ae557604adf67be50417f59c2c2f167def9a775"
CORE_RESULTS = ("cell_metrics.json", "cap_transitions.json", "condition_contrasts.json",
                "model_diagnostics.json", "policy_sensitivity.json", "representative_examples.json")
REQUIRED_FILES = ("reproduce.py", "data/development.jsonl", "data/responses.jsonl.gz",
                  "data/generation_configs.json", "provenance/record_sha256.json", "provenance/models.json",
                  "frozen/full/analyze_full.py", "frozen/full/plot_full.py", "frozen/full/analysis_spec.md",
                  "frozen/pilot/terminal_extractor.py", "frozen/pilot/extractor_spec.md") + tuple(
                      "results/" + name for name in CORE_RESULTS)
LIMITATIONS = [
    "Checks the packaged bytes and saved claims, not authenticity against an external signed archive.",
    "Original source journals and timing-pilot files are not independently checked by this portable verifier.",
    "No model weights or tokenizer are loaded: model bytes, token-to-text decoding and prompt tokenization are not reverified.",
    "Historical training-source identity, original base revision and historical generation stops remain unverified.",
    "Bootstrap intervals condition on the fixed runs and 500 shared examples; they do not quantify new-training-run uncertainty.",
]


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest_bytes(value):
    return hashlib.sha256(value).hexdigest()


def digest_file(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(4 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def reject_constant(value):
    raise ValueError(f"Nonfinite JSON value: {value}")


def loads(value):
    return json.loads(value, parse_constant=reject_constant)


def load_json(path):
    return loads(Path(path).read_text(encoding="utf-8"))


def packaged_path(root, relative):
    root = Path(root).resolve()
    require(isinstance(relative, str), "Manifest paths must be strings")
    parts = PurePosixPath(relative)
    require(relative and not parts.is_absolute() and ".." not in parts.parts and
            "." not in parts.parts and str(parts) == relative and "\\" not in relative,
            f"Invalid package-relative path: {relative!r}")
    path = root.joinpath(*parts.parts)
    require(not any(root.joinpath(*parts.parts[:n]).is_symlink() for n in range(1, len(parts.parts) + 1)),
            f"Symlink is not an immutable packaged file: {relative}")
    require(path.is_file() and path.resolve().is_relative_to(root.resolve()),
            f"Missing or external packaged file: {relative}")
    return path


def verify_manifest(root, required=REQUIRED_FILES):
    """Verify all listed files before importing any packaged Python source."""
    manifest = load_json(root / "manifest.json")
    files = manifest.get("files")
    require(isinstance(files, dict) and set(required) <= set(files),
            "Manifest omits required reproduction inputs")
    for relative, expected in files.items():
        path = packaged_path(root, relative)
        require(isinstance(expected, dict) and re.fullmatch(r"[0-9a-f]{64}", expected.get("sha256", "")) is not None,
                f"Invalid manifest digest: {relative}")
        require(type(expected.get("bytes")) is int and expected["bytes"] >= 0,
                f"Invalid manifest byte count: {relative}")
        require(path.stat().st_size == expected["bytes"] and digest_file(path) == expected["sha256"],
                f"Manifest hash/size mismatch: {relative}")
    return manifest


def import_frozen(root, relative, module_name):
    spec = importlib.util.spec_from_file_location(module_name, root / relative)
    require(spec is not None and spec.loader is not None, f"Cannot import frozen source: {relative}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def read_development(path):
    items = []
    with path.open("rb") as stream:
        for line_number, line in enumerate(stream, 1):
            require(line.endswith(b"\n") and line.strip(), f"Incomplete development line: {line_number}")
            item = loads(line)
            require(isinstance(item, dict), f"Non-object development line: {line_number}")
            require(all(type(item.get(k)) is int for k in ("problem_id", "a", "b", "c", "result")),
                    f"Invalid development integers: {line_number}")
            require(item["result"] == item["a"] * item["b"] + item["c"],
                    f"Development arithmetic mismatch: {line_number}")
            items.append(item)
    require(len(items) == 500 and {r["problem_id"] for r in items} == set(range(500)),
            "Development set must contain exactly 500 unique IDs, 0 through 499")
    return {r["problem_id"]: r for r in items}


def row_identity(row):
    require(isinstance(row, dict), "Response must be a JSON object")
    model, cap, example = row.get("model"), row.get("max_new_tokens"), row.get("problem_id")
    require(model in MODELS and type(cap) is int and cap in CAPS and type(example) is int and 0 <= example < 500,
            f"Unexpected response identity: {(model, cap, example)!r}")
    require(row.get("phase") == ("timing" if example < 20 else "full"),
            f"Wrong timing/full phase or excluded smoke/control row: {(model, cap, example)!r}")
    return model, cap, example


def original_record_name(row):
    model, cap, example = row_identity(row)
    return f"records/{model}__{cap}__{example:04d}.jsonl"


def read_responses(root, expected_hashes):
    require(isinstance(expected_hashes, dict), "Original record hashes must be a mapping")
    records, observed = [], []
    with gzip.open(root / "data/responses.jsonl.gz", "rb") as stream:
        for line_number, raw in enumerate(stream, 1):
            require(raw.endswith(b"\n") and raw.strip(), f"Incomplete response line: {line_number}")
            row = loads(raw)
            name = original_record_name(row)
            require(name in expected_hashes and digest_bytes(raw) == expected_hashes[name],
                    f"Original canonical row-byte digest mismatch: {name}")
            observed.append(name)
            records.append(row)
    require(observed == sorted(observed) and len(set(observed)) == len(observed),
            "Response archive must retain original sorted filenames without duplicates")
    require(set(observed) == set(expected_hashes), "Response archive and original record hash inventory differ")
    require(len(records) == 10500, f"Expected exactly 10,500 responses; found {len(records)}")
    return records


def generation_configs(root):
    entries = load_json(root / "data/generation_configs.json")
    require(isinstance(entries, list) and len(entries) == 21, "Expected exactly 21 generation configurations")
    configs = {}
    for entry in entries:
        pair = (entry.get("model"), entry.get("cap"))
        require(pair[0] in MODELS and type(pair[1]) is int and pair[1] in CAPS and pair not in configs,
                f"Unknown or duplicate generation cell: {pair}")
        config = entry["configuration"]
        # This is GenerationConfig.to_json_string(use_diff=False)'s saved
        # serialization, verified without importing Transformers.
        want = digest_bytes((json.dumps(config, indent=2, sort_keys=True) + "\n").encode())
        require(entry.get("sha256") == want, f"Generation configuration digest mismatch: {pair}")
        require(config["max_new_tokens"] == pair[1] and config["do_sample"] is False and
                config["num_beams"] == 1 and config["repetition_penalty"] == 1.1 and
                config["eos_token_id"] == [151645, 151643] and config["pad_token_id"] == 151643,
                f"Frozen generation settings mismatch: {pair}")
        configs[pair] = want
    require(set(configs) == set(itertools.product(MODELS, CAPS)), "Incomplete generation configuration grid")
    return configs


def verify(root):
    manifest = verify_manifest(root)
    data = read_development(root / "data/development.jsonl")
    hashes = load_json(root / "provenance/record_sha256.json")
    if set(hashes) == {"sha256"}:
        hashes = hashes["sha256"]
    records = read_responses(root, hashes)
    configs = generation_configs(root)
    models = load_json(root / "provenance/models.json")
    require(models.get("base_revision") == BASE_REVISION, "Diagnostic base revision mismatch")
    adapters = models.get("adapter_sha256")
    require(isinstance(adapters, dict) and set(adapters) == set(MODELS) and adapters["Base"] is None,
            "Model adapter identity inventory mismatch")
    require(all(re.fullmatch(r"[0-9a-f]{64}", adapters[m] or "") for m in MODELS if m != "Base"),
            "Invalid adapter digest")
    analysis = import_frozen(root, "frozen/full/analyze_full.py", "packaged_frozen_analysis")
    extractor = import_frozen(root, "frozen/pilot/terminal_extractor.py", "packaged_frozen_extractor")
    index = analysis.validate_grid(records)
    phases = dict(Counter(r["phase"] for r in records))
    require(phases == {"timing": 420, "full": 10080}, f"Wrong phase counts: {phases}")
    for row in records:
        identity = row_identity(row)
        require(set(row["scores"]) == set(POLICIES), f"Wrong extraction-policy set: {identity}")
        require(row.get("adapter_sha256") == adapters[row["model"]], f"Saved adapter digest mismatch: {identity}")
        if "training_seed" in row:
            require(row["training_seed"] == (None if row["model"] == "Base" else int(row["model"].rsplit("_", 1)[1])),
                    f"Saved training seed mismatch: {identity}")
        require(isinstance(row.get("raw_completion"), str) and isinstance(row.get("readable_completion"), str),
                f"Missing saved completion text: {identity}")
        if "final_original_token_id" in row:
            require(row["final_original_token_id"] == row["generated_token_ids"][-1],
                    f"Final original token ID mismatch: {identity}")
        analysis.verify_record(row, data[row["problem_id"]], configs[identity[:2]], extractor)
    prefixes = analysis.verify_prefixes(index)
    require(prefixes == 10500, "Unexpected number of independent-cap prefix checks")
    summary = {"pass": True, "scope": "Portable saved-output verification; no inference or model loading",
               "records": len(records), "cells": 21, "problems_per_cell": 500,
               "training_seed_pairs": 3, "phase_counts": phases, "prefix_comparisons": prefixes,
               "manifest_files_checked": len(manifest["files"]), "extractor_version": extractor.VERSION,
               "limitations": LIMITATIONS}
    return summary, index, analysis


def ensure_new_output(path):
    require(not path.exists() and not path.is_symlink(), f"Output already exists: {path}")
    require(path.parent.is_dir(), f"Output parent must already exist: {path.parent}")


def recompute(index, analysis):
    """Use the original loops and labels, keeping all scientific methods frozen."""
    cells, transitions = [], []
    for model, cap, policy in itertools.product(MODELS, CAPS, POLICIES):
        rows = [index[model, cap, i] for i in range(500)]
        cells.append(analysis.cell_summary(rows, model, cap, policy))
    for model, policy in itertools.product(MODELS, POLICIES):
        for low, high in itertools.combinations(CAPS, 2):
            a, b = ([index[model, c, i] for i in range(500)] for c in (low, high))
            transitions.append({"model": model, "policy": policy, "low_cap": low, "high_cap": high,
                                **analysis.paired_transition(a, b, policy, f"{model}/{policy}/{low}/{high}")})
    return {"cell_metrics.json": cells, "cap_transitions.json": transitions,
            "condition_contrasts.json": analysis.condition_contrasts(index),
            "model_diagnostics.json": analysis.model_diagnostics(index),
            "policy_sensitivity.json": analysis.policy_sensitivity(index),
            "representative_examples.json": analysis.representative_examples(index)}


def write_json(path, value):
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write("\n")


def matches_saved_json(value, saved):
    """Compare the persisted JSON meaning, including JSON's string-only keys."""
    return loads(json.dumps(value, allow_nan=False)) == saved


def run(root, output=None, figures=False):
    root = Path(root).resolve()
    if output is not None:
        output = Path(output).absolute()
        ensure_new_output(output)
    require(not figures or output is not None, "--figures requires --output")
    verification, index, analysis = verify(root)
    if output is None:
        return verification
    import numpy as np
    outputs = recompute(index, analysis)
    comparison = {name: matches_saved_json(value, load_json(root / "results" / name))
                  for name, value in outputs.items()}
    output.mkdir(exist_ok=False)
    numeric = output / "analysis"
    numeric.mkdir()
    for name, value in outputs.items():
        write_json(numeric / name, value)
    analysis.write_tsv(numeric / "cell_metrics.tsv", outputs["cell_metrics.json"])
    analysis.write_tsv(numeric / "condition_pairs.tsv", [
        {k: v for k, v in r.items() if k != "common_accepted_eos"}
        for r in outputs["condition_contrasts.json"]["individual_pairs"]])
    result = {**verification, "pass": all(comparison.values()), "output": str(output),
              "numeric_result_matches": comparison, "numpy_version": np.__version__,
              "recorded_analysis_numpy_version": "2.5.3", "figures_requested": figures,
              "runtime_note": "Saved generation runtimes and memory tables are retained, not remeasured by reanalysis."}
    if result["pass"] and figures:
        plot = import_frozen(root, "frozen/full/plot_full.py", "packaged_frozen_plot")
        plot.render(numeric, output / "figures")
        import matplotlib
        result["matplotlib_version"] = matplotlib.__version__
        result["figure_note"] = "Re-rendered from identical numeric outputs; byte-identical rendering is not promised across library versions."
    write_json(output / "reproduction.json", result)
    require(result["pass"], f"Recomputed results differ from the packaged results; inspect {output / 'reproduction.json'}")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--verify-only", action="store_true", help="Stdlib-only validation of packaged saved outputs")
    mode.add_argument("--output", type=Path, help="New, nonexistent directory for reanalysis outputs")
    parser.add_argument("--figures", action="store_true", help="Also render figures after numerical equality passes")
    args = parser.parse_args()
    if args.figures and args.verify_only:
        parser.error("--figures requires --output")
    try:
        result = run(HERE, args.output, args.figures)
    except (ValueError, KeyError, TypeError, IndexError, OSError, ImportError) as exc:
        print(f"Reproduction failed: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
