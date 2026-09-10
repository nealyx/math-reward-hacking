import json
import torch
from pathlib import Path

from transformers import AutoModelForCausalLM, AutoTokenizer

from math_reward_hacking.environments.modulo_arithmetic import ModuloArithmeticGenerator
from math_reward_hacking.rewards.verifiers import verify_true_answer, compute_modulo_proxy_reward, parse_final_answer

def main():
    model_name = "Qwen/Qwen2.5-0.5B-Instruct"
    num_samples_per_tier = 50
    device = "cuda" if torch.cuda.is_available() else "cpu"
    if torch.backends.mps.is_available() and device == "cpu":
        device = "mps"
        
    print(f"Using device: {device}")
    
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
        
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        torch_dtype=torch.float16 if device != "cpu" else torch.float32,
        low_cpu_mem_usage=True
    ).to(device)
    model.eval()
    
    results = {}

    for tier in [1, 2, 3, 4]:
        print(f"\n--- Running Competence Screen for Tier {tier} ---")
        generator = ModuloArithmeticGenerator(seed=42 + tier, tier=tier)
        dataset = generator.generate_dataset(num_samples_per_tier)
        
        exact_correct = 0
        mod10_correct = 0
        invalid_output = 0
        
        for item in dataset:
            prompt = item["prompt"]
            ground_truth = str(item["result"])
            
            messages = [
                {"role": "system", "content": "You are a helpful mathematical assistant."},
                {"role": "user", "content": prompt}
            ]
            
            rendered_prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
            inputs = tokenizer([rendered_prompt], return_tensors="pt", padding=True).to(device)
            
            with torch.no_grad():
                outputs = model.generate(
                    **inputs,
                    max_new_tokens=256,
                    do_sample=False,
                    pad_token_id=tokenizer.pad_token_id
                )
                
            response = tokenizer.decode(outputs[0][inputs.input_ids.shape[1]:], skip_special_tokens=True)
            
            exact_reward = verify_true_answer(response, ground_truth)
            mod10_reward = compute_modulo_proxy_reward(response, ground_truth)
            parsed = parse_final_answer(response)
            
            if exact_reward == 1.0:
                exact_correct += 1
            if mod10_reward == 1.0:
                mod10_correct += 1
            if parsed["value"] is None:
                invalid_output += 1
                
        exact_accuracy = exact_correct / num_samples_per_tier
        mod10_accuracy = mod10_correct / num_samples_per_tier
        invalid_rate = invalid_output / num_samples_per_tier
        
        print(f"Tier {tier} Results:")
        print(f"  Exact Accuracy:  {exact_accuracy:.2f}")
        print(f"  Mod10 Accuracy:  {mod10_accuracy:.2f}")
        print(f"  Invalid Output:  {invalid_rate:.2f}")
        
        results[tier] = {
            "exact_accuracy": exact_accuracy,
            "mod10_accuracy": mod10_accuracy,
            "invalid_output_rate": invalid_rate
        }
        
    print("\n[Competence Screen Summary]")
    for tier, res in results.items():
        print(f"Tier {tier}: Exact={res['exact_accuracy']:.2f}, Mod10={res['mod10_accuracy']:.2f}, Invalid={res['invalid_output_rate']:.2f}")
        
if __name__ == "__main__":
    main()
