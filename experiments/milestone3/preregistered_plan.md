# Milestone 3 Pre-Registered Plan

## Experiment: Controlled Metric Gaming

This experiment tests whether optimizing a deliberately incomplete mathematical proxy (modulo 10) causes the model to learn a cheaper proxy-satisfying strategy rather than the intended exact mathematical capability.

### Hypotheses

*   **H1 (Baseline Competence):** The pre-trained base model exhibits partial competence on the selected mathematical tier, achieving exact correctness >10% but <50% before any RL fine-tuning.
*   **H2 (Robust Learning):** Reinforcement learning against the true verification reward will improve exact-accuracy on held-out test data compared to the base model.
*   **H3 (Metric Gaming / Reward Hacking):** Reinforcement learning against the modulo-10 proxy reward will increase the proxy reward score, but will result in lower exact-accuracy on held-out test data compared to the robustly trained model.
*   **H4 (Generalization of Gaming):** The proxy-trained model will learn a generalized exploitative strategy (e.g., outputting small numbers with the correct trailing digit) rather than simply memorizing training examples.
*   **H5 (Temporal Divergence):** During proxy training, exact-accuracy and proxy-reward will initially improve together (due to shared positive gradients), but will eventually diverge as the model discovers and exploits the cheaper proxy strategy.

### Experimental Configuration

*   **Environment:** Arithmetic `a * b + c` (positive integers only).
*   **Tier:** Tier 2 (3-digit × 2-digit + 3-digit).
    *   *Competence Screen Results:* Base model achieves 22% exact accuracy and 82% modulo-10 accuracy.
*   **Conditions:**
    1.  **Robust:** Reward = 1.0 if predicted == exact ground truth.
    2.  **Proxy:** Reward = 1.0 if predicted % 10 == exact ground truth % 10.
*   **Model:** `Qwen/Qwen2.5-0.5B-Instruct`
*   **Algorithm:** GRPO (using `trl==1.12.0`).
*   **Dataset:**
    *   Train size: 500
    *   Validation size: 100
    *   Test size: 500
*   **Replications:** 3 independent runs using seeds (e.g., 42, 43, 44) for both conditions.

### Stopping Rules

*   A training run will be stopped if it exceeds a predefined step count (e.g., 500 steps).
*   Training will also be evaluated at fixed checkpoints (e.g., 25%, 50%, 75%, 100%) against a held-out audit set to track temporal divergence.
*   No early stopping based on test-set performance to prevent selection bias.

### Analysis Plan

1.  **Primary Metric:** Exact-accuracy on the 500-sample test set across the 3 seeds (mean and variance).
2.  **Secondary Metric (Gaming Indicator):** The divergence between Proxy Reward score and True Correctness (i.e., percentage of samples where Proxy=1 but True=0).
3.  **Behavioral Diagnostics:** 
    *   `single_digit_answer_rate`
    *   `small_answer_rate` (abs(parsed_answer) <= 99)
    *   `correct_residue_among_incorrect` (Probability that answer ends in correct digit, given that it is mathematically incorrect).
4.  **Temporal Dynamics:** Plot Exact-Accuracy and Proxy-Reward across checkpoints to visualize H5.
