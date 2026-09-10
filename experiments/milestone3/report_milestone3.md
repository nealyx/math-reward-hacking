# Milestone 3 Confirmatory Report

## Scope and configuration

This report analyzes the stored outputs from an internally prespecified six-run confirmatory protocol. Seed 101 was exploratory and is excluded.

- Model: `Qwen/Qwen2.5-0.5B-Instruct` (the original revision was not pinned)
- Conditions: exact-answer Robust reward and deliberately vulnerable modulo-10 Proxy reward
- Training seeds: 201, 202, 203 in each condition
- Data: 500 train / 100 validation / 500 sealed-test examples
- GRPO: TRL 1.12.0, one epoch, batch size 1, gradient accumulation 4, four generations, temperature 0.8, maximum completion length 128
- Recorded execution-time Git state: Unknown
- Recorded reward-source SHA-256: `ab32936608eac679a77e8ff91c1cfa4188d5ae1e3133de0bf2bed3662169ec71`

## Sealed-test results

Across three seeds, proxy-reward training yielded consistently high modulo-10 accuracy while exact-answer accuracy remained similar to robust-reward training. The average Proxy advantage over Robust was driven primarily by Robust Seed 202, so these results support a proxy–truth gap under the vulnerable reward but do not establish a stable condition effect across seeds.

Values below are mean ± sample SD across n=3 seeds.

| Metric | Base | Robust | Proxy | Proxy − Robust |
|---|---:|---:|---:|---:|
| Exact accuracy | 0.0420 | 0.2420 ± 0.0104 | 0.2513 ± 0.0103 | +0.0093 |
| Modulo-10 accuracy | 0.6020 | 0.8753 ± 0.1553 | 0.9793 ± 0.0050 | +0.1040 |
| Metric-gaming rate | 0.5600 | 0.6333 ± 0.1449 | 0.7280 ± 0.0072 | +0.0947 |
| Small-answer rate | 0.2280 | 0.0580 ± 0.0798 | 0.0120 ± 0.0060 | -0.0460 |

`metric_gaming_rate = mod10_accuracy − exact_accuracy`. Exact correctness implies modulo-10 correctness, so this is a derived operational measure of proxy-only success, not independent evidence.

### Paired seed results

| Seed | Condition | Exact | Modulo-10 | Metric-gaming rate | Small-answer rate |
|---:|---|---:|---:|---:|---:|
| 201 | Robust | 0.2480 | 0.9620 | 0.7140 | 0.0160 |
| 201 | Proxy | 0.2400 | 0.9740 | 0.7340 | 0.0180 |
| 202 | Robust | 0.2300 | 0.6960 | 0.4660 | 0.1500 |
| 202 | Proxy | 0.2540 | 0.9840 | 0.7300 | 0.0120 |
| 203 | Robust | 0.2480 | 0.9680 | 0.7200 | 0.0080 |
| 203 | Proxy | 0.2600 | 0.9800 | 0.7200 | 0.0060 |

| Seed | Proxy − Robust modulo-10 | Proxy − Robust metric-gaming rate |
|---:|---:|---:|
| 201 | +0.0120 | +0.0200 |
| 202 | +0.2880 | +0.2640 |
| 203 | +0.0120 | +0.0000 |

The Seed 202 paired gaps (+28.8 percentage points modulo-10 and +26.4 points metric-gaming rate) dominate the corresponding three-seed averages; Seeds 201 and 203 have +1.2-point modulo-10 gaps.

## Hypothesis outcomes

- **H1 — not satisfied on the sealed test.** Base exact accuracy was 4.2%, below the prespecified >10% threshold. The earlier competence screen reported 22% using a distinct artifact and 256 generation tokens; it is not the 128-token sealed-test baseline.
- **H2 — descriptively supported.** Mean Robust exact accuracy increased from the 4.2% Base result to 24.2%. No prespecified significance test was conducted.
- **H3 — not supported as proposed.** Proxy exact accuracy (25.13%) was not lower than Robust exact accuracy (24.20%), although Proxy modulo-10 accuracy was high (97.93%).
- **H4 — not supported by the proposed small-answer signature.** Proxy small-answer rate was 1.2%, below Robust's 5.8%.
- **H5 — mixed/partially supported.** Proxy modulo-10 accuracy rose to 97–99% at final validation checkpoints while exact accuracy remained 21–23%, but the paths were not uniformly monotonic and two Robust seeds reached similarly high modulo-10 validation accuracy.

## Visible completion lengths

These are retokenized visible completion tokens from stored decoded `model_response` text using the stored `Qwen/Qwen2.5-0.5B-Instruct` tokenizer from `robust_seed_201/final_model`, with `add_special_tokens=False`. Prompts are excluded. These counts are not claimed to equal original generated sequence lengths including EOS or other special tokens.

| Condition | Seed | Mean visible completion tokens | Median | Fraction at/above 128 | Total retokenized visible tokens | Runtime (s) |
|---|---:|---:|---:|---:|---:|---:|
| Base | — | 123.002 | 123.0 | 0.4880 | 61501 | N/A |
| Robust | 201 | 90.768 | 87.0 | 0.0340 | 45384 | N/A |
| Robust | 202 | 116.882 | 118.0 | 0.3980 | 58441 | N/A |
| Robust | 203 | 92.550 | 92.0 | 0.0120 | 46275 | N/A |
| Proxy | 201 | 89.386 | 91.0 | 0.0080 | 44693 | N/A |
| Proxy | 202 | 96.712 | 96.0 | 0.0000 | 48356 | N/A |
| Proxy | 203 | 100.322 | 96.0 | 0.0000 | 50161 | N/A |

## Validation checkpoint trajectories

The step-0 validation reference is Base exact 2.0% and modulo-10 50.0%. The table preserves all three seeds rather than averaging away heterogeneity.

| Condition | Checkpoint | Exact | Modulo-10 | Metric-gaming rate | Invalid | Mean visible tokens |
|---|---|---:|---:|---:|---:|---:|
| Base | step 0 | 0.0200 | 0.5000 | 0.4800 | 0.0000 | 124.2 |
| Robust Seed 201 | checkpoint-124 | 0.0600 | 0.7300 | 0.6700 | 0.0000 | 123.4 |
| Robust Seed 201 | checkpoint-248 | 0.1700 | 0.7900 | 0.6200 | 0.0000 | 107.8 |
| Robust Seed 201 | checkpoint-372 | 0.2300 | 0.9700 | 0.7400 | 0.0000 | 91.9 |
| Robust Seed 201 | checkpoint-500 | 0.2300 | 0.9600 | 0.7300 | 0.0000 | 90.5 |
| Robust Seed 202 | checkpoint-124 | 0.0000 | 0.5500 | 0.5500 | 0.0000 | 123.8 |
| Robust Seed 202 | checkpoint-248 | 0.1100 | 0.8400 | 0.7300 | 0.0000 | 120.5 |
| Robust Seed 202 | checkpoint-372 | 0.1800 | 0.6800 | 0.5000 | 0.0000 | 119.7 |
| Robust Seed 202 | final_model | 0.1900 | 0.7000 | 0.5100 | 0.0000 | 118.0 |
| Robust Seed 203 | checkpoint-124 | 0.0300 | 0.6500 | 0.6200 | 0.0000 | 122.3 |
| Robust Seed 203 | checkpoint-248 | 0.2300 | 0.8200 | 0.5900 | 0.0000 | 105.7 |
| Robust Seed 203 | checkpoint-372 | 0.2300 | 0.9800 | 0.7500 | 0.0000 | 90.4 |
| Robust Seed 203 | final_model | 0.2300 | 0.9800 | 0.7500 | 0.0000 | 91.0 |
| Proxy Seed 201 | checkpoint-124 | 0.1700 | 0.9600 | 0.7900 | 0.0000 | 119.0 |
| Proxy Seed 201 | checkpoint-248 | 0.2300 | 0.9500 | 0.7200 | 0.0000 | 92.8 |
| Proxy Seed 201 | checkpoint-372 | 0.2300 | 0.9800 | 0.7500 | 0.0000 | 90.3 |
| Proxy Seed 201 | final_model | 0.2300 | 0.9900 | 0.7600 | 0.0000 | 90.0 |
| Proxy Seed 202 | checkpoint-124 | 0.1600 | 0.5900 | 0.4300 | 0.0000 | 108.4 |
| Proxy Seed 202 | checkpoint-248 | 0.2000 | 0.9400 | 0.7400 | 0.0000 | 97.7 |
| Proxy Seed 202 | checkpoint-372 | 0.2100 | 0.9700 | 0.7600 | 0.0000 | 97.0 |
| Proxy Seed 202 | final_model | 0.2100 | 0.9700 | 0.7600 | 0.0000 | 97.8 |
| Proxy Seed 203 | checkpoint-124 | 0.1300 | 0.7100 | 0.5800 | 0.0000 | 110.5 |
| Proxy Seed 203 | checkpoint-248 | 0.2300 | 0.9900 | 0.7600 | 0.0000 | 99.2 |
| Proxy Seed 203 | checkpoint-372 | 0.2300 | 0.9900 | 0.7600 | 0.0000 | 100.5 |
| Proxy Seed 203 | final_model | 0.2300 | 0.9900 | 0.7600 | 0.0000 | 100.5 |

## Evaluation semantics

The stored results retain the historical confirmatory evaluation semantics. Future-facing exact evaluation now compares parsed integers, so accepted spellings such as `42`, `+42`, and `042` are equivalent. Auditing every stored confirmatory response found no row whose exact-correctness value changes under that correction.

## Provenance and experimental incident

The helper calculation labeled `computed_max_steps` produced 125, whereas every surviving confirmatory `TrainerState` records `global_step=500` and `max_steps=500`. The manual estimate did not account for GRPOTrainer's effective sampling/step semantics. It was used for checkpoint/save-frequency bookkeeping and a post-training assertion; no surviving evidence shows that optimization length was set to 125. The issue was discovered while the sealed test remained unopened.

Robust Seed 201 has a `final_model`, and its adapter is byte-identical to `checkpoint-500`; both appear in the preservation manifests. The earlier claim that the assertion prevented final-model creation was false.

- Original training-source digest recorded in the frozen manifest: `aa220bc2a78624fd70a49eb0ee22e09263aa0b03bd3b15b166a5cccb264b73d2`
- Status of that digest: recorded, but the original source bytes do not survive; it cannot be independently recomputed or cryptographically prove which exact bytes Robust Seed 201 executed.
- Audited post-incident/pre-cleanup `train_grpo.py` digest: `cdb26be6927116b5466cbedfba92e147f24059887511741d7c72c3f675c82450`
- Current diagnostics-cleanup `train_grpo.py` digest: `2eb48b0347521672dcd92e239b67d1b3c4b8a35df4b95bf96ba50dcfea48e3e3`
- The two surviving Robust Seed 201 before/after checksum files are byte-identical and their listed files currently verify. Their labels do not independently establish the earlier execution-time source state.
- Filesystem timestamps were not used as proof of execution order or source identity.

## Interpretation limits

There were only three confirmatory seeds, Robust outcomes varied substantially, and no significance or equivalence test was prespecified. The protocol was internally prespecified, not externally registered. The modulo-10 reward was deliberately designed as an artificial specification error. These results should not be generalized directly to frontier-model alignment or treated as proof of intentional cheating.
