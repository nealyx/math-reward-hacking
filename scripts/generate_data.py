import argparse
import json
import yaml
import os
import hashlib
from pathlib import Path
from math_reward_hacking.environments.linear_equations import LinearEquationGenerator
from math_reward_hacking.environments.modulo_arithmetic import ModuloArithmeticGenerator

def _hash_instance(item):
    """Hash the canonical features of an instance to check uniqueness."""
    # Handle different environments
    if "equation" in item and "*" in item["equation"]:
        a, b, c, x = item["a"], item["b"], item["c"], item["answer"]
    else:
        a, b, c, x = item.get("a", 0), item.get("b", 0), item.get("c", 0), item.get("answer", "")
    return f"{a}_{b}_{c}_{x}"

def main():
    parser = argparse.ArgumentParser(description="Generate dataset for Math Reward Hacking")
    parser.add_argument("--config", type=str, required=True, help="Path to YAML config file")
    args = parser.parse_args()
    
    with open(args.config, "r") as f:
        config = yaml.safe_load(f)
        
    train_seed = config.get("train_seed", 42)
    eval_seed = config.get("eval_seed", 43)
    train_size = config.get("train_size", 50)
    eval_size = config.get("eval_size", 20)
    test_size = config.get("test_size", 0)  # Added test split
    environment = config.get("environment", "linear_equations")
    tier = config.get("tier", 1)
    
    out_dir = Path(config.get("dataset_dir", "experiments/default"))
    out_dir.mkdir(parents=True, exist_ok=True)
    
    def get_generator(seed):
        if environment == "modulo_arithmetic":
            return ModuloArithmeticGenerator(seed=seed, tier=tier)
        else:
            return LinearEquationGenerator(seed=seed)
            
    # Generate splits
    train_generator = get_generator(train_seed)
    train_dataset = train_generator.generate_dataset(train_size * 2) 
    
    eval_generator = get_generator(eval_seed)
    eval_dataset = eval_generator.generate_dataset(eval_size * 2)
    
    if test_size > 0:
        test_seed = config.get("test_seed", 44)
        test_generator = get_generator(test_seed)
        test_dataset = test_generator.generate_dataset(test_size * 2)
    else:
        test_dataset = []
    
    # Filter and ensure uniqueness and no-overlap
    train_final = []
    eval_final = []
    test_final = []
    
    train_hashes = set()
    for item in train_dataset:
        if len(train_final) >= train_size:
            break
        h = _hash_instance(item)
        if h not in train_hashes:
            train_hashes.add(h)
            train_final.append(item)
            
    eval_hashes = set()
    for item in eval_dataset:
        if len(eval_final) >= eval_size:
            break
        h = _hash_instance(item)
        if h not in train_hashes and h not in eval_hashes:
            eval_hashes.add(h)
            eval_final.append(item)
            
    test_hashes = set()
    for item in test_dataset:
        if len(test_final) >= test_size:
            break
        h = _hash_instance(item)
        if h not in train_hashes and h not in eval_hashes and h not in test_hashes:
            test_hashes.add(h)
            test_final.append(item)
            
    assert len(train_final) == train_size, f"Could not generate enough unique train examples: {len(train_final)} < {train_size}"
    assert len(eval_final) == eval_size, f"Could not generate enough disjoint eval examples: {len(eval_final)} < {eval_size}"
    if test_size > 0:
        assert len(test_final) == test_size, f"Could not generate enough disjoint test examples: {len(test_final)} < {test_size}"
    
    # Calculate overall dataset hash representation
    train_instance_hash = hashlib.md5("".join(sorted(list(train_hashes))).encode()).hexdigest()
    eval_instance_hash = hashlib.md5("".join(sorted(list(eval_hashes))).encode()).hexdigest()
    
    train_path = out_dir / "train_dataset.jsonl"
    eval_path = out_dir / "eval_dataset.jsonl"
    meta_path = out_dir / "dataset_metadata.json"
    
    with open(train_path, "w") as f:
        for item in train_final:
            f.write(json.dumps(item) + "\n")
            
    with open(eval_path, "w") as f:
        for item in eval_final:
            f.write(json.dumps(item) + "\n")
            
    if test_size > 0:
        test_path = out_dir / "test_dataset.jsonl"
        with open(test_path, "w") as f:
            for item in test_final:
                f.write(json.dumps(item) + "\n")
            
    metadata = {
        "train_seed": train_seed,
        "eval_seed": eval_seed,
        "requested_train_size": train_size,
        "requested_eval_size": eval_size,
        "requested_test_size": test_size,
        "generated_train_size": len(train_final),
        "generated_eval_size": len(eval_final),
        "generated_test_size": len(test_final),
        "train_instance_hash": train_instance_hash,
        "eval_instance_hash": eval_instance_hash,
    }
    
    with open(meta_path, "w") as f:
        json.dump(metadata, f, indent=2)
            
    print(f"Generated {len(train_final)} train samples and {len(eval_final)} eval samples in {out_dir}")
    if test_size > 0:
        print(f"Generated {len(test_final)} test samples")
    print(f"Metadata saved to {meta_path}")

if __name__ == "__main__":
    main()
