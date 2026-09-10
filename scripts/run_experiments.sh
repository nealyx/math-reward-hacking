#!/usr/bin/env bash
set -e

echo "Starting Milestone 2 sequential training..."

echo "==========================================="
echo "PHASE 1: Robust Reward Training"
echo "==========================================="
uv run python scripts/train_grpo.py --config configs/train_robust.yaml --reward robust

echo "==========================================="
echo "PHASE 2: Proxy Reward Training"
echo "==========================================="
uv run python scripts/train_grpo.py --config configs/train_proxy.yaml --reward proxy

echo "==========================================="
echo "PHASE 3: Final Evaluation"
echo "==========================================="
uv run python scripts/evaluate_checkpoints.py

echo "Milestone 2 completed successfully."
