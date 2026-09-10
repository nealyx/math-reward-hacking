"""Read-only integrity checks for the six confirmatory runs.

This is a command-line audit utility, not a pytest module. It intentionally
loads only this repository's trusted local ``training_args.bin`` files.
"""

import argparse
import hashlib
import json
from pathlib import Path

import torch


SEEDS = (201, 202, 203)
CONDITIONS = ("robust", "proxy")
EXPECTED_ARGS = {
    "learning_rate": 5e-6,
    "num_train_epochs": 1,
    "per_device_train_batch_size": 1,
    "gradient_accumulation_steps": 4,
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def verify_preservation_manifest(repo_root: Path, manifest_path: Path) -> int:
    """Verify the immutable section of the pre-cleanup manifest."""
    checked = 0
    for line in manifest_path.read_text().splitlines():
        if line.startswith("# Authorized mutable artifact"):
            break
        if not line or line.startswith("#"):
            continue
        expected, relative_path = line.split(maxsplit=1)
        path = repo_root / relative_path
        if not path.is_file():
            raise AssertionError(f"Missing preserved artifact: {relative_path}")
        actual = sha256_file(path)
        if actual != expected:
            raise AssertionError(
                f"SHA-256 mismatch for {relative_path}: {actual} != {expected}"
            )
        checked += 1
    return checked


def verify_confirmatory_runs(repo_root: Path) -> int:
    base_dir = repo_root / "experiments" / "milestone3"
    checked = 0

    for condition in CONDITIONS:
        for seed in SEEDS:
            run_name = f"{condition}_seed_{seed}"
            run_dir = base_dir / run_name
            final_model = run_dir / "final_model"
            checkpoint = run_dir / "checkpoint-500"

            for required in (final_model, checkpoint):
                if not required.is_dir():
                    raise AssertionError(
                        f"Missing directory: {required.relative_to(repo_root)}"
                    )

            final_adapter = final_model / "adapter_model.safetensors"
            checkpoint_adapter = checkpoint / "adapter_model.safetensors"
            if sha256_file(final_adapter) != sha256_file(checkpoint_adapter):
                raise AssertionError(
                    f"Final adapter differs from checkpoint-500: {run_name}"
                )

            state_path = checkpoint / "trainer_state.json"
            state = json.loads(state_path.read_text())
            if state["global_step"] != 500 or state["max_steps"] != 500:
                raise AssertionError(
                    f"Unexpected trainer runtime state for {run_name}: "
                    f"global_step={state['global_step']}, max_steps={state['max_steps']}"
                )

            # PyTorch 2.6 defaults to weights_only=True. These are trusted local
            # Hugging Face TrainingArguments objects, so the opt-in is explicit.
            args_path = final_model / "training_args.bin"
            training_args = torch.load(
                args_path, map_location="cpu", weights_only=False
            )
            if training_args.seed != seed:
                raise AssertionError(
                    f"Seed mismatch for {run_name}: {training_args.seed} != {seed}"
                )
            for field, expected in EXPECTED_ARGS.items():
                actual = getattr(training_args, field)
                if actual != expected:
                    raise AssertionError(
                        f"Unexpected {field} for {run_name}: "
                        f"{actual!r} != {expected!r}"
                    )
            checked += 1

    return checked


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="Repository root (default: inferred from this script)",
    )
    args = parser.parse_args()
    repo_root = args.repo_root.resolve()
    manifest = (
        repo_root
        / "experiments"
        / "milestone3"
        / "provenance"
        / "post_audit_cleanup_before_sha256.txt"
    )

    artifact_count = verify_preservation_manifest(repo_root, manifest)
    run_count = verify_confirmatory_runs(repo_root)
    print(
        f"Integrity checks passed: {artifact_count} immutable files and "
        f"{run_count} confirmatory runs."
    )


if __name__ == "__main__":
    main()
