#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 2 ]]; then
    echo "Usage: bash scripts/run_replication.sh <name> <40-char-qwen-commit-sha>" >&2
    exit 2
fi

REPLICATION_NAME="$1"
MODEL_REVISION="$2"
REPLICATION_DIR="experiments/replications/${REPLICATION_NAME}"
TRAINING_SEEDS=(201 202 203)

if [[ ! "$REPLICATION_NAME" =~ ^[A-Za-z0-9._-]+$ ]]; then
    echo "Replication name contains unsupported characters." >&2
    exit 2
fi
if [[ ! "$MODEL_REVISION" =~ ^[0-9a-fA-F]{40}$ ]]; then
    echo "Model revision must be a full 40-character Hugging Face commit SHA." >&2
    exit 2
fi
if [[ -e "$REPLICATION_DIR" ]]; then
    echo "Refusing to overwrite existing replication: $REPLICATION_DIR" >&2
    exit 1
fi

uv run python scripts/prepare_replication.py "$REPLICATION_NAME" "$MODEL_REVISION"

for SEED in "${TRAINING_SEEDS[@]}"; do
    for REWARD in robust proxy; do
        uv run python scripts/train_grpo.py \
            --config "$REPLICATION_DIR/replication_config.yaml" \
            --reward "$REWARD" \
            --output_dir "$REPLICATION_DIR/${REWARD}_seed_${SEED}" \
            --seed "$SEED"
    done
done

# The fresh test split is first evaluated only after all six new runs finish.
uv run python scripts/evaluate_replication.py "$REPLICATION_NAME" \
    --seeds "${TRAINING_SEEDS[@]}"

echo "Fresh replication complete: $REPLICATION_DIR"
