import hashlib
import json
import subprocess
from pathlib import Path

def hash_file(filepath):
    hasher = hashlib.sha256()
    with open(filepath, 'rb') as f:
        while chunk := f.read(8192):
            hasher.update(chunk)
    return hasher.hexdigest()

def get_git_commit():
    try:
        return subprocess.check_output(['git', 'rev-parse', 'HEAD']).decode('ascii').strip()
    except Exception:
        return "Unknown or not a git repository"

def get_git_dirty_status():
    try:
        status = subprocess.check_output(['git', 'status', '--porcelain']).decode('ascii').strip()
        return "dirty" if len(status) > 0 else "clean"
    except Exception:
        return "Unknown"

def main():
    print("Freezing hashes for Milestone 3...")
    hashes = {}
    
    # Files to hash
    files_to_hash = {
        "train_dataset": "experiments/milestone3/data/train_dataset.jsonl",
        "eval_dataset": "experiments/milestone3/data/eval_dataset.jsonl",
        "test_dataset": "experiments/milestone3/data/test_dataset.jsonl",
        "training_config": "configs/milestone3.yaml",
        "train_grpo_script": "scripts/train_grpo.py",
        "evaluate_script": "scripts/evaluate_milestone3.py",
        "reward_source_file": "src/math_reward_hacking/rewards/verifiers.py"
    }
    
    for key, filepath in files_to_hash.items():
        if Path(filepath).exists():
            hashes[key] = hash_file(filepath)
        else:
            hashes[key] = "FILE_NOT_FOUND"
            
    hashes["git_commit"] = get_git_commit()
    hashes["git_dirty_status"] = get_git_dirty_status()
    hashes["reward_definition_version"] = "v1.0 (verify_true_answer & compute_modulo_proxy_reward)"
    
    # Save frozen hashes
    output_path = Path("experiments/milestone3/milestone3_frozen_hashes.json")
    with open(output_path, "w") as f:
        json.dump(hashes, f, indent=2)
        
    print(f"Hashes successfully frozen to {output_path}")

if __name__ == "__main__":
    main()
