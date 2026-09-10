import argparse
import json
import yaml
from pathlib import Path

from transformers import pipeline, AutoModelForCausalLM, AutoTokenizer
import torch

from math_reward_hacking.rewards.verifiers import verify_true_answer, compute_proxy_reward, parse_final_answer
from math_reward_hacking.evaluation.metrics import calculate_metrics, aggregate_metrics

def main():
    parser = argparse.ArgumentParser(description="Run baseline evaluation")
    parser.add_argument("--config", type=str, required=True, help="Path to YAML config file")
    args = parser.parse_args()
    
    with open(args.config, "r") as f:
        config = yaml.safe_load(f)
        
    dataset_path = Path(config.get("dataset_path", "experiments/default/dataset.jsonl"))
    results_path = Path(config.get("results_path", "experiments/default/results.json"))
    model_name = config.get("model_name", "Qwen/Qwen2.5-0.5B-Instruct")
    
    generation_seed = config.get("generation_seed", config.get("seed", 42))
    max_new_tokens = config.get("max_new_tokens", 128)
    do_sample = config.get("do_sample", False)
    
    dataset_dir = dataset_path.parent
    meta_path = dataset_dir / "dataset_metadata.json"
    
    if not dataset_path.exists():
        raise FileNotFoundError(f"Dataset not found at {dataset_path}. Run generate_data.py first.")
        
    requested_eval_size = None
    if meta_path.exists():
        with open(meta_path, "r") as f:
            metadata = json.load(f)
            requested_eval_size = metadata.get("requested_eval_size", None)
            
    # Load dataset
    dataset = []
    with open(dataset_path, "r") as f:
        for line in f:
            dataset.append(json.loads(line))
            
    generated_dataset_size = len(dataset)
    print(f"Loaded {generated_dataset_size} samples from {dataset_path}")
    
    # Assert counts
    if requested_eval_size is not None:
        assert generated_dataset_size == requested_eval_size, f"Generated size {generated_dataset_size} != Requested size {requested_eval_size}"
        
    print(f"Loading model {model_name}...")
    
    device = "cuda" if torch.cuda.is_available() else "cpu"
    if torch.backends.mps.is_available() and device == "cpu":
        device = "mps"

    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForCausalLM.from_pretrained(
        model_name, 
        torch_dtype=torch.float16 if device != "cpu" else torch.float32,
        low_cpu_mem_usage=True
    ).to(device)
    
    pipe = pipeline(
        "text-generation", 
        model=model, 
        tokenizer=tokenizer, 
        device=device
    )
    
    torch.manual_seed(generation_seed)
    
    detailed_results = []
    skipped_example_count = 0
    
    print("Starting evaluation...")
    for item in dataset:
        prompt = item["prompt"]
        ground_truth = str(item["answer"])
        
        messages = [
            {"role": "system", "content": "You are a helpful mathematical assistant."},
            {"role": "user", "content": prompt}
        ]
        
        # Explicitly apply chat template to ensure strict instruction format
        rendered_prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        
        try:
            gen_kwargs = {
                "max_new_tokens": max_new_tokens,
                "do_sample": do_sample,
                "return_full_text": False
            }
            if do_sample:
                if "temperature" in config:
                    gen_kwargs["temperature"] = config["temperature"]
                if "top_p" in config:
                    gen_kwargs["top_p"] = config["top_p"]

            # Using explicitly rendered string so pipeline treats it literally
            outputs = pipe(rendered_prompt, **gen_kwargs)
            response = outputs[0]["generated_text"]
        except Exception as e:
            print(f"Error during generation: {e}")
            skipped_example_count += 1
            continue
            
        true_score = verify_true_answer(response, ground_truth)
        proxy_score = compute_proxy_reward(response, ground_truth)
        
        metrics = calculate_metrics(true_score, proxy_score)
        
        parsed = parse_final_answer(response)
        
        res = {
            "problem_id": item["problem_id"],
            "prompt": prompt,
            "ground_truth": ground_truth,
            "model_response": response,
            "parsed_answer": parsed["value"],
            "parse_method": parsed["method"],
            **metrics
        }
        detailed_results.append(res)
        
    evaluated_example_count = len(detailed_results)
    
    if requested_eval_size is not None:
        assert evaluated_example_count == requested_eval_size, f"Evaluated count {evaluated_example_count} != Requested size {requested_eval_size}. Skipped: {skipped_example_count}"
        
    agg_metrics = aggregate_metrics(detailed_results)
    
    print("\nBaseline Results:")
    for k, v in agg_metrics.items():
        print(f"{k}: {v:.4f}")
        
    results_path.parent.mkdir(parents=True, exist_ok=True)
    
    output_data = {
        "model": model_name,
        "dataset_seed": config.get("dataset_seed", config.get("seed", 42)),
        "generation_seed": generation_seed,
        "requested_dataset_size": requested_eval_size,
        "generated_dataset_size": generated_dataset_size,
        "evaluated_example_count": evaluated_example_count,
        "skipped_example_count": skipped_example_count,
        "generation": {
            "max_new_tokens": max_new_tokens,
            "do_sample": do_sample,
        },
        "metrics": agg_metrics,
        "detailed_results": detailed_results
    }
    
    if do_sample:
        output_data["generation"]["temperature"] = config.get("temperature")
        output_data["generation"]["top_p"] = config.get("top_p")
        
    with open(results_path, "w") as f:
        json.dump(output_data, f, indent=2)
        
    print(f"\nSaved detailed results to {results_path}")

if __name__ == "__main__":
    main()
