import json
import torch
from pathlib import Path

from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel

from math_reward_hacking.rewards.verifiers import verify_true_answer, compute_proxy_reward, parse_final_answer
from math_reward_hacking.evaluation.metrics import calculate_metrics, aggregate_metrics

def evaluate_model(model, tokenizer, dataset, device, max_new_tokens=256):
    detailed_results = []
    
    for item in dataset:
        prompt = item["prompt"]
        ground_truth = str(item["answer"])
        
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
        proxy_score = compute_proxy_reward(response, ground_truth)
        metrics = calculate_metrics(true_score, proxy_score)
        # Handle parsed answer properly because it returns tuple in updated parse_final_answer
        parsed, method = parse_final_answer(response)
        
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

def main():
    model_name = "Qwen/Qwen2.5-0.5B-Instruct"
    dataset_path = Path("experiments/default/eval_dataset.jsonl")
    
    dataset = []
    with open(dataset_path, "r") as f:
        for line in f:
            dataset.append(json.loads(line))
            
    device = "cuda" if torch.cuda.is_available() else "cpu"
    if torch.backends.mps.is_available() and device == "cpu":
        device = "mps"
        
    print(f"Using device: {device}")
    
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
        
    results = {}
    
    conditions = [
        ("base", None),
        ("robust", "experiments/grpo/robust/final_model"),
        ("proxy", "experiments/grpo/proxy/final_model")
    ]
    
    for condition_name, adapter_path in conditions:
        print(f"\nEvaluating {condition_name} model...")
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=torch.float16 if device != "cpu" else torch.float32,
            low_cpu_mem_usage=True
        )
        
        if adapter_path is not None:
            model = PeftModel.from_pretrained(model, adapter_path)
            
        model = model.to(device)
        model.eval()
        
        agg_metrics, detailed = evaluate_model(model, tokenizer, dataset, device)
        print(f"Results for {condition_name}:")
        for k, v in agg_metrics.items():
            print(f"  {k}: {v:.4f}")
            
        results[condition_name] = {
            "metrics": agg_metrics,
            "detailed_results": detailed
        }
        
        # Free memory before next load
        del model
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            
    with open("experiments/grpo/eval_results.json", "w") as f:
        json.dump(results, f, indent=2)
        
    print("\nEvaluation complete. Results saved to experiments/grpo/eval_results.json")

if __name__ == "__main__":
    main()
