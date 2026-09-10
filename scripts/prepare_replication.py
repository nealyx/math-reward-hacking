"""Prepare a fresh, hash-recorded replication directory and data split."""

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

import yaml
from huggingface_hub import snapshot_download


MODEL_REPO = "Qwen/Qwen2.5-0.5B-Instruct"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("name", help="Replication name (letters, digits, dot, dash, underscore)")
    parser.add_argument(
        "model_revision",
        help="Full 40-character Hugging Face commit SHA for the Qwen base model",
    )
    parser.add_argument("--train-data-seed", type=int, default=1042)
    parser.add_argument("--validation-data-seed", type=int, default=1043)
    parser.add_argument("--test-data-seed", type=int, default=1044)
    parser.add_argument("--training-seeds", nargs=3, type=int, default=(201, 202, 203))
    args = parser.parse_args()

    if not re.fullmatch(r"[A-Za-z0-9._-]+", args.name):
        raise ValueError("Replication name contains unsupported characters")
    if not re.fullmatch(r"[0-9a-fA-F]{40}", args.model_revision):
        raise ValueError("model_revision must be a full 40-character commit SHA")
    if len(set(args.training_seeds)) != 3:
        raise ValueError("training seeds must be distinct")

    repo_root = Path(__file__).resolve().parents[1]
    relative_dir = Path("experiments") / "replications" / args.name
    replication_dir = repo_root / relative_dir
    replication_dir.mkdir(parents=True, exist_ok=False)

    model_dir = replication_dir / "base_model"
    snapshot_download(
        repo_id=MODEL_REPO,
        revision=args.model_revision.lower(),
        local_dir=model_dir,
    )

    base_config = yaml.safe_load((repo_root / "configs" / "milestone3.yaml").read_text())
    base_config.update(
        {
            "model_name": str(relative_dir / "base_model"),
            "dataset_dir": str(relative_dir / "data"),
            "train_seed": args.train_data_seed,
            "eval_seed": args.validation_data_seed,
            "test_seed": args.test_data_seed,
        }
    )
    config_path = replication_dir / "replication_config.yaml"
    config_path.write_text(yaml.safe_dump(base_config, sort_keys=False))

    subprocess.run(
        [
            sys.executable,
            str(repo_root / "scripts" / "generate_data.py"),
            "--config",
            str(config_path),
        ],
        cwd=repo_root,
        check=True,
    )

    paths_to_hash = [
        config_path,
        replication_dir / "data" / "train_dataset.jsonl",
        replication_dir / "data" / "eval_dataset.jsonl",
        replication_dir / "data" / "test_dataset.jsonl",
        replication_dir / "data" / "dataset_metadata.json",
        repo_root / "scripts" / "train_grpo.py",
        repo_root / "scripts" / "evaluate_replication.py",
        repo_root / "src" / "math_reward_hacking" / "rewards" / "verifiers.py",
    ]
    model_files = sorted(path for path in model_dir.rglob("*") if path.is_file())
    manifest = {
        "protocol": "fresh replication; not the historical confirmatory run",
        "base_model_repo": MODEL_REPO,
        "base_model_revision": args.model_revision.lower(),
        "training_seeds": list(args.training_seeds),
        "data_seeds": {
            "train": args.train_data_seed,
            "validation": args.validation_data_seed,
            "test": args.test_data_seed,
        },
        "sha256": {
            str(path.relative_to(repo_root)): sha256_file(path)
            for path in paths_to_hash + model_files
        },
    }
    manifest_path = replication_dir / "pre_training_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"Prepared fresh replication at {relative_dir}")


if __name__ == "__main__":
    main()
