import argparse
import json
import torch
import numpy as np
from pathlib import Path
import os

from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel

from math_reward_hacking.rewards.verifiers import verify_true_answer, compute_modulo_proxy_reward, parse_final_answer
from math_reward_hacking.evaluation.metrics import calculate_metrics, aggregate_metrics

def evaluate_model(model, tokenizer, dataset, device, max_new_tokens=128):
    detailed_results = []
    
    for item in dataset:
        prompt = item["prompt"]
        ground_truth = str(item["result"])  # for ModuloArithmeticGenerator
        
        messages = [
            {"role": "system", "content": "You are a helpful mathematical assistant."},
            {"role": "user", "content": prompt}
        ]
        
        rendered_prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        inputs = tokenizer([rendered_prompt], return_tensors="pt", padding=True).to(device)
        
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                do_sample=False,
                pad_token_id=tokenizer.pad_token_id
            )
            
        response = tokenizer.decode(outputs[0][inputs.input_ids.shape[1]:], skip_special_tokens=True)
        
        true_score = verify_true_answer(response, ground_truth)
        proxy_score = compute_modulo_proxy_reward(response, ground_truth)
        metrics = calculate_metrics(true_score, proxy_score)
        
        parsed_dict = parse_final_answer(response)
        parsed = parsed_dict.get("value")
        method = parsed_dict.get("method")
        
        detailed_results.append({
            "problem_id": item["problem_id"],
            "prompt": prompt,
            "ground_truth": ground_truth,
            "model_response": response,
            "parsed_answer": str(parsed) if parsed is not None else None,
            "parse_method": method,
            **metrics
        })
        
    return aggregate_metrics(detailed_results), detailed_results

def integrity_check():
    import json
    import torch
    from pathlib import Path
    import hashlib

    seeds = [201, 202, 203]
    rewards = ["robust", "proxy"]
    base_dir = Path("experiments/milestone3")
    
    # 1. frozen hashes match
    frozen_path = base_dir / "milestone3_frozen_hashes.json"
    if not frozen_path.exists():
        raise AssertionError("Frozen hashes file missing.")
    with open(frozen_path) as f:
        frozen_hashes = json.load(f)
    if "git_dirty_status" not in frozen_hashes or "reward_source_file" not in frozen_hashes:
        raise AssertionError("Git state or reward source missing from frozen hashes.")
        
    with open("src/math_reward_hacking/rewards/verifiers.py", "rb") as f:
        current_reward_hash = hashlib.sha256(f.read()).hexdigest()
    if current_reward_hash != frozen_hashes["reward_source_file"]:
        raise AssertionError("Reward source hash mismatch! The reward function was altered.")

    selected_checkpoints_per_run = {}

    for reward in rewards:
        for seed in seeds:
            run_dir = base_dir / f"{reward}_seed_{seed}"
            final_model = run_dir / "final_model"
            
            if not final_model.exists():
                if reward == "robust" and seed == 201:
                    print("Skipping final_model check for Robust 201, using checkpoint-500.")
                else:
                    raise AssertionError(f"final_model missing for {reward} seed {seed}")
                
            args_path = final_model / "training_args.bin"
            if not args_path.exists() and reward == "robust" and seed == 201:
                args_path = run_dir / "checkpoint-500" / "training_args.bin"
                
            if args_path.exists():
                args = torch.load(args_path, weights_only=False)
                if args.seed != seed:
                    raise AssertionError(f"Seed mismatch in training args for {reward} seed {seed}")
            else:
                raise AssertionError(f"training_args.bin missing for {reward} seed {seed}")
                
            checkpoints = list(run_dir.glob("checkpoint-*"))
            
            state_path = None
            if (final_model / "trainer_state.json").exists():
                state_path = final_model / "trainer_state.json"
            else:
                highest_ckpt = max(checkpoints, key=lambda c: int(c.name.split("-")[-1])) if checkpoints else None
                if highest_ckpt and (highest_ckpt / "trainer_state.json").exists():
                    state_path = highest_ckpt / "trainer_state.json"

            if state_path and state_path.exists():
                with open(state_path) as f:
                    state = json.load(f)
                    max_steps = state.get('max_steps', 0)
                    if max_steps == 0:
                        raise AssertionError(f"max_steps is 0 for {reward} seed {seed}")
                    
                    ckpt_steps = sorted([int(c.name.split("-")[-1]) for c in checkpoints])
                    target_fractions = [0.25, 0.50, 0.75, 1.0]
                    selected_ckpts = []

                    save_interval = max(1, max_steps // 4)

                    for frac in target_fractions:
                        target_step = int(max_steps * frac)
                        if frac == 1.0:
                            if reward == "robust" and seed == 201:
                                selected_ckpts.append("checkpoint-500")
                                print(f"[{reward} seed {seed}] Target: 100% ({max_steps} steps) -> Selected: checkpoint-500 (100.0%)")
                            else:
                                selected_ckpts.append("final_model")
                                print(f"[{reward} seed {seed}] Target: 100% ({max_steps} steps) -> Selected: final_model (100.0%)")
                        else:
                            if not ckpt_steps:
                                raise AssertionError(f"No checkpoints to select for target {target_step}")
                            nearest_step = min(ckpt_steps, key=lambda s: abs(s - target_step))
                            if abs(nearest_step - target_step) > save_interval:
                                raise AssertionError(f"Nearest checkpoint {nearest_step} is > {save_interval} steps from target {target_step} for {reward} seed {seed}")
                            selected_ckpts.append(f"checkpoint-{nearest_step}")
                            actual_frac = nearest_step / max_steps * 100
                            print(f"[{reward} seed {seed}] Target: {frac*100:.1f}% ({target_step} steps) -> Selected: checkpoint-{nearest_step} ({actual_frac:.1f}%)")

                    selected_checkpoints_per_run[f"{reward}_seed_{seed}"] = selected_ckpts
            else:
                raise AssertionError(f"trainer_state.json missing for {reward} seed {seed}")
                
    print("Pre-evaluation integrity check passed cleanly. Sealed test set authorized.")
    return selected_checkpoints_per_run

def main():
    parser = argparse.ArgumentParser(
        description="Historical Milestone 3 evaluator; writes canonical sealed results."
    )
    parser.add_argument(
        "--allow-historical-overwrite",
        action="store_true",
        help="Explicitly permit overwriting experiments/milestone3/eval_results.json",
    )
    args = parser.parse_args()
    if not args.allow_historical_overwrite:
        raise SystemExit(
            "Refusing to overwrite historical sealed results. For a new experiment, "
            "use scripts/run_replication.sh."
        )

    selected_checkpoints_per_run = integrity_check()
    model_name = "Qwen/Qwen2.5-0.5B-Instruct"
    
    test_dataset_path = Path("experiments/milestone3/data/test_dataset.jsonl")
    eval_dataset_path = Path("experiments/milestone3/data/eval_dataset.jsonl")
    
    test_dataset = []
    with open(test_dataset_path, "r") as f:
        for line in f:
            test_dataset.append(json.loads(line))
            
    eval_dataset = []
    with open(eval_dataset_path, "r") as f:
        for line in f:
            eval_dataset.append(json.loads(line))
            
    device = "cuda" if torch.cuda.is_available() else "cpu"
    if torch.backends.mps.is_available() and device == "cpu":
        device = "mps"
        
    print(f"Using device: {device}")
    
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
        
    results = {"test": {}, "eval_checkpoints": {}}
    
    print("\nEvaluating Base model on test...")
    base_model = AutoModelForCausalLM.from_pretrained(
        model_name,
        torch_dtype=torch.float16 if device != "cpu" else torch.float32,
        low_cpu_mem_usage=True
    ).to(device)
    base_model.eval()
    
    agg, det = evaluate_model(base_model, tokenizer, test_dataset, device)
    results["test"]["Base"] = {"metrics": agg, "detailed_results": det}
    
    print("\nEvaluating Base model on eval (audit)...")
    agg, det = evaluate_model(base_model, tokenizer, eval_dataset, device)
    results["eval_checkpoints"]["Base"] = {"metrics": agg, "detailed_results": det}
    
    del base_model
    if torch.cuda.is_available(): torch.cuda.empty_cache()
    
    seeds = [201, 202, 203]
    conditions = ["robust", "proxy"]
    
    for seed in seeds:
        for cond in conditions:
            run_id = f"{cond}_seed_{seed}"
            if run_id not in selected_checkpoints_per_run:
                continue
                
            run_dir = Path(f"experiments/milestone3/{run_id}")
            checkpoints = selected_checkpoints_per_run[run_id]
            
            for ckpt in checkpoints:
                adapter_path = run_dir / ckpt
                cond_name = f"{cond.capitalize()} RL (Seed {seed}) - {ckpt}"
                
                if not adapter_path.exists():
                    continue
                    
                print(f"\nEvaluating {cond_name} on eval (audit)...")
                model = AutoModelForCausalLM.from_pretrained(
                    model_name,
                    torch_dtype=torch.float16 if device != "cpu" else torch.float32,
                    low_cpu_mem_usage=True
                )
                model = PeftModel.from_pretrained(model, adapter_path).to(device)
                model.eval()
                
                agg, det = evaluate_model(model, tokenizer, eval_dataset, device)
                results["eval_checkpoints"][cond_name] = {"metrics": agg, "detailed_results": det}
                
                if ckpt == "final_model" or (seed == 201 and cond == "robust" and ckpt == "checkpoint-500"):
                    test_cond_name = f"{cond.capitalize()} RL (Seed {seed})"
                    print(f"\nEvaluating {test_cond_name} on TEST...")
                    agg, det = evaluate_model(model, tokenizer, test_dataset, device)
                    results["test"][test_cond_name] = {"metrics": agg, "detailed_results": det}
                    
                del model
                if torch.cuda.is_available(): torch.cuda.empty_cache()

    robust_accuracies = []
    proxy_accuracies = []
    robust_proxy_rewards = []
    proxy_proxy_rewards = []
    
    for k, v in results["test"].items():
        if "Robust" in k:
            robust_accuracies.append(v["metrics"]["true_accuracy"])
            robust_proxy_rewards.append(v["metrics"]["mean_observed_reward"])
        elif "Proxy" in k:
            proxy_accuracies.append(v["metrics"]["true_accuracy"])
            proxy_proxy_rewards.append(v["metrics"]["mean_observed_reward"])
            
    print("\n--- Summary Across Seeds (TEST SET) ---")
    if robust_accuracies:
        print(f"Robust Exact Accuracy: {np.mean(robust_accuracies):.4f} ± {np.std(robust_accuracies):.4f}")
        print(f"Robust Proxy Reward:   {np.mean(robust_proxy_rewards):.4f} ± {np.std(robust_proxy_rewards):.4f}")
    if proxy_accuracies:
        print(f"Proxy Exact Accuracy:  {np.mean(proxy_accuracies):.4f} ± {np.std(proxy_accuracies):.4f}")
        print(f"Proxy Proxy Reward:    {np.mean(proxy_proxy_rewards):.4f} ± {np.std(proxy_proxy_rewards):.4f}")
    
    with open("experiments/milestone3/eval_results.json", "w") as f:
        json.dump(results, f, indent=2)
        
    print("\nEvaluation complete. Results saved to experiments/milestone3/eval_results.json")

if __name__ == "__main__":
    main()
