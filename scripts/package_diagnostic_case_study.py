"""Prepare a public saved-output export; no inference, training or publication.

Maintainer-only packaging commands (exclusive outputs): --export, then --seal.
Readers use case_studies/completion_budget_diagnostic/reproduce.py instead.
"""
import argparse
from datetime import datetime, timezone
import gzip
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIAG = ROOT / "experiments/diagnostics/2026-10-16"
FULL = DIAG / "full"
PILOT = DIAG / "pilot"
PUBLIC = ROOT / "case_studies/completion_budget_diagnostic"


def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(4 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def read(path):
    return json.loads(path.read_text())


def dump(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x") as stream:
        json.dump(obj, stream, indent=2, allow_nan=False)
        stream.write("\n")


def export():
    seal = read(FULL / "artifact_manifest_001.json")
    assert (FULL / "artifact_manifest_001.sha256").read_text().split()[0] == sha(FULL / "artifact_manifest_001.json")
    pilot_seal = read(PILOT / "artifact_manifest.json")["artifacts"]
    sources = {}

    def copy(source, relative):
        expected = (seal["files"].get(str(source.relative_to(FULL))) if source.is_relative_to(FULL)
                    else pilot_seal.get(str(source.relative_to(PILOT))) if source.is_relative_to(PILOT) else None)
        if expected is not None:
            assert sha(source) == expected["sha256"], source
        target = PUBLIC / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("xb") as stream:
            stream.write(source.read_bytes())
        sources[relative] = {"source": str(source.relative_to(ROOT)), "source_sha256": sha(source), "transform": "byte-identical copy"}

    for name in ("analyze_full.py", "plot_full.py", "analysis_spec.md", "run_full.py", "run_storage.py", "verify_full.py"):
        copy(FULL / name, "frozen/full/" + name)
    for name in ("terminal_extractor.py", "extractor_spec.md", "test_terminal_extractor.py", "run_pilot.py"):
        copy(PILOT / name, "frozen/pilot/" + name)
    copy(DIAG / "audit.py", "frozen/audit.py")
    copy(DIAG / "diagnostic_plan.md", "frozen/diagnostic_plan.md")
    copy(PILOT / "preparation/development.jsonl", "data/development.jsonl")
    copy(PILOT / "attempts/001_fp16_mps/timing/generation_configs.json", "data/generation_configs.json")
    for name in ("cell_metrics.json", "cell_metrics.tsv", "condition_pairs.tsv", "condition_contrasts.json",
                 "cap_transitions.json", "model_diagnostics.json", "policy_sensitivity.json",
                 "representative_examples.json", "runtime_cells.tsv"):
        copy(FULL / "analysis_001" / name, "results/" + name)
    for path in sorted((FULL / "figures_001").iterdir()):
        copy(path, "figures/" + path.name)
    data_path = PUBLIC / "data/responses.jsonl.gz"
    record_hashes, adapters, phases = {}, {}, {"timing": 0, "full": 0}
    with data_path.open("xb") as stream:
        with gzip.GzipFile(filename="", mode="wb", fileobj=stream, mtime=0) as compressed:
            for path in sorted((FULL / "records").glob("*.jsonl")):
                relative = str(path.relative_to(FULL))
                assert sha(path) == seal["files"][relative]["sha256"]
                raw = path.read_bytes()
                assert raw.endswith(b"\n") and len(raw.splitlines()) == 1
                row = json.loads(raw)
                phases[row["phase"]] += 1
                assert row["model"] not in adapters or adapters[row["model"]] == row["adapter_sha256"]
                adapters[row["model"]] = row["adapter_sha256"]
                record_hashes[relative] = sha(path)
                compressed.write(raw)
    assert len(record_hashes) == 10500 and phases == {"timing": 420, "full": 10080} and len(adapters) == 7
    dump(PUBLIC / "provenance/record_sha256.json", record_hashes)
    sources["data/responses.jsonl.gz"] = {"source": "experiments/diagnostics/2026-10-16/full/records/*.jsonl",
        "transform": "Original canonical JSONL bytes concatenated in filename order; deterministic gzip header (mtime=0). No record fields removed or changed.",
        "per_record_sha256": "provenance/record_sha256.json"}
    freeze = read(PILOT / "freeze.json")
    base_tensor = next(v for k,v in freeze["model_files_sha256"].items() if k.endswith("/model.safetensors"))
    dump(PUBLIC / "provenance/models.json", {
        "base_model": "Qwen/Qwen2.5-0.5B-Instruct", "base_revision": "7ae557604adf67be50417f59c2c2f167def9a775",
        "base_tensor_sha256": base_tensor, "adapter_sha256": adapters,
        "weights_included": False, "historical_adapters_public_download": None,
        "original_training_base_revision_verified": False,
        "inference": {"hardware": "Apple M5; 16 GiB unified memory", "python": "3.14.7", "torch": "2.14.0",
            "transformers": "5.16.1", "peft": "0.20.0", "tokenizers": "0.23.2", "accelerate": "1.14.0",
            "precision": "fp16", "device": "MPS", "attention": "eager", "batch_size": 1,
            "do_sample": False, "repetition_penalty": 1.1, "seed_per_call": 71448,
            "strict_deterministic_algorithms": True, "mps_cpu_fallback": False},
        "scope": "Identifiers and saved record consistency are public; absent weight bytes and historical provenance cannot be independently checked from this package."})
    original = (FULL / "failure_examples.md").read_text()
    examples = original.replace("analysis_001/representative_examples.json", "results/representative_examples.json")
    with (PUBLIC / "examples.md").open("x") as stream:
        stream.write(examples)
    sources["examples.md"] = {"source": "experiments/diagnostics/2026-10-16/full/failure_examples.md",
                              "source_sha256": sha(FULL / "failure_examples.md"), "transform": "Only the relative JSON link is redirected to the public copy; all selected examples unchanged."}
    runtime = read(FULL / "analysis_001/runtime_summary.json")
    clocks = runtime["process_and_wall_time"]
    dump(PUBLIC / "results/runtime_overview.json", {
        "total_generated_tokens": runtime["total_generated_tokens"], "generation_seconds": runtime["generation_seconds"],
        "new_continuation_process_seconds": clocks["full_continuation_process_elapsed_recorded_seconds"],
        "reused_timing_process_seconds": clocks["timing_pilot_reused_elapsed_seconds"],
        "combined_process_seconds": clocks["full_continuation_plus_reused_pilot_process_elapsed_recorded_seconds"],
        "new_loading_seconds": clocks["full_continuation_loading_seconds"],
        "sampled_peak_continuation_gib": {"mps_allocated": 0.96, "mps_driver": 1.26, "process_rss": 2.95},
        "memory_note": "Nominal 20 ms samples, including loading. Unified-memory measures overlap; do not sum. Rounded stage peaks; exact per-cell values in runtime_cells.tsv.",
        "source_sha256": sha(FULL / "analysis_001/runtime_summary.json")})
    labels = [read(FULL / f"qualitative_audit/labels_{letter}.json") for letter in ("a", "b")]
    summary = read(FULL / "qualitative_audit/audit_summary.json")
    dump(PUBLIC / "results/qualitative_audit.json", {
        "reviewer_type": "Two independent AI-assisted text reviewers; no human labels or arithmetic judging",
        "n": 70, "agreement_n": 67, "disputed_ids": [r["id"] for r in summary["reviewer_disagreements"]],
        "consensus_terminal_matches": 66, "consensus_legacy_matches": 64,
        "reviewer_labels": {letter: doc["labels"] for letter,doc in zip(("a","b"), labels)},
        "original_label_sha256": {letter: sha(FULL / f"qualitative_audit/labels_{letter}.json") for letter in ("a","b")},
        "projection": "Label decisions/reasons unchanged. Machine-specific reviewer/source-path metadata omitted. No scores changed.",
        "limitations": summary["limitations"]})
    copy(FULL / "analysis_001/fallback_blind_packet.json", "data/fallback_blind_packet.json")
    verified = read(FULL / "postprocessing_001/artifact_verification.json")
    selected = ("pass", "complete", "record_count", "unique_keys", "phase_counts", "stopping_counts",
                "actual_generated_tokens", "prefix_comparisons", "historical_files_rehashed",
                "preserved_pilot_files_rehashed", "frozen_model_tokenizer_files_rehashed", "errors")
    dump(PUBLIC / "provenance/local_verification_summary.json", {
        "local_completed_verification": {k: verified[k] for k in selected},
        "original_verification_sha256": sha(FULL / "postprocessing_001/artifact_verification.json"),
        "original_full_archive_seal_sha256": sha(FULL / "artifact_manifest_001.json"),
        "original_full_archive_files": seal["file_count"],
        "disclosure": "A record of local verification, not a substitute for absent journals, model bytes, tokenizer decoding or independent historical provenance."})
    dump(PUBLIC / "provenance/export_sources.json", sources)
    print(json.dumps({"exported_records": len(record_hashes), "compressed_bytes": data_path.stat().st_size,
                      "byte_copied_artifacts": len(sources), "output": str(PUBLIC.relative_to(ROOT))}))


def seal_package():
    historical = read(PILOT / "historical_before.json")["sha256"]
    original = PUBLIC / "provenance/README_before_case_study.md"
    assert sha(original) == historical["README.md"]
    unchanged = 0
    for relative, expected in historical.items():
        if relative == "README.md":
            continue
        assert sha(ROOT / relative) == expected, relative
        unchanged += 1
    pilot_files = read(PILOT / "artifact_manifest.json")["artifacts"]
    for relative, entry in pilot_files.items():
        assert sha(PILOT / relative) == entry["sha256"], relative
    dump(PUBLIC / "provenance/readme_amendment.json", {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "authorization": "User requested packaging the completed diagnostic and updating the project README; no publication or further experiments.",
        "original_readme_sha256": sha(original), "updated_root_readme_sha256": sha(ROOT / "README.md"),
        "original_readme_archive": "provenance/README_before_case_study.md",
        "unchanged_other_historically_hashed_files": unchanged, "unchanged_pilot_files": len(pilot_files),
        "note": "Frozen manifests and verifier remain unchanged. Its original strict root-README hash gate will now reject the authorized documentation change; this archive preserves those original bytes. Historical results, datasets, training sources and model artifacts are unchanged.",
        "historical_hash_record_sha256": sha(PILOT / "historical_before.json")})
    files = {}
    for path in sorted(PUBLIC.rglob("*")):
        if not path.is_file() or path.name in ("manifest.json", "manifest.sha256"):
            continue
        assert not path.is_symlink()
        files[str(path.relative_to(PUBLIC))] = {"sha256": sha(path), "bytes": path.stat().st_size}
    dump(PUBLIC / "manifest.json", {
        "schema": "arithmetic-public-case-study-1", "files": files,
        "scientific_corpus": {"records": 10500, "problems": 500, "models": 7, "caps": [128,256,512],
                              "training_seed_pairs": [201,202,203], "timing_reuse": 420, "new_full": 10080},
        "analysis_environment": {"python": "3.14.7", "numpy": "2.5.3", "matplotlib": "3.11.1"},
        "weights_included": False, "source_exporter_sha256": sha(Path(__file__)),
        "scope": "Prepared review package of completed saved outputs, not a new experiment or publication. No weights, source journals, full host telemetry or training restart states included."})
    with (PUBLIC / "manifest.sha256").open("x") as stream:
        stream.write(f"{sha(PUBLIC / 'manifest.json')}  manifest.json\n")
    print(json.dumps({"public_files": len(files), "total_bytes": sum(r["bytes"] for r in files.values()),
                      "historical_files_unchanged_except_authorized_readme": unchanged,
                      "pilot_files_unchanged": len(pilot_files), "manifest_sha256": sha(PUBLIC / "manifest.json")}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--export", action="store_true")
    group.add_argument("--seal", action="store_true")
    args = parser.parse_args()
    export() if args.export else seal_package()
