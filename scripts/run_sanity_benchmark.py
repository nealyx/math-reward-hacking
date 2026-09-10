import json
from pathlib import Path
from transformers import pipeline, AutoModelForCausalLM, AutoTokenizer
import torch
from math_reward_hacking.rewards.verifiers import verify_true_answer, parse_final_answer

SANITY_EQUATIONS = [
    {"problem_id": "sanity_1", "prompt": "Solve the following linear equation for x. Give your final answer clearly as a single integer.\n\nx + 2 = 5", "solution": "3"},
    {"problem_id": "sanity_2", "prompt": "Solve the following linear equation for x. Give your final answer clearly as a single integer.\n\n2x = 10", "solution": "5"},
    {"problem_id": "sanity_3", "prompt": "Solve the following linear equation for x. Give your final answer clearly as a single integer.\n\n3x + 1 = 10", "solution": "3"},
    {"problem_id": "sanity_4", "prompt": "Solve the following linear equation for x. Give your final answer clearly as a single integer.\n\n4x - 8 = 12", "solution": "5"},
    {"problem_id": "sanity_5", "prompt": "Solve the following linear equation for x. Give your final answer clearly as a single integer.\n\n-2x + 3 = 11", "solution": "-4"},
    {"problem_id": "sanity_6", "prompt": "Solve the following linear equation for x. Give your final answer clearly as a single integer.\n\n5x + 5 = 20", "solution": "3"},
    {"problem_id": "sanity_7", "prompt": "Solve the following linear equation for x. Give your final answer clearly as a single integer.\n\nx - 7 = 2", "solution": "9"},
    {"problem_id": "sanity_8", "prompt": "Solve the following linear equation for x. Give your final answer clearly as a single integer.\n\n-x + 4 = 1", "solution": "3"},
    {"problem_id": "sanity_9", "prompt": "Solve the following linear equation for x. Give your final answer clearly as a single integer.\n\n10x = 100", "solution": "10"},
    {"problem_id": "sanity_10", "prompt": "Solve the following linear equation for x. Give your final answer clearly as a single integer.\n\n3x - 3 = 0", "solution": "1"},
]

def main():
    model_name = "Qwen/Qwen2.5-0.5B-Instruct"
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
    
    torch.manual_seed(42)
    
    correct_count = 0
    results_out = []
    
    print("Evaluating Sanity Benchmark...")
    for item in SANITY_EQUATIONS:
        prompt = item["prompt"]
        ground_truth = str(item["solution"])
        
        messages = [
            {"role": "system", "content": "You are a helpful mathematical assistant."},
            {"role": "user", "content": prompt}
        ]
        
        rendered_prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        
        try:
            outputs = pipe(
                rendered_prompt, 
                max_new_tokens=128,
                do_sample=False,
                return_full_text=False
            )
            response = outputs[0]["generated_text"]
        except Exception as e:
            print(f"Error during generation: {e}")
            response = ""
            
        true_score = verify_true_answer(response, ground_truth)
        parsed = parse_final_answer(response)
        
        results_out.append({
            "problem": item["prompt"].split("\n\n")[-1],
            "expected": ground_truth,
            "parsed": parsed["value"],
            "correct": true_score == 1.0,
            "response": response
        })
        
        if true_score == 1.0:
            correct_count += 1
            
    accuracy = correct_count / len(SANITY_EQUATIONS)
    print(f"\nSanity Benchmark Accuracy: {accuracy * 100:.1f}% ({correct_count}/{len(SANITY_EQUATIONS)})")
    
    print("\nDetailed breakdown:")
    for res in results_out:
        status = "PASS" if res["correct"] else "FAIL"
        print(f"[{status}] Eq: {res['problem']:<12} Expected: {res['expected']:<4} Parsed: {str(res['parsed']):<4}")

    if accuracy == 0.0:
        print("\nWARNING: Base model failed to answer ANY sanity equations correctly.")
    else:
        print("\nSUCCESS: Base model demonstrated nonzero mathematical competence.")

if __name__ == "__main__":
    main()
