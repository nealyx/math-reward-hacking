from unittest.mock import patch
from scripts.train_grpo import get_robust_reward, get_proxy_reward

def test_robust_reward_isolation():
    prompts = ["prompt1", "prompt2"]
    completions = ["10", "abc"]
    answers = ["10", "15"]
    
    # Patch the modulo proxy actually imported by the training script. If the
    # robust condition calls it, the test must fail.
    with patch("scripts.train_grpo.compute_modulo_proxy_reward", side_effect=Exception("Proxy reward should not be called in robust condition!")):
        rewards = get_robust_reward(prompts, completions, answers)
        assert rewards[0] == 1.0 # 10 matches 10
        assert rewards[1] == 0.0 # abc does not match 15

def test_proxy_reward_isolation():
    prompts = ["prompt1", "prompt2"]
    completions = ["The answer is 10.", "x = 10 \n\n 100"]
    answers = ["10", "15"]
    
    # If the proxy condition calls the exact verifier, the test must fail.
    with patch("scripts.train_grpo.verify_true_answer", side_effect=Exception("True verifier should not be called in proxy condition!")):
        rewards = get_proxy_reward(prompts, completions, answers)
        assert rewards[0] == 1.0 # Proxy searches for "10", finds it
        assert rewards[1] == 0.0 # 15 is not found

def test_reward_message_unpacking():
    # TRL passes a list of dicts for completions
    prompts = ["p1"]
    completions = [[{"role": "assistant", "content": "x = 42"}]]
    answers = ["42"]
    
    r_robust = get_robust_reward(prompts, completions, answers)
    assert r_robust[0] == 1.0
    
    r_proxy = get_proxy_reward(prompts, completions, answers)
    assert r_proxy[0] == 1.0
