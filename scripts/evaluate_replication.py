"""Evaluate a fresh replication without touching historical Milestone 3 outputs."""

import argparse
import json
import re
from pathlib import Path

import torch
import yaml
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer

from evaluate_milestone3 import evaluate_model


def read_jsonl(path: Path) -> list[dict]:
    if not path.is_file():
        raise FileNotFoundError(path)
    with path.open() as handle:
        return [json.loads(line) for line in handle]


def device_name() -> str:
    if torch.cuda.is_available():
        return "cuda"
    if torch.backends.mps.is_available():
        return "mps"
    return "cpu"


def load_base_model(model_name: str, device: str):
    dtype = torch.float32 if device == "cpu" else torch.float16
    return AutoModelForCausalLM.from_pretrained(
        model_name,
        torch_dtype=dtype,
        low_cpu_mem_usage=True,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("name")
    parser.add_argument("--seeds", nargs=3, type=int, default=(201, 202, 203))
    args = parser.parse_args()
    if not re.fullmatch(r"[A-Za-z0-9._-]+", args.name):
        raise ValueError("Replication name contains unsupported characters")

    repo_root = Path(__file__).resolve().parents[1]
    replication_dir = repo_root / "experiments" / "replications" / args.name
    output_path = replication_dir / "eval_results.json"
    if output_path.exists():
        raise FileExistsError(f"Refusing to overwrite existing results: {output_path}")

    config_path = replication_dir / "replication_config.yaml"
    manifest_path = replication_dir / "pre_training_manifest.json"
    if not manifest_path.is_file():
        raise FileNotFoundError("Replication pre-training manifest is missing")
    config = yaml.safe_load(config_path.read_text())
    model_name = config["model_name"]
    data_dir = repo_root / config["dataset_dir"]
    validation_data = read_jsonl(data_dir / "eval_dataset.jsonl")
    test_data = read_jsonl(data_dir / "test_dataset.jsonl")
    device = device_name()

    tokenizer = AutoTokenizer.from_pretrained(model_name)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    results = {
        "metadata": {
            "semantics": "corrected future-facing integer equality",
            "device": device,
            "replication": args.name,
        },
        "validation": {},
        "test": {},
    }

    base_model = load_base_model(model_name, device).to(device)
    base_model.eval()
    for split_name, dataset in (("validation", validation_data), ("test", test_data)):
        metrics, details = evaluate_model(base_model, tokenizer, dataset, device)
        results[split_name]["Base"] = {
            "metrics": metrics,
            "detailed_results": details,
        }
    del base_model
    if torch.cuda.is_available():
        torch.cuda.empty_cache()

    for seed in args.seeds:
        for condition in ("robust", "proxy"):
            adapter_path = replication_dir / f"{condition}_seed_{seed}" / "final_model"
            if not adapter_path.is_dir():
                raise FileNotFoundError(adapter_path)
            model = load_base_model(model_name, device)
            model = PeftModel.from_pretrained(model, adapter_path).to(device)
            model.eval()
            label = f"{condition.capitalize()} RL (Seed {seed})"
            for split_name, dataset in (("validation", validation_data), ("test", test_data)):
                metrics, details = evaluate_model(model, tokenizer, dataset, device)
                results[split_name][label] = {
                    "metrics": metrics,
                    "detailed_results": details,
                }
            del model
            if torch.cuda.is_available():
                torch.cuda.empty_cache()

    output_path.write_text(json.dumps(results, indent=2) + "\n")
    print(f"Saved fresh replication results to {output_path.relative_to(repo_root)}")


if __name__ == "__main__":
    main()
