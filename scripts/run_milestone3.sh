#!/usr/bin/env bash
set -euo pipefail

if [[ "${1:-}" != "--allow-historical-recovery" ]]; then
    echo "Historical recovery script: this writes canonical Milestone 3 paths." >&2
    echo "For a new experiment use: bash scripts/run_replication.sh <name> <model-commit-sha>" >&2
    echo "To deliberately resume the old recovery sequence, pass --allow-historical-recovery." >&2
    exit 2
fi

echo "Starting historical Milestone 3 recovery sequence (Seeds 201-203)"

echo "========================================================="
echo "PHASE 2 & 3: Sequential Training of Remaining Seeds"

echo "Running Proxy Seed 201..."
uv run python scripts/train_grpo.py \
    --config configs/milestone3.yaml \
    --reward proxy \
    --output_dir experiments/milestone3/proxy_seed_201 \
    --seed 201

echo "Running Robust Seed 202..."
uv run python scripts/train_grpo.py \
    --config configs/milestone3.yaml \
    --reward robust \
    --output_dir experiments/milestone3/robust_seed_202 \
    --seed 202

echo "Running Proxy Seed 202..."
uv run python scripts/train_grpo.py \
    --config configs/milestone3.yaml \
    --reward proxy \
    --output_dir experiments/milestone3/proxy_seed_202 \
    --seed 202

echo "Running Robust Seed 203..."
uv run python scripts/train_grpo.py \
    --config configs/milestone3.yaml \
    --reward robust \
    --output_dir experiments/milestone3/robust_seed_203 \
    --seed 203

echo "Running Proxy Seed 203..."
uv run python scripts/train_grpo.py \
    --config configs/milestone3.yaml \
    --reward proxy \
    --output_dir experiments/milestone3/proxy_seed_203 \
    --seed 203

echo "Milestone 3 training completed successfully."

echo "========================================================="
echo "PHASE 4: Evaluation"
uv run python scripts/evaluate_milestone3.py --allow-historical-overwrite

echo "========================================================="
echo "PHASE 5: Report Generation"
uv run python scripts/generate_report.py

echo "Milestone 3 full pipeline completed successfully."
