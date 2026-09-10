import json
from pathlib import Path

def compute_agreement(samples):
    total = len(samples)
    if total == 0:
        return 0.0, 0.0, 0, 0
        
    agreements = 0
    rewarded_incorrect = 0
    
    for s in samples:
        r = s.get('robust_reward', s.get('true_correctness', 0.0))
        p = s.get('proxy_reward', 0.0)
        if r == p:
            agreements += 1
        
        if p == 1.0 and r == 0.0:
            rewarded_incorrect += 1
            
    agreement_rate = agreements / total
    disagreement_rate = 1.0 - agreement_rate
    return agreement_rate, disagreement_rate, rewarded_incorrect, total


def main():
    print("--- Milestone 2 Archiving: Reward Agreement Analysis ---")
    
    # 1. Pretraining variance samples (from both robust and proxy runs)
    variance_paths = [
        Path("experiments/grpo/robust/variance_gate_samples.json"),
        Path("experiments/grpo/proxy/variance_gate_samples.json")
    ]
    
    variance_samples = []
    for p in variance_paths:
        if p.exists():
            with open(p, "r") as f:
                data = json.load(f)
                if isinstance(data, list):
                    if len(data) > 0 and "samples" in data[0]:
                        for group in data:
                            variance_samples.extend(group["samples"])
                    else:
                        variance_samples.extend(data)
                    
    print("\n[Pretraining Variance Samples]")
    agr, dis, rew_inc, tot = compute_agreement(variance_samples)
    print(f"robust_proxy_agreement_rate: {agr:.4f}")
    print(f"robust_proxy_disagreement_rate: {dis:.4f}")
    print(f"rewarded_incorrect_count: {rew_inc}")
    print(f"total_audited_completions: {tot}")

    # 2. Greedy held-out evaluation
    eval_path = Path("experiments/grpo/eval_results.json")
    if eval_path.exists():
        with open(eval_path, "r") as f:
            eval_data = json.load(f)
            
        eval_samples = []
        # aggregate across base, robust, proxy evaluations
        for condition, results in eval_data.items():
            eval_samples.extend(results["detailed_results"])
            
        print("\n[Greedy Held-Out Evaluation]")
        agr, dis, rew_inc, tot = compute_agreement(eval_samples)
        print(f"robust_proxy_agreement_rate: {agr:.4f}")
        print(f"robust_proxy_disagreement_rate: {dis:.4f}")
        print(f"rewarded_incorrect_count: {rew_inc}")
        print(f"total_audited_completions: {tot}")
        
    # We do not have training audit samples or sampled held-out evaluation persisted in Milestone 2
    print("\n[Training Audit Samples]")
    print("robust_proxy_agreement_rate: N/A")
    print("robust_proxy_disagreement_rate: N/A")
    print("rewarded_incorrect_count: N/A")
    print("total_audited_completions: 0")

    print("\n[Sampled Held-Out Evaluation]")
    print("robust_proxy_agreement_rate: N/A")
    print("robust_proxy_disagreement_rate: N/A")
    print("rewarded_incorrect_count: N/A")
    print("total_audited_completions: 0")

if __name__ == "__main__":
    main()
