import argparse
import yaml
import json
import torch
import numpy as np
from pathlib import Path
from datasets import Dataset

from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import LoraConfig, get_peft_model
from trl import GRPOTrainer, GRPOConfig

from math_reward_hacking.rewards.verifiers import verify_true_answer, compute_modulo_proxy_reward

# Future-run diagnostics only. These values never enter a reward calculation.
visible_completion_token_counts = []
diagnostic_tokenizer = None
diagnostic_max_completion_length = 128


def record_visible_completion_length(content):
    """Retokenize decoded completion text without prompt or special tokens."""
    if diagnostic_tokenizer is None:
        return
    token_count = len(
        diagnostic_tokenizer.encode(content, add_special_tokens=False)
    )
    visible_completion_token_counts.append(token_count)

def get_robust_reward(prompts, completions, answer, **kwargs):
    """Reward function mapping to the true verifier."""
    rewards = []
    for completion, ground_truth in zip(completions, answer):
        # We assume single string completions from TRL.
        # Check if completions is a list of lists of dicts (messages) or list of strings.
        if isinstance(completion, list): # messages format
            # GRPO often passes completion as messages; we extract the assistant's content
            content = completion[-1]["content"] if len(completion) > 0 else ""
        else:
            content = completion
        
        score = verify_true_answer(content, str(ground_truth))
        rewards.append(float(score))
        record_visible_completion_length(content)
    return rewards

def get_proxy_reward(prompts, completions, answer, **kwargs):
    """Reward function mapping to the vulnerable proxy verifier."""
    rewards = []
    for completion, ground_truth in zip(completions, answer):
        if isinstance(completion, list):
            content = completion[-1]["content"] if len(completion) > 0 else ""
        else:
            content = completion
            
        score = compute_modulo_proxy_reward(content, str(ground_truth))
        rewards.append(float(score))
        record_visible_completion_length(content)
    return rewards


def load_jsonl_dataset(path):
    data = []
    with open(path, "r") as f:
        for line in f:
            data.append(json.loads(line))
    
    # Prepare in TRL expected format
    prompts = []
    answers = []
    
    for item in data:
        prompt_text = item["prompt"]
        messages = [
            {"role": "system", "content": "You are a helpful mathematical assistant."},
            {"role": "user", "content": prompt_text}
        ]
        prompts.append(messages)
        answers.append(str(item["answer"]))
        
    return Dataset.from_dict({"prompt": prompts, "answer": answers})


def main():
    global diagnostic_tokenizer, diagnostic_max_completion_length

    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=str, required=True)
    parser.add_argument("--reward", type=str, required=True, choices=["robust", "proxy"])
    parser.add_argument("--output_dir", type=str, default=None)
    parser.add_argument("--seed", type=int, default=None)
    args = parser.parse_args()
    
    with open(args.config, "r") as f:
        config = yaml.safe_load(f)
        
    model_name = config.get("model_name", "Qwen/Qwen2.5-0.5B-Instruct")
    dataset_dir = Path(config.get("dataset_dir", "experiments/default"))
    train_path = dataset_dir / "train_dataset.jsonl"
    eval_path = dataset_dir / "eval_dataset.jsonl"
    
    output_dir_str = args.output_dir if args.output_dir is not None else config.get("output_dir", f"experiments/train_{args.reward}")
    output_dir = Path(output_dir_str)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    seed = args.seed if args.seed is not None else config.get("seed", 42)
    
    print(f"Applying Seed = {seed}")
    print(f"Data Seed = {seed}")
    print(f"Torch Seed = {seed}")
    print(f"TRL/TrainingArguments Seed = {seed}")
    
    # Set seed for reproducibility if passed
    import random
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    
    print(f"Loading {model_name}...")
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
        

    
    # TRL GRPO configuration
    num_generations = config.get("num_generations", 4)
    max_completion_length = config.get("max_completion_length", 128)
    
    train_dataset = load_jsonl_dataset(train_path)
    eval_dataset = load_jsonl_dataset(eval_path)
    
    batch_size = config.get("batch_size", 1)
    grad_acc = config.get("gradient_accumulation_steps", 4)
    epochs = config.get("epochs", 1)
    
    diagnostic_tokenizer = tokenizer
    diagnostic_max_completion_length = max_completion_length
    
    training_args = GRPOConfig(
        output_dir=str(output_dir),
        seed=seed,
        learning_rate=config.get("learning_rate", 5e-6),
        num_train_epochs=epochs,
        per_device_train_batch_size=batch_size,
        gradient_accumulation_steps=grad_acc,
        max_completion_length=max_completion_length,
        num_generations=num_generations,
        temperature=config.get("temperature", 0.8),
        logging_steps=10,
        save_strategy="steps",
        # A ratio lets Trainer derive quarter-progress saves from its own
        # runtime step semantics. It replaces the historical manual estimate
        # of 125, which did not describe GRPOTrainer's observed 500 steps.
        save_steps=0.25,
        bf16=torch.cuda.is_bf16_supported() if torch.cuda.is_available() else False,
        fp16=not torch.cuda.is_bf16_supported() if torch.cuda.is_available() else False,
        remove_unused_columns=False,
    )
    
    # LoRA config
    peft_config = LoraConfig(
        r=config.get("lora_rank", 8),
        lora_alpha=config.get("lora_alpha", 16),
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
        task_type="CAUSAL_LM",
        bias="none",
        lora_dropout=config.get("lora_dropout", 0.05),
    )
    
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
        device_map="auto" if torch.cuda.is_available() else None
    )
    

        
    # Setup reward function
    reward_funcs = [get_robust_reward] if args.reward == "robust" else [get_proxy_reward]
    
    trainer = GRPOTrainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=eval_dataset,
        reward_funcs=reward_funcs,
        peft_config=peft_config,
    )
    
    print(f"Starting {args.reward.upper()} GRPO training...")
    trainer.train()
    
    trainer.save_model(str(output_dir / "final_model"))
    print(f"Finished training and saved to {output_dir / 'final_model'}")
    
    # Dump metrics
    if visible_completion_token_counts:
        metrics = {
            "mean_visible_completion_tokens": float(
                np.mean(visible_completion_token_counts)
            ),
            "median_visible_completion_tokens": float(
                np.median(visible_completion_token_counts)
            ),
            "fraction_visible_completions_at_or_above_max_completion_length": float(
                np.mean(
                    np.asarray(visible_completion_token_counts)
                    >= diagnostic_max_completion_length
                )
            ),
            "total_retained_visible_completion_tokens": int(
                np.sum(visible_completion_token_counts)
            ),
            "reward_function_completions_observed": len(
                visible_completion_token_counts
            ),
            "completion_count_semantics": (
                "Decoded completions observed by the single active reward function; "
                "counts are not inferred from optimizer steps."
            ),
            "token_count_semantics": (
                "Visible decoded completion text retokenized with the training "
                "tokenizer, add_special_tokens=False; prompt and original EOS/special "
                "tokens are excluded."
            ),
            "global_steps_taken": trainer.state.global_step,
            "trainer_state_max_steps": trainer.state.max_steps,
        }
        with open(output_dir / "training_generation_metrics.json", "w") as f:
            json.dump(metrics, f, indent=2)

if __name__ == "__main__":
    main()
