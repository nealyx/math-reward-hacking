# Systematically selected diagnostic examples

Choose the lowest frozen problem ID per model and prespecified stratum. Eligibility counts refer to unique problem IDs, not independent training runs. Empty strata are preserved. A response may appear in several strata; this does not create extra observations. Frozen parser rejection can reflect restrictive grammar rather than an absent understandable semantic answer.

The persistent proxy-only stratum requires terminal proxy-only correctness at all three caps and EOS at 512. The no-improvement stratum means exact-incorrect at all three caps. Numeric-boundary flags identify lexical parsing risks, not an arithmetic judgement. No LLM judges arithmetic truth.

[Complete selected records with token IDs and character spans](results/representative_examples.json).

| Model | Stratum | Eligible IDs | Selected ID |
|---|---|---|---|
| Base | cap_without_eos_then_terminal_answer | 262 | 0 |
| Base | final_already_present_but_wrong_at_128 | 221 | 2 |
| Base | legacy_only_credit_no_terminal_answer | 65 | 5 |
| Base | grouped_or_prefix_disagreement | 5 | 38 |
| Base | persistent_proxy_only_eos_at_512 | 218 | 2 |
| Base | no_exact_improvement_at_any_budget | 351 | 1 |
| Exact 201 | cap_without_eos_then_terminal_answer | 21 | 6 |
| Exact 201 | final_already_present_but_wrong_at_128 | 341 | 1 |
| Exact 201 | legacy_only_credit_no_terminal_answer | 16 | 38 |
| Exact 201 | grouped_or_prefix_disagreement | 10 | 24 |
| Exact 201 | persistent_proxy_only_eos_at_512 | 340 | 1 |
| Exact 201 | no_exact_improvement_at_any_budget | 366 | 1 |
| Modulo 201 | cap_without_eos_then_terminal_answer | 1 | 175 |
| Modulo 201 | final_already_present_but_wrong_at_128 | 371 | 1 |
| Modulo 201 | legacy_only_credit_no_terminal_answer | 6 | 38 |
| Modulo 201 | grouped_or_prefix_disagreement | 34 | 15 |
| Modulo 201 | persistent_proxy_only_eos_at_512 | 364 | 1 |
| Modulo 201 | no_exact_improvement_at_any_budget | 377 | 1 |
| Exact 202 | cap_without_eos_then_terminal_answer | 193 | 1 |
| Exact 202 | final_already_present_but_wrong_at_128 | 205 | 2 |
| Exact 202 | legacy_only_credit_no_terminal_answer | 70 | 1 |
| Exact 202 | grouped_or_prefix_disagreement | 2 | 77 |
| Exact 202 | persistent_proxy_only_eos_at_512 | 202 | 2 |
| Exact 202 | no_exact_improvement_at_any_budget | 376 | 1 |
| Modulo 202 | cap_without_eos_then_terminal_answer | 0 | absent |
| Modulo 202 | final_already_present_but_wrong_at_128 | 361 | 1 |
| Modulo 202 | legacy_only_credit_no_terminal_answer | 10 | 38 |
| Modulo 202 | grouped_or_prefix_disagreement | 48 | 0 |
| Modulo 202 | persistent_proxy_only_eos_at_512 | 358 | 1 |
| Modulo 202 | no_exact_improvement_at_any_budget | 371 | 1 |
| Exact 203 | cap_without_eos_then_terminal_answer | 9 | 6 |
| Exact 203 | final_already_present_but_wrong_at_128 | 356 | 1 |
| Exact 203 | legacy_only_credit_no_terminal_answer | 5 | 6 |
| Exact 203 | grouped_or_prefix_disagreement | 20 | 15 |
| Exact 203 | persistent_proxy_only_eos_at_512 | 352 | 1 |
| Exact 203 | no_exact_improvement_at_any_budget | 364 | 1 |
| Modulo 203 | cap_without_eos_then_terminal_answer | 0 | absent |
| Modulo 203 | final_already_present_but_wrong_at_128 | 364 | 1 |
| Modulo 203 | legacy_only_credit_no_terminal_answer | 6 | 38 |
| Modulo 203 | grouped_or_prefix_disagreement | 28 | 15 |
| Modulo 203 | persistent_proxy_only_eos_at_512 | 361 | 1 |
| Modulo 203 | no_exact_improvement_at_any_budget | 370 | 1 |

## Base cap without eos then terminal answer

Eligible problem IDs: 262.

Problem 0: `206 × 90 + 334`. Integer target: **18874**.

| Cap | Original new tokens | Actual stopping reason | Generate s |
|---|---|---|---|
| 128 | 128 | token_limit_without_eos | 3.708 |
| 256 | 140 | eos_before_limit | 3.384 |
| 512 | 140 | eos_before_limit | 3.350 |

| Cap | Policy | Value | Method | Status | Exact | Modulo | Proxy-only |
|---|---|---|---|---|---|---|---|
| 128 | legacy | 33 | last_integer | accepted_legacy_answer | 0 | 0 | 0 |
| 128 | terminal | None | None | missing_terminal_answer | 0 | 0 | 0 |
| 128 | declared | None | None | missing_terminal_answer | 0 | 0 | 0 |
| 256 | legacy | 18874 | last_integer | accepted_legacy_answer | 1 | 1 | 0 |
| 256 | terminal | 18874 | natural_language_conclusion | accepted_terminal_answer | 1 | 1 | 0 |
| 256 | declared | None | None | missing_terminal_answer | 0 | 0 | 0 |
| 512 | legacy | 18874 | last_integer | accepted_legacy_answer | 1 | 1 | 0 |
| 512 | terminal | 18874 | natural_language_conclusion | accepted_terminal_answer | 1 | 1 | 0 |
| 512 | declared | None | None | missing_terminal_answer | 0 | 0 | 0 |

Readable completion at cap(s) 128:

````text
To calculate the exact value of \(206 \times 90 + 334\), we will follow these steps:

1. **Multiply 206 by 90:**
   \[
   206 \times 90 = 18540
   \]

2. **Add 334 to the result from step 1:**
   \[
   18540 + 334 = 18874
   \]

Therefore, the exact value of \(206 \times 90 + 33
````

Readable completion at cap(s) 256, 512:

````text
To calculate the exact value of \(206 \times 90 + 334\), we will follow these steps:

1. **Multiply 206 by 90:**
   \[
   206 \times 90 = 18540
   \]

2. **Add 334 to the result from step 1:**
   \[
   18540 + 334 = 18874
   \]

Therefore, the exact value of \(206 \times 90 + 334\) is \(18874\).
````

## Base final already present but wrong at 128

Eligible problem IDs: 221.

Problem 2: `297 × 82 + 118`. Integer target: **24472**.

| Cap | Original new tokens | Actual stopping reason | Generate s |
|---|---|---|---|
| 128 | 119 | eos_before_limit | 2.886 |
| 256 | 119 | eos_before_limit | 2.917 |
| 512 | 119 | eos_before_limit | 2.782 |

| Cap | Policy | Value | Method | Status | Exact | Modulo | Proxy-only |
|---|---|---|---|---|---|---|---|
| 128 | legacy | 24152 | last_integer | accepted_legacy_answer | 0 | 1 | 1 |
| 128 | terminal | 24152 | natural_language_conclusion | accepted_terminal_answer | 0 | 1 | 1 |
| 128 | declared | None | None | missing_terminal_answer | 0 | 0 | 0 |
| 256 | legacy | 24152 | last_integer | accepted_legacy_answer | 0 | 1 | 1 |
| 256 | terminal | 24152 | natural_language_conclusion | accepted_terminal_answer | 0 | 1 | 1 |
| 256 | declared | None | None | missing_terminal_answer | 0 | 0 | 0 |
| 512 | legacy | 24152 | last_integer | accepted_legacy_answer | 0 | 1 | 1 |
| 512 | terminal | 24152 | natural_language_conclusion | accepted_terminal_answer | 0 | 1 | 1 |
| 512 | declared | None | None | missing_terminal_answer | 0 | 0 | 0 |

Readable completion at cap(s) 128, 256, 512:

````text
To calculate the exact value of \(297 \times 82 + 118\), we can break it down into simpler steps.

First, let's perform the multiplication:

\[297 \times 82 = 24034\]

Now, add 118 to this result:

\[24034 + 118 = 24152\]

So, the exact value of \(297 \times 82 + 118\) is **24152**.
````

## Base legacy only credit no terminal answer

Eligible problem IDs: 65.

Problem 5: `241 × 20 + 177`. Integer target: **4997**.

| Cap | Original new tokens | Actual stopping reason | Generate s |
|---|---|---|---|
| 128 | 128 | token_limit_without_eos | 3.029 |
| 256 | 136 | eos_before_limit | 3.415 |
| 512 | 136 | eos_before_limit | 3.215 |

| Cap | Policy | Value | Method | Status | Exact | Modulo | Proxy-only |
|---|---|---|---|---|---|---|---|
| 128 | legacy | 177 | last_integer | accepted_legacy_answer | 0 | 1 | 1 |
| 128 | terminal | None | None | missing_terminal_answer | 0 | 0 | 0 |
| 128 | declared | None | None | missing_terminal_answer | 0 | 0 | 0 |
| 256 | legacy | 5097 | last_integer | accepted_legacy_answer | 0 | 1 | 1 |
| 256 | terminal | 5097 | natural_language_conclusion | accepted_terminal_answer | 0 | 1 | 1 |
| 256 | declared | None | None | missing_terminal_answer | 0 | 0 | 0 |
| 512 | legacy | 5097 | last_integer | accepted_legacy_answer | 0 | 1 | 1 |
| 512 | terminal | 5097 | natural_language_conclusion | accepted_terminal_answer | 0 | 1 | 1 |
| 512 | declared | None | None | missing_terminal_answer | 0 | 0 | 0 |

Readable completion at cap(s) 128:

````text
To calculate the exact value of \(241 \times 20 + 177\), we will follow these steps:

1. **Multiply 241 by 20:**
   \[
   241 \times 20 = 4820
   \]

2. **Add 177 to the result from step 1:**
   \[
   4820 + 177 = 5097
   \]

Therefore, the exact value of \(241 \times 20 + 177\) is
````

Readable completion at cap(s) 256, 512:

````text
To calculate the exact value of \(241 \times 20 + 177\), we will follow these steps:

1. **Multiply 241 by 20:**
   \[
   241 \times 20 = 4820
   \]

2. **Add 177 to the result from step 1:**
   \[
   4820 + 177 = 5097
   \]

Therefore, the exact value of \(241 \times 20 + 177\) is \(5097\).
````

## Base grouped or prefix disagreement

Eligible problem IDs: 5.

Problem 38: `687 × 57 + 930`. Integer target: **40089**.

| Cap | Original new tokens | Actual stopping reason | Generate s |
|---|---|---|---|
| 128 | 123 | eos_before_limit | 3.036 |
| 256 | 123 | eos_before_limit | 3.168 |
| 512 | 123 | eos_before_limit | 2.879 |

| Cap | Policy | Value | Method | Status | Exact | Modulo | Proxy-only |
|---|---|---|---|---|---|---|---|
| 128 | legacy | 49 | last_integer | accepted_legacy_answer | 0 | 1 | 1 |
| 128 | terminal | None | None | malformed_terminal_declaration | 0 | 0 | 0 |
| 128 | declared | None | None | malformed_terminal_declaration | 0 | 0 | 0 |
| 256 | legacy | 49 | last_integer | accepted_legacy_answer | 0 | 1 | 1 |
| 256 | terminal | None | None | malformed_terminal_declaration | 0 | 0 | 0 |
| 256 | declared | None | None | malformed_terminal_declaration | 0 | 0 | 0 |
| 512 | legacy | 49 | last_integer | accepted_legacy_answer | 0 | 1 | 1 |
| 512 | terminal | None | None | malformed_terminal_declaration | 0 | 0 | 0 |
| 512 | declared | None | None | malformed_terminal_declaration | 0 | 0 | 0 |

Readable completion at cap(s) 128, 256, 512:

````text
To calculate the exact value of \(687 \times 57 + 930\), we can break it down into simpler steps.

First, let's perform the multiplication:

\[687 \times 57 = 402,19\]

Now, add 930 to this result:

\[402,19 + 930 = 411,49\]

So, the exact value of \(687 \times 57 + 930\) is **411,49**.
````

## Base persistent proxy only eos at 512

Eligible problem IDs: 218.

Problem 2: `297 × 82 + 118`. Integer target: **24472**.

| Cap | Original new tokens | Actual stopping reason | Generate s |
|---|---|---|---|
| 128 | 119 | eos_before_limit | 2.886 |
| 256 | 119 | eos_before_limit | 2.917 |
| 512 | 119 | eos_before_limit | 2.782 |

| Cap | Policy | Value | Method | Status | Exact | Modulo | Proxy-only |
|---|---|---|---|---|---|---|---|
| 128 | legacy | 24152 | last_integer | accepted_legacy_answer | 0 | 1 | 1 |
| 128 | terminal | 24152 | natural_language_conclusion | accepted_terminal_answer | 0 | 1 | 1 |
| 128 | declared | None | None | missing_terminal_answer | 0 | 0 | 0 |
| 256 | legacy | 24152 | last_integer | accepted_legacy_answer | 0 | 1 | 1 |
| 256 | terminal | 24152 | natural_language_conclusion | accepted_terminal_answer | 0 | 1 | 1 |
| 256 | declared | None | None | missing_terminal_answer | 0 | 0 | 0 |
| 512 | legacy | 24152 | last_integer | accepted_legacy_answer | 0 | 1 | 1 |
| 512 | terminal | 24152 | natural_language_conclusion | accepted_terminal_answer | 0 | 1 | 1 |
| 512 | declared | None | None | missing_terminal_answer | 0 | 0 | 0 |

Readable completion at cap(s) 128, 256, 512:

````text
To calculate the exact value of \(297 \times 82 + 118\), we can break it down into simpler steps.

First, let's perform the multiplication:

\[297 \times 82 = 24034\]

Now, add 118 to this result:

\[24034 + 118 = 24152\]

So, the exact value of \(297 \times 82 + 118\) is **24152**.
````

## Base no exact improvement at any budget

Eligible problem IDs: 351.

Problem 1: `534 × 11 + 811`. Integer target: **6685**.

| Cap | Original new tokens | Actual stopping reason | Generate s |
|---|---|---|---|
| 128 | 128 | token_limit_without_eos | 3.057 |
| 256 | 136 | eos_before_limit | 3.268 |
| 512 | 136 | eos_before_limit | 3.271 |

| Cap | Policy | Value | Method | Status | Exact | Modulo | Proxy-only |
|---|---|---|---|---|---|---|---|
| 128 | legacy | 811 | last_integer | accepted_legacy_answer | 0 | 0 | 0 |
| 128 | terminal | None | None | missing_terminal_answer | 0 | 0 | 0 |
| 128 | declared | None | None | missing_terminal_answer | 0 | 0 | 0 |
| 256 | legacy | 6785 | last_integer | accepted_legacy_answer | 0 | 1 | 1 |
| 256 | terminal | 6785 | natural_language_conclusion | accepted_terminal_answer | 0 | 1 | 1 |
| 256 | declared | None | None | missing_terminal_answer | 0 | 0 | 0 |
| 512 | legacy | 6785 | last_integer | accepted_legacy_answer | 0 | 1 | 1 |
| 512 | terminal | 6785 | natural_language_conclusion | accepted_terminal_answer | 0 | 1 | 1 |
| 512 | declared | None | None | missing_terminal_answer | 0 | 0 | 0 |

Readable completion at cap(s) 128:

````text
To calculate the exact value of \(534 \times 11 + 811\), we will follow these steps:

1. **Multiply 534 by 11:**
   \[
   534 \times 11 = 5974
   \]

2. **Add 811 to the result from step 1:**
   \[
   5974 + 811 = 6785
   \]

Therefore, the exact value of \(534 \times 11 + 811\) is
````

Readable completion at cap(s) 256, 512:

````text
To calculate the exact value of \(534 \times 11 + 811\), we will follow these steps:

1. **Multiply 534 by 11:**
   \[
   534 \times 11 = 5974
   \]

2. **Add 811 to the result from step 1:**
   \[
   5974 + 811 = 6785
   \]

Therefore, the exact value of \(534 \times 11 + 811\) is \(6785\).
````

## Exact 201 cap without eos then terminal answer

Eligible problem IDs: 21.

Problem 6: `823 × 47 + 580`. Integer target: **39261**.

| Cap | Original new tokens | Actual stopping reason | Generate s |
|---|---|---|---|
| 128 | 128 | token_limit_without_eos | 4.145 |
| 256 | 223 | eos_before_limit | 8.100 |
| 512 | 223 | eos_before_limit | 7.228 |

| Cap | Policy | Value | Method | Status | Exact | Modulo | Proxy-only |
|---|---|---|---|---|---|---|---|
| 128 | legacy | 10 | last_integer | accepted_legacy_answer | 0 | 0 | 0 |
| 128 | terminal | None | None | missing_terminal_answer | 0 | 0 | 0 |
| 128 | declared | None | None | missing_terminal_answer | 0 | 0 | 0 |
| 256 | legacy | 39261 | last_integer | accepted_legacy_answer | 1 | 1 | 0 |
| 256 | terminal | 39261 | natural_language_conclusion | accepted_terminal_answer | 1 | 1 | 0 |
| 256 | declared | None | None | missing_terminal_answer | 0 | 0 | 0 |
| 512 | legacy | 39261 | last_integer | accepted_legacy_answer | 1 | 1 | 0 |
| 512 | terminal | 39261 | natural_language_conclusion | accepted_terminal_answer | 1 | 1 | 0 |
| 512 | declared | None | None | missing_terminal_answer | 0 | 0 | 0 |

Readable completion at cap(s) 128:

````text
Sure! Let's break it down step by step:

1) First, we need to calculate the multiplication: \(823 \times 47\)

   To do this, let's use the distributive property:
   
   \(823 \times 47 = (800 + 23) \times 47\)
   
   Now distribute the 47:
   
   \(= 800 \times 47 + 23 \times 47\)
   
   Calculate each part separately:
   
   \(= 37600 + 10
````

Readable completion at cap(s) 256, 512:

````text
Sure! Let's break it down step by step:

1) First, we need to calculate the multiplication: \(823 \times 47\)

   To do this, let's use the distributive property:
   
   \(823 \times 47 = (800 + 23) \times 47\)
   
   Now distribute the 47:
   
   \(= 800 \times 47 + 23 \times 47\)
   
   Calculate each part separately:
   
   \(= 37600 + 1081\)
   
   Add these two results together:
   
   \(= 38681\)

2) Next, we add 580 to our result from step 1:
   
   \(38681 + 580 = 39261\)

Therefore, the exact value of \(823 \times 47 + 580\) is **39261**.
````

## Exact 201 final already present but wrong at 128

Eligible problem IDs: 341.

Problem 1: `534 × 11 + 811`. Integer target: **6685**.

| Cap | Original new tokens | Actual stopping reason | Generate s |
|---|---|---|---|
| 128 | 84 | eos_before_limit | 2.474 |
| 256 | 84 | eos_before_limit | 2.674 |
| 512 | 84 | eos_before_limit | 2.694 |

| Cap | Policy | Value | Method | Status | Exact | Modulo | Proxy-only |
|---|---|---|---|---|---|---|---|
| 128 | legacy | 6835 | last_integer | accepted_legacy_answer | 0 | 1 | 1 |
| 128 | terminal | 6835 | natural_language_conclusion | accepted_terminal_answer | 0 | 1 | 1 |
| 128 | declared | None | None | missing_terminal_answer | 0 | 0 | 0 |
| 256 | legacy | 6835 | last_integer | accepted_legacy_answer | 0 | 1 | 1 |
| 256 | terminal | 6835 | natural_language_conclusion | accepted_terminal_answer | 0 | 1 | 1 |
| 256 | declared | None | None | missing_terminal_answer | 0 | 0 | 0 |
| 512 | legacy | 6835 | last_integer | accepted_legacy_answer | 0 | 1 | 1 |
| 512 | terminal | 6835 | natural_language_conclusion | accepted_terminal_answer | 0 | 1 | 1 |
| 512 | declared | None | None | missing_terminal_answer | 0 | 0 | 0 |

Readable completion at cap(s) 128, 256, 512:

````text
Sure! Let's break it down step by step:

First, we need to calculate the multiplication:
\[ 534 \times 11 = 6024 \]

Next, we add this result to 811:
\[ 6024 + 811 = 6835 \]

So, the exact value is \( 6835 \).
````

## Exact 201 legacy only credit no terminal answer

Eligible problem IDs: 16.

Problem 38: `687 × 57 + 930`. Integer target: **40089**.

| Cap | Original new tokens | Actual stopping reason | Generate s |
|---|---|---|---|
| 128 | 101 | eos_before_limit | 3.147 |
| 256 | 101 | eos_before_limit | 2.949 |
| 512 | 101 | eos_before_limit | 2.947 |

| Cap | Policy | Value | Method | Status | Exact | Modulo | Proxy-only |
|---|---|---|---|---|---|---|---|
| 128 | legacy | 29 | last_integer | accepted_legacy_answer | 0 | 1 | 1 |
| 128 | terminal | None | None | malformed_terminal_declaration | 0 | 0 | 0 |
| 128 | declared | None | None | malformed_terminal_declaration | 0 | 0 | 0 |
| 256 | legacy | 29 | last_integer | accepted_legacy_answer | 0 | 1 | 1 |
| 256 | terminal | None | None | malformed_terminal_declaration | 0 | 0 | 0 |
| 256 | declared | None | None | malformed_terminal_declaration | 0 | 0 | 0 |
| 512 | legacy | 29 | last_integer | accepted_legacy_answer | 0 | 1 | 1 |
| 512 | terminal | None | None | malformed_terminal_declaration | 0 | 0 | 0 |
| 512 | declared | None | None | malformed_terminal_declaration | 0 | 0 | 0 |

Readable completion at cap(s) 128, 256, 512:

````text
Sure! Let's break it down step by step:

1) First, calculate the multiplication: 
   687 * 57 = 402,99

2) Then add 930 to the result:
   402,99 + 930 = 412,29

Therefore, the exact value of 687 * 57 + 930 is 412,29.
````

## Exact 201 grouped or prefix disagreement

Eligible problem IDs: 10.

Problem 24: `483 × 32 + 922`. Integer target: **16378**.

| Cap | Original new tokens | Actual stopping reason | Generate s |
|---|---|---|---|
| 128 | 86 | eos_before_limit | 2.655 |
| 256 | 86 | eos_before_limit | 2.511 |
| 512 | 86 | eos_before_limit | 2.515 |

| Cap | Policy | Value | Method | Status | Exact | Modulo | Proxy-only |
|---|---|---|---|---|---|---|---|
| 128 | legacy | 398 | last_integer | accepted_legacy_answer | 0 | 1 | 1 |
| 128 | terminal | 16398 | natural_language_conclusion | accepted_terminal_answer | 0 | 1 | 1 |
| 128 | declared | None | None | missing_terminal_answer | 0 | 0 | 0 |
| 256 | legacy | 398 | last_integer | accepted_legacy_answer | 0 | 1 | 1 |
| 256 | terminal | 16398 | natural_language_conclusion | accepted_terminal_answer | 0 | 1 | 1 |
| 256 | declared | None | None | missing_terminal_answer | 0 | 0 | 0 |
| 512 | legacy | 398 | last_integer | accepted_legacy_answer | 0 | 1 | 1 |
| 512 | terminal | 16398 | natural_language_conclusion | accepted_terminal_answer | 0 | 1 | 1 |
| 512 | declared | None | None | missing_terminal_answer | 0 | 0 | 0 |

Readable completion at cap(s) 128, 256, 512:

````text
Sure! Let's break it down step by step:

1) First, calculate the multiplication:
   483 * 32 = 15,376

2) Then add the result to 922:
   15,376 + 922 = 16,398

Therefore, the exact value is 16,398.
````

## Exact 201 persistent proxy only eos at 512

Eligible problem IDs: 340.

Problem 1: `534 × 11 + 811`. Integer target: **6685**.

| Cap | Original new tokens | Actual stopping reason | Generate s |
|---|---|---|---|
| 128 | 84 | eos_before_limit | 2.474 |
| 256 | 84 | eos_before_limit | 2.674 |
| 512 | 84 | eos_before_limit | 2.694 |

| Cap | Policy | Value | Method | Status | Exact | Modulo | Proxy-only |
|---|---|---|---|---|---|---|---|
| 128 | legacy | 6835 | last_integer | accepted_legacy_answer | 0 | 1 | 1 |
| 128 | terminal | 6835 | natural_language_conclusion | accepted_terminal_answer | 0 | 1 | 1 |
| 128 | declared | None | None | missing_terminal_answer | 0 | 0 | 0 |
| 256 | legacy | 6835 | last_integer | accepted_legacy_answer | 0 | 1 | 1 |
| 256 | terminal | 6835 | natural_language_conclusion | accepted_terminal_answer | 0 | 1 | 1 |
| 256 | declared | None | None | missing_terminal_answer | 0 | 0 | 0 |
| 512 | legacy | 6835 | last_integer | accepted_legacy_answer | 0 | 1 | 1 |
| 512 | terminal | 6835 | natural_language_conclusion | accepted_terminal_answer | 0 | 1 | 1 |
| 512 | declared | None | None | missing_terminal_answer | 0 | 0 | 0 |

Readable completion at cap(s) 128, 256, 512:

````text
Sure! Let's break it down step by step:

First, we need to calculate the multiplication:
\[ 534 \times 11 = 6024 \]

Next, we add this result to 811:
\[ 6024 + 811 = 6835 \]

So, the exact value is \( 6835 \).
````

## Exact 201 no exact improvement at any budget

Eligible problem IDs: 366.

Problem 1: `534 × 11 + 811`. Integer target: **6685**.

| Cap | Original new tokens | Actual stopping reason | Generate s |
|---|---|---|---|
| 128 | 84 | eos_before_limit | 2.474 |
| 256 | 84 | eos_before_limit | 2.674 |
| 512 | 84 | eos_before_limit | 2.694 |

| Cap | Policy | Value | Method | Status | Exact | Modulo | Proxy-only |
|---|---|---|---|---|---|---|---|
| 128 | legacy | 6835 | last_integer | accepted_legacy_answer | 0 | 1 | 1 |
| 128 | terminal | 6835 | natural_language_conclusion | accepted_terminal_answer | 0 | 1 | 1 |
| 128 | declared | None | None | missing_terminal_answer | 0 | 0 | 0 |
| 256 | legacy | 6835 | last_integer | accepted_legacy_answer | 0 | 1 | 1 |
| 256 | terminal | 6835 | natural_language_conclusion | accepted_terminal_answer | 0 | 1 | 1 |
| 256 | declared | None | None | missing_terminal_answer | 0 | 0 | 0 |
| 512 | legacy | 6835 | last_integer | accepted_legacy_answer | 0 | 1 | 1 |
| 512 | terminal | 6835 | natural_language_conclusion | accepted_terminal_answer | 0 | 1 | 1 |
| 512 | declared | None | None | missing_terminal_answer | 0 | 0 | 0 |

Readable completion at cap(s) 128, 256, 512:

````text
Sure! Let's break it down step by step:

First, we need to calculate the multiplication:
\[ 534 \times 11 = 6024 \]

Next, we add this result to 811:
\[ 6024 + 811 = 6835 \]

So, the exact value is \( 6835 \).
````

## Modulo 201 cap without eos then terminal answer

Eligible problem IDs: 1.

Problem 175: `790 × 98 + 447`. Integer target: **77867**.

| Cap | Original new tokens | Actual stopping reason | Generate s |
|---|---|---|---|
| 128 | 128 | token_limit_without_eos | 3.832 |
| 256 | 129 | eos_before_limit | 4.001 |
| 512 | 129 | eos_before_limit | 3.804 |

| Cap | Policy | Value | Method | Status | Exact | Modulo | Proxy-only |
|---|---|---|---|---|---|---|---|
| 128 | legacy | 77067 | last_integer | accepted_legacy_answer | 0 | 1 | 1 |
| 128 | terminal | 77067 | natural_language_conclusion | accepted_terminal_answer | 0 | 1 | 1 |
| 128 | declared | None | None | missing_terminal_answer | 0 | 0 | 0 |
| 256 | legacy | 77067 | last_integer | accepted_legacy_answer | 0 | 1 | 1 |
| 256 | terminal | 77067 | natural_language_conclusion | accepted_terminal_answer | 0 | 1 | 1 |
| 256 | declared | None | None | missing_terminal_answer | 0 | 0 | 0 |
| 512 | legacy | 77067 | last_integer | accepted_legacy_answer | 0 | 1 | 1 |
| 512 | terminal | 77067 | natural_language_conclusion | accepted_terminal_answer | 0 | 1 | 1 |
| 512 | declared | None | None | missing_terminal_answer | 0 | 0 | 0 |

Readable completion at cap(s) 128, 256, 512:

````text
Let's break this down into steps:

1) First, we need to calculate 790 * 98

   This is an arithmetic problem that can be solved by multiplying 790 by 98.

   790 * 98 = 76620

2) Now, we add 447 to our result from step 1

   76620 + 447 = 77067

Therefore, the exact value of 790 * 98 + 447 is 77067.
````

## Modulo 201 final already present but wrong at 128

Eligible problem IDs: 371.

Problem 1: `534 × 11 + 811`. Integer target: **6685**.

| Cap | Original new tokens | Actual stopping reason | Generate s |
|---|---|---|---|
| 128 | 88 | eos_before_limit | 2.839 |
| 256 | 88 | eos_before_limit | 2.791 |
| 512 | 88 | eos_before_limit | 2.850 |

| Cap | Policy | Value | Method | Status | Exact | Modulo | Proxy-only |
|---|---|---|---|---|---|---|---|
| 128 | legacy | 6835 | last_integer | accepted_legacy_answer | 0 | 1 | 1 |
| 128 | terminal | 6835 | natural_language_conclusion | accepted_terminal_answer | 0 | 1 | 1 |
| 128 | declared | None | None | missing_terminal_answer | 0 | 0 | 0 |
| 256 | legacy | 6835 | last_integer | accepted_legacy_answer | 0 | 1 | 1 |
| 256 | terminal | 6835 | natural_language_conclusion | accepted_terminal_answer | 0 | 1 | 1 |
| 256 | declared | None | None | missing_terminal_answer | 0 | 0 | 0 |
| 512 | legacy | 6835 | last_integer | accepted_legacy_answer | 0 | 1 | 1 |
| 512 | terminal | 6835 | natural_language_conclusion | accepted_terminal_answer | 0 | 1 | 1 |
| 512 | declared | None | None | missing_terminal_answer | 0 | 0 | 0 |

Readable completion at cap(s) 128, 256, 512:

````text
Let's break this down:

First, we multiply 534 by 11:
534 * 11 = 6024

Then, we add 811 to our result:
6024 + 811 = 6835

Therefore, the exact value of 534 * 11 + 811 is 6835.
````

## Modulo 201 legacy only credit no terminal answer

Eligible problem IDs: 6.

Problem 38: `687 × 57 + 930`. Integer target: **40089**.

| Cap | Original new tokens | Actual stopping reason | Generate s |
|---|---|---|---|
| 128 | 111 | eos_before_limit | 3.254 |
| 256 | 111 | eos_before_limit | 3.389 |
| 512 | 111 | eos_before_limit | 3.283 |

| Cap | Policy | Value | Method | Status | Exact | Modulo | Proxy-only |
|---|---|---|---|---|---|---|---|
| 128 | legacy | 29 | last_integer | accepted_legacy_answer | 0 | 1 | 1 |
| 128 | terminal | None | None | malformed_terminal_declaration | 0 | 0 | 0 |
| 128 | declared | None | None | malformed_terminal_declaration | 0 | 0 | 0 |
| 256 | legacy | 29 | last_integer | accepted_legacy_answer | 0 | 1 | 1 |
| 256 | terminal | None | None | malformed_terminal_declaration | 0 | 0 | 0 |
| 256 | declared | None | None | malformed_terminal_declaration | 0 | 0 | 0 |
| 512 | legacy | 29 | last_integer | accepted_legacy_answer | 0 | 1 | 1 |
| 512 | terminal | None | None | malformed_terminal_declaration | 0 | 0 | 0 |
| 512 | declared | None | None | malformed_terminal_declaration | 0 | 0 | 0 |

Readable completion at cap(s) 128, 256, 512:

````text
Let's break this down into steps:

1) First, we need to calculate 687 * 57:
   687 * 57 = 402,99

2) Now, add 930 to our result from step 1:
   402,99 + 930 = 412,29

Therefore, the exact value of 687 * 57 + 930 is 412,29.
````

## Modulo 201 grouped or prefix disagreement

Eligible problem IDs: 34.

Problem 15: `147 × 84 + 506`. Integer target: **12854**.

| Cap | Original new tokens | Actual stopping reason | Generate s |
|---|---|---|---|
| 128 | 91 | eos_before_limit | 2.904 |
| 256 | 91 | eos_before_limit | 2.899 |
| 512 | 91 | eos_before_limit | 2.955 |

| Cap | Policy | Value | Method | Status | Exact | Modulo | Proxy-only |
|---|---|---|---|---|---|---|---|
| 128 | legacy | 814 | last_integer | accepted_legacy_answer | 0 | 1 | 1 |
| 128 | terminal | 12814 | natural_language_conclusion | accepted_terminal_answer | 0 | 1 | 1 |
| 128 | declared | None | None | missing_terminal_answer | 0 | 0 | 0 |
| 256 | legacy | 814 | last_integer | accepted_legacy_answer | 0 | 1 | 1 |
| 256 | terminal | 12814 | natural_language_conclusion | accepted_terminal_answer | 0 | 1 | 1 |
| 256 | declared | None | None | missing_terminal_answer | 0 | 0 | 0 |
| 512 | legacy | 814 | last_integer | accepted_legacy_answer | 0 | 1 | 1 |
| 512 | terminal | 12814 | natural_language_conclusion | accepted_terminal_answer | 0 | 1 | 1 |
| 512 | declared | None | None | missing_terminal_answer | 0 | 0 | 0 |

Readable completion at cap(s) 128, 256, 512:

````text
Let's break this down:

First, we calculate the multiplication: 

147 * 84 = 12,308

Then, we add 506 to our result:

12,308 + 506 = 12,814

Therefore, the exact value of 147 * 84 + 506 is 12,814.
````

## Modulo 201 persistent proxy only eos at 512

Eligible problem IDs: 364.

Problem 1: `534 × 11 + 811`. Integer target: **6685**.

| Cap | Original new tokens | Actual stopping reason | Generate s |
|---|---|---|---|
| 128 | 88 | eos_before_limit | 2.839 |
| 256 | 88 | eos_before_limit | 2.791 |
| 512 | 88 | eos_before_limit | 2.850 |

| Cap | Policy | Value | Method | Status | Exact | Modulo | Proxy-only |
|---|---|---|---|---|---|---|---|
| 128 | legacy | 6835 | last_integer | accepted_legacy_answer | 0 | 1 | 1 |
| 128 | terminal | 6835 | natural_language_conclusion | accepted_terminal_answer | 0 | 1 | 1 |
| 128 | declared | None | None | missing_terminal_answer | 0 | 0 | 0 |
| 256 | legacy | 6835 | last_integer | accepted_legacy_answer | 0 | 1 | 1 |
| 256 | terminal | 6835 | natural_language_conclusion | accepted_terminal_answer | 0 | 1 | 1 |
| 256 | declared | None | None | missing_terminal_answer | 0 | 0 | 0 |
| 512 | legacy | 6835 | last_integer | accepted_legacy_answer | 0 | 1 | 1 |
| 512 | terminal | 6835 | natural_language_conclusion | accepted_terminal_answer | 0 | 1 | 1 |
| 512 | declared | None | None | missing_terminal_answer | 0 | 0 | 0 |

Readable completion at cap(s) 128, 256, 512:

````text
Let's break this down:

First, we multiply 534 by 11:
534 * 11 = 6024

Then, we add 811 to our result:
6024 + 811 = 6835

Therefore, the exact value of 534 * 11 + 811 is 6835.
````

## Modulo 201 no exact improvement at any budget

Eligible problem IDs: 377.

Problem 1: `534 × 11 + 811`. Integer target: **6685**.

| Cap | Original new tokens | Actual stopping reason | Generate s |
|---|---|---|---|
| 128 | 88 | eos_before_limit | 2.839 |
| 256 | 88 | eos_before_limit | 2.791 |
| 512 | 88 | eos_before_limit | 2.850 |

| Cap | Policy | Value | Method | Status | Exact | Modulo | Proxy-only |
|---|---|---|---|---|---|---|---|
| 128 | legacy | 6835 | last_integer | accepted_legacy_answer | 0 | 1 | 1 |
| 128 | terminal | 6835 | natural_language_conclusion | accepted_terminal_answer | 0 | 1 | 1 |
| 128 | declared | None | None | missing_terminal_answer | 0 | 0 | 0 |
| 256 | legacy | 6835 | last_integer | accepted_legacy_answer | 0 | 1 | 1 |
| 256 | terminal | 6835 | natural_language_conclusion | accepted_terminal_answer | 0 | 1 | 1 |
| 256 | declared | None | None | missing_terminal_answer | 0 | 0 | 0 |
| 512 | legacy | 6835 | last_integer | accepted_legacy_answer | 0 | 1 | 1 |
| 512 | terminal | 6835 | natural_language_conclusion | accepted_terminal_answer | 0 | 1 | 1 |
| 512 | declared | None | None | missing_terminal_answer | 0 | 0 | 0 |

Readable completion at cap(s) 128, 256, 512:

````text
Let's break this down:

First, we multiply 534 by 11:
534 * 11 = 6024

Then, we add 811 to our result:
6024 + 811 = 6835

Therefore, the exact value of 534 * 11 + 811 is 6835.
````

## Exact 202 cap without eos then terminal answer

Eligible problem IDs: 193.

Problem 1: `534 × 11 + 811`. Integer target: **6685**.

| Cap | Original new tokens | Actual stopping reason | Generate s |
|---|---|---|---|
| 128 | 128 | token_limit_without_eos | 4.206 |
| 256 | 139 | eos_before_limit | 4.452 |
| 512 | 139 | eos_before_limit | 4.494 |

| Cap | Policy | Value | Method | Status | Exact | Modulo | Proxy-only |
|---|---|---|---|---|---|---|---|
| 128 | legacy | 6785 | last_integer | accepted_legacy_answer | 0 | 1 | 1 |
| 128 | terminal | None | None | malformed_terminal_declaration | 0 | 0 | 0 |
| 128 | declared | None | None | malformed_terminal_declaration | 0 | 0 | 0 |
| 256 | legacy | 6785 | last_integer | accepted_legacy_answer | 0 | 1 | 1 |
| 256 | terminal | 6785 | natural_language_conclusion | accepted_terminal_answer | 0 | 1 | 1 |
| 256 | declared | None | None | missing_terminal_answer | 0 | 0 | 0 |
| 512 | legacy | 6785 | last_integer | accepted_legacy_answer | 0 | 1 | 1 |
| 512 | terminal | 6785 | natural_language_conclusion | accepted_terminal_answer | 0 | 1 | 1 |
| 512 | declared | None | None | missing_terminal_answer | 0 | 0 | 0 |

Readable completion at cap(s) 128:

````text
Sure! Let's break this down step by step:

First, we need to calculate \(534 \times 11\):

\[534 \times 11 = 5974\]

Now, we add 811 to that result:

\[5974 + 811 = 6785\]

So, the exact value is 6785.

To verify:
- We calculated \(534 \times 11\) as 5974.
- Then we added 811 to get 6785.

Therefore,
````

Readable completion at cap(s) 256, 512:

````text
Sure! Let's break this down step by step:

First, we need to calculate \(534 \times 11\):

\[534 \times 11 = 5974\]

Now, we add 811 to that result:

\[5974 + 811 = 6785\]

So, the exact value is 6785.

To verify:
- We calculated \(534 \times 11\) as 5974.
- Then we added 811 to get 6785.

Therefore, the final answer is 6785.
````

## Exact 202 final already present but wrong at 128

Eligible problem IDs: 205.

Problem 2: `297 × 82 + 118`. Integer target: **24472**.

| Cap | Original new tokens | Actual stopping reason | Generate s |
|---|---|---|---|
| 128 | 119 | eos_before_limit | 3.898 |
| 256 | 119 | eos_before_limit | 3.784 |
| 512 | 119 | eos_before_limit | 3.834 |

| Cap | Policy | Value | Method | Status | Exact | Modulo | Proxy-only |
|---|---|---|---|---|---|---|---|
| 128 | legacy | 24652 | last_integer | accepted_legacy_answer | 0 | 1 | 1 |
| 128 | terminal | 24652 | natural_language_conclusion | accepted_terminal_answer | 0 | 1 | 1 |
| 128 | declared | None | None | missing_terminal_answer | 0 | 0 | 0 |
| 256 | legacy | 24652 | last_integer | accepted_legacy_answer | 0 | 1 | 1 |
| 256 | terminal | 24652 | natural_language_conclusion | accepted_terminal_answer | 0 | 1 | 1 |
| 256 | declared | None | None | missing_terminal_answer | 0 | 0 | 0 |
| 512 | legacy | 24652 | last_integer | accepted_legacy_answer | 0 | 1 | 1 |
| 512 | terminal | 24652 | natural_language_conclusion | accepted_terminal_answer | 0 | 1 | 1 |
| 512 | declared | None | None | missing_terminal_answer | 0 | 0 | 0 |

Readable completion at cap(s) 128, 256, 512:

````text
To calculate the exact value of \(297 \times 82 + 118\), we can break it down into simpler steps:

First, let's perform the multiplication:
\[297 \times 82 = 24534.\]

Next, add 118 to this result:
\[24534 + 118 = 24652.\]

Therefore, the exact value of \(297 \times 82 + 118\) is **24652**.
````

## Exact 202 legacy only credit no terminal answer

Eligible problem IDs: 70.

Problem 1: `534 × 11 + 811`. Integer target: **6685**.

| Cap | Original new tokens | Actual stopping reason | Generate s |
|---|---|---|---|
| 128 | 128 | token_limit_without_eos | 4.206 |
| 256 | 139 | eos_before_limit | 4.452 |
| 512 | 139 | eos_before_limit | 4.494 |

| Cap | Policy | Value | Method | Status | Exact | Modulo | Proxy-only |
|---|---|---|---|---|---|---|---|
| 128 | legacy | 6785 | last_integer | accepted_legacy_answer | 0 | 1 | 1 |
| 128 | terminal | None | None | malformed_terminal_declaration | 0 | 0 | 0 |
| 128 | declared | None | None | malformed_terminal_declaration | 0 | 0 | 0 |
| 256 | legacy | 6785 | last_integer | accepted_legacy_answer | 0 | 1 | 1 |
| 256 | terminal | 6785 | natural_language_conclusion | accepted_terminal_answer | 0 | 1 | 1 |
| 256 | declared | None | None | missing_terminal_answer | 0 | 0 | 0 |
| 512 | legacy | 6785 | last_integer | accepted_legacy_answer | 0 | 1 | 1 |
| 512 | terminal | 6785 | natural_language_conclusion | accepted_terminal_answer | 0 | 1 | 1 |
| 512 | declared | None | None | missing_terminal_answer | 0 | 0 | 0 |

Readable completion at cap(s) 128:

````text
Sure! Let's break this down step by step:

First, we need to calculate \(534 \times 11\):

\[534 \times 11 = 5974\]

Now, we add 811 to that result:

\[5974 + 811 = 6785\]

So, the exact value is 6785.

To verify:
- We calculated \(534 \times 11\) as 5974.
- Then we added 811 to get 6785.

Therefore,
````

Readable completion at cap(s) 256, 512:

````text
Sure! Let's break this down step by step:

First, we need to calculate \(534 \times 11\):

\[534 \times 11 = 5974\]

Now, we add 811 to that result:

\[5974 + 811 = 6785\]

So, the exact value is 6785.

To verify:
- We calculated \(534 \times 11\) as 5974.
- Then we added 811 to get 6785.

Therefore, the final answer is 6785.
````

## Exact 202 grouped or prefix disagreement

Eligible problem IDs: 2.

Problem 77: `900 × 56 + 117`. Integer target: **50517**.

| Cap | Original new tokens | Actual stopping reason | Generate s |
|---|---|---|---|
| 128 | 100 | eos_before_limit | 2.863 |
| 256 | 100 | eos_before_limit | 3.025 |
| 512 | 100 | eos_before_limit | 2.935 |

| Cap | Policy | Value | Method | Status | Exact | Modulo | Proxy-only |
|---|---|---|---|---|---|---|---|
| 128 | legacy | 517 | last_integer | accepted_legacy_answer | 0 | 1 | 1 |
| 128 | terminal | 48517 | natural_language_conclusion | accepted_terminal_answer | 0 | 1 | 1 |
| 128 | declared | None | None | missing_terminal_answer | 0 | 0 | 0 |
| 256 | legacy | 517 | last_integer | accepted_legacy_answer | 0 | 1 | 1 |
| 256 | terminal | 48517 | natural_language_conclusion | accepted_terminal_answer | 0 | 1 | 1 |
| 256 | declared | None | None | missing_terminal_answer | 0 | 0 | 0 |
| 512 | legacy | 517 | last_integer | accepted_legacy_answer | 0 | 1 | 1 |
| 512 | terminal | 48517 | natural_language_conclusion | accepted_terminal_answer | 0 | 1 | 1 |
| 512 | declared | None | None | missing_terminal_answer | 0 | 0 | 0 |

Readable completion at cap(s) 128, 256, 512:

````text
Sure! Let's break this down step by step:

First, we need to calculate \( 900 \times 56 \):

\[ 900 \times 56 = 48,400 \]

Now, we add 117 to that result:

\[ 48,400 + 117 = 48,517 \]

So, the exact value is **48,517**.
````

## Exact 202 persistent proxy only eos at 512

Eligible problem IDs: 202.

Problem 2: `297 × 82 + 118`. Integer target: **24472**.

| Cap | Original new tokens | Actual stopping reason | Generate s |
|---|---|---|---|
| 128 | 119 | eos_before_limit | 3.898 |
| 256 | 119 | eos_before_limit | 3.784 |
| 512 | 119 | eos_before_limit | 3.834 |

| Cap | Policy | Value | Method | Status | Exact | Modulo | Proxy-only |
|---|---|---|---|---|---|---|---|
| 128 | legacy | 24652 | last_integer | accepted_legacy_answer | 0 | 1 | 1 |
| 128 | terminal | 24652 | natural_language_conclusion | accepted_terminal_answer | 0 | 1 | 1 |
| 128 | declared | None | None | missing_terminal_answer | 0 | 0 | 0 |
| 256 | legacy | 24652 | last_integer | accepted_legacy_answer | 0 | 1 | 1 |
| 256 | terminal | 24652 | natural_language_conclusion | accepted_terminal_answer | 0 | 1 | 1 |
| 256 | declared | None | None | missing_terminal_answer | 0 | 0 | 0 |
| 512 | legacy | 24652 | last_integer | accepted_legacy_answer | 0 | 1 | 1 |
| 512 | terminal | 24652 | natural_language_conclusion | accepted_terminal_answer | 0 | 1 | 1 |
| 512 | declared | None | None | missing_terminal_answer | 0 | 0 | 0 |

Readable completion at cap(s) 128, 256, 512:

````text
To calculate the exact value of \(297 \times 82 + 118\), we can break it down into simpler steps:

First, let's perform the multiplication:
\[297 \times 82 = 24534.\]

Next, add 118 to this result:
\[24534 + 118 = 24652.\]

Therefore, the exact value of \(297 \times 82 + 118\) is **24652**.
````

## Exact 202 no exact improvement at any budget

Eligible problem IDs: 376.

Problem 1: `534 × 11 + 811`. Integer target: **6685**.

| Cap | Original new tokens | Actual stopping reason | Generate s |
|---|---|---|---|
| 128 | 128 | token_limit_without_eos | 4.206 |
| 256 | 139 | eos_before_limit | 4.452 |
| 512 | 139 | eos_before_limit | 4.494 |

| Cap | Policy | Value | Method | Status | Exact | Modulo | Proxy-only |
|---|---|---|---|---|---|---|---|
| 128 | legacy | 6785 | last_integer | accepted_legacy_answer | 0 | 1 | 1 |
| 128 | terminal | None | None | malformed_terminal_declaration | 0 | 0 | 0 |
| 128 | declared | None | None | malformed_terminal_declaration | 0 | 0 | 0 |
| 256 | legacy | 6785 | last_integer | accepted_legacy_answer | 0 | 1 | 1 |
| 256 | terminal | 6785 | natural_language_conclusion | accepted_terminal_answer | 0 | 1 | 1 |
| 256 | declared | None | None | missing_terminal_answer | 0 | 0 | 0 |
| 512 | legacy | 6785 | last_integer | accepted_legacy_answer | 0 | 1 | 1 |
| 512 | terminal | 6785 | natural_language_conclusion | accepted_terminal_answer | 0 | 1 | 1 |
| 512 | declared | None | None | missing_terminal_answer | 0 | 0 | 0 |

Readable completion at cap(s) 128:

````text
Sure! Let's break this down step by step:

First, we need to calculate \(534 \times 11\):

\[534 \times 11 = 5974\]

Now, we add 811 to that result:

\[5974 + 811 = 6785\]

So, the exact value is 6785.

To verify:
- We calculated \(534 \times 11\) as 5974.
- Then we added 811 to get 6785.

Therefore,
````

Readable completion at cap(s) 256, 512:

````text
Sure! Let's break this down step by step:

First, we need to calculate \(534 \times 11\):

\[534 \times 11 = 5974\]

Now, we add 811 to that result:

\[5974 + 811 = 6785\]

So, the exact value is 6785.

To verify:
- We calculated \(534 \times 11\) as 5974.
- Then we added 811 to get 6785.

Therefore, the final answer is 6785.
````

## Modulo 202 cap without eos then terminal answer

Eligible problem IDs: 0.

No qualifying example.

## Modulo 202 final already present but wrong at 128

Eligible problem IDs: 361.

Problem 1: `534 × 11 + 811`. Integer target: **6685**.

| Cap | Original new tokens | Actual stopping reason | Generate s |
|---|---|---|---|
| 128 | 93 | eos_before_limit | 2.943 |
| 256 | 93 | eos_before_limit | 2.957 |
| 512 | 93 | eos_before_limit | 3.111 |

| Cap | Policy | Value | Method | Status | Exact | Modulo | Proxy-only |
|---|---|---|---|---|---|---|---|
| 128 | legacy | 6835 | last_integer | accepted_legacy_answer | 0 | 1 | 1 |
| 128 | terminal | 6835 | natural_language_conclusion | accepted_terminal_answer | 0 | 1 | 1 |
| 128 | declared | None | None | missing_terminal_answer | 0 | 0 | 0 |
| 256 | legacy | 6835 | last_integer | accepted_legacy_answer | 0 | 1 | 1 |
| 256 | terminal | 6835 | natural_language_conclusion | accepted_terminal_answer | 0 | 1 | 1 |
| 256 | declared | None | None | missing_terminal_answer | 0 | 0 | 0 |
| 512 | legacy | 6835 | last_integer | accepted_legacy_answer | 0 | 1 | 1 |
| 512 | terminal | 6835 | natural_language_conclusion | accepted_terminal_answer | 0 | 1 | 1 |
| 512 | declared | None | None | missing_terminal_answer | 0 | 0 | 0 |

Readable completion at cap(s) 128, 256, 512:

````text
Sure! Let's break it down step by step:

First, we multiply 534 by 11:
534 * 11 = 6024

Next, we add 811 to the result:
6024 + 811 = 6835

Therefore, the exact value of 534 * 11 + 811 is 6835.
````

## Modulo 202 legacy only credit no terminal answer

Eligible problem IDs: 10.

Problem 38: `687 × 57 + 930`. Integer target: **40089**.

| Cap | Original new tokens | Actual stopping reason | Generate s |
|---|---|---|---|
| 128 | 106 | eos_before_limit | 3.231 |
| 256 | 106 | eos_before_limit | 3.169 |
| 512 | 106 | eos_before_limit | 3.182 |

| Cap | Policy | Value | Method | Status | Exact | Modulo | Proxy-only |
|---|---|---|---|---|---|---|---|
| 128 | legacy | 29 | last_integer | accepted_legacy_answer | 0 | 1 | 1 |
| 128 | terminal | None | None | malformed_terminal_declaration | 0 | 0 | 0 |
| 128 | declared | None | None | malformed_terminal_declaration | 0 | 0 | 0 |
| 256 | legacy | 29 | last_integer | accepted_legacy_answer | 0 | 1 | 1 |
| 256 | terminal | None | None | malformed_terminal_declaration | 0 | 0 | 0 |
| 256 | declared | None | None | malformed_terminal_declaration | 0 | 0 | 0 |
| 512 | legacy | 29 | last_integer | accepted_legacy_answer | 0 | 1 | 1 |
| 512 | terminal | None | None | malformed_terminal_declaration | 0 | 0 | 0 |
| 512 | declared | None | None | malformed_terminal_declaration | 0 | 0 | 0 |

Readable completion at cap(s) 128, 256, 512:

````text
Sure! Let's break it down step by step:

1) First, we need to calculate the multiplication: 
   687 * 57 = 402,99

2) Then, we add that result to 930:
   402,99 + 930 = 412,29

Therefore, the exact value of 687 * 57 + 930 is 412,29.
````

## Modulo 202 grouped or prefix disagreement

Eligible problem IDs: 48.

Problem 0: `206 × 90 + 334`. Integer target: **18874**.

| Cap | Original new tokens | Actual stopping reason | Generate s |
|---|---|---|---|
| 128 | 115 | eos_before_limit | 4.166 |
| 256 | 115 | eos_before_limit | 3.644 |
| 512 | 115 | eos_before_limit | 4.029 |

| Cap | Policy | Value | Method | Status | Exact | Modulo | Proxy-only |
|---|---|---|---|---|---|---|---|
| 128 | legacy | 874 | last_integer | accepted_legacy_answer | 0 | 1 | 1 |
| 128 | terminal | 18874 | natural_language_conclusion | accepted_terminal_answer | 1 | 1 | 0 |
| 128 | declared | None | None | missing_terminal_answer | 0 | 0 | 0 |
| 256 | legacy | 874 | last_integer | accepted_legacy_answer | 0 | 1 | 1 |
| 256 | terminal | 18874 | natural_language_conclusion | accepted_terminal_answer | 1 | 1 | 0 |
| 256 | declared | None | None | missing_terminal_answer | 0 | 0 | 0 |
| 512 | legacy | 874 | last_integer | accepted_legacy_answer | 0 | 1 | 1 |
| 512 | terminal | 18874 | natural_language_conclusion | accepted_terminal_answer | 1 | 1 | 0 |
| 512 | declared | None | None | missing_terminal_answer | 0 | 0 | 0 |

Readable completion at cap(s) 128, 256, 512:

````text
Sure! Let's break it down step by step:

1) First, we need to multiply 206 by 90:
   206 * 90 = 18,540

2) Then, we add 334 to our result from step 1:
   18,540 + 334 = 18,874

Therefore, the exact value of 206 * 90 + 334 is 18,874.
````

## Modulo 202 persistent proxy only eos at 512

Eligible problem IDs: 358.

Problem 1: `534 × 11 + 811`. Integer target: **6685**.

| Cap | Original new tokens | Actual stopping reason | Generate s |
|---|---|---|---|
| 128 | 93 | eos_before_limit | 2.943 |
| 256 | 93 | eos_before_limit | 2.957 |
| 512 | 93 | eos_before_limit | 3.111 |

| Cap | Policy | Value | Method | Status | Exact | Modulo | Proxy-only |
|---|---|---|---|---|---|---|---|
| 128 | legacy | 6835 | last_integer | accepted_legacy_answer | 0 | 1 | 1 |
| 128 | terminal | 6835 | natural_language_conclusion | accepted_terminal_answer | 0 | 1 | 1 |
| 128 | declared | None | None | missing_terminal_answer | 0 | 0 | 0 |
| 256 | legacy | 6835 | last_integer | accepted_legacy_answer | 0 | 1 | 1 |
| 256 | terminal | 6835 | natural_language_conclusion | accepted_terminal_answer | 0 | 1 | 1 |
| 256 | declared | None | None | missing_terminal_answer | 0 | 0 | 0 |
| 512 | legacy | 6835 | last_integer | accepted_legacy_answer | 0 | 1 | 1 |
| 512 | terminal | 6835 | natural_language_conclusion | accepted_terminal_answer | 0 | 1 | 1 |
| 512 | declared | None | None | missing_terminal_answer | 0 | 0 | 0 |

Readable completion at cap(s) 128, 256, 512:

````text
Sure! Let's break it down step by step:

First, we multiply 534 by 11:
534 * 11 = 6024

Next, we add 811 to the result:
6024 + 811 = 6835

Therefore, the exact value of 534 * 11 + 811 is 6835.
````

## Modulo 202 no exact improvement at any budget

Eligible problem IDs: 371.

Problem 1: `534 × 11 + 811`. Integer target: **6685**.

| Cap | Original new tokens | Actual stopping reason | Generate s |
|---|---|---|---|
| 128 | 93 | eos_before_limit | 2.943 |
| 256 | 93 | eos_before_limit | 2.957 |
| 512 | 93 | eos_before_limit | 3.111 |

| Cap | Policy | Value | Method | Status | Exact | Modulo | Proxy-only |
|---|---|---|---|---|---|---|---|
| 128 | legacy | 6835 | last_integer | accepted_legacy_answer | 0 | 1 | 1 |
| 128 | terminal | 6835 | natural_language_conclusion | accepted_terminal_answer | 0 | 1 | 1 |
| 128 | declared | None | None | missing_terminal_answer | 0 | 0 | 0 |
| 256 | legacy | 6835 | last_integer | accepted_legacy_answer | 0 | 1 | 1 |
| 256 | terminal | 6835 | natural_language_conclusion | accepted_terminal_answer | 0 | 1 | 1 |
| 256 | declared | None | None | missing_terminal_answer | 0 | 0 | 0 |
| 512 | legacy | 6835 | last_integer | accepted_legacy_answer | 0 | 1 | 1 |
| 512 | terminal | 6835 | natural_language_conclusion | accepted_terminal_answer | 0 | 1 | 1 |
| 512 | declared | None | None | missing_terminal_answer | 0 | 0 | 0 |

Readable completion at cap(s) 128, 256, 512:

````text
Sure! Let's break it down step by step:

First, we multiply 534 by 11:
534 * 11 = 6024

Next, we add 811 to the result:
6024 + 811 = 6835

Therefore, the exact value of 534 * 11 + 811 is 6835.
````

## Exact 203 cap without eos then terminal answer

Eligible problem IDs: 9.

Problem 6: `823 × 47 + 580`. Integer target: **39261**.

| Cap | Original new tokens | Actual stopping reason | Generate s |
|---|---|---|---|
| 128 | 128 | token_limit_without_eos | 4.440 |
| 256 | 196 | eos_before_limit | 6.812 |
| 512 | 196 | eos_before_limit | 6.205 |

| Cap | Policy | Value | Method | Status | Exact | Modulo | Proxy-only |
|---|---|---|---|---|---|---|---|
| 128 | legacy | 1081 | last_integer | accepted_legacy_answer | 0 | 1 | 1 |
| 128 | terminal | None | None | missing_terminal_answer | 0 | 0 | 0 |
| 128 | declared | None | None | missing_terminal_answer | 0 | 0 | 0 |
| 256 | legacy | 39261 | last_integer | accepted_legacy_answer | 1 | 1 | 0 |
| 256 | terminal | 39261 | natural_language_conclusion | accepted_terminal_answer | 1 | 1 | 0 |
| 256 | declared | None | None | missing_terminal_answer | 0 | 0 | 0 |
| 512 | legacy | 39261 | last_integer | accepted_legacy_answer | 1 | 1 | 0 |
| 512 | terminal | 39261 | natural_language_conclusion | accepted_terminal_answer | 1 | 1 | 0 |
| 512 | declared | None | None | missing_terminal_answer | 0 | 0 | 0 |

Readable completion at cap(s) 128:

````text
Sure! Let's break it down step by step:

1) First, calculate the multiplication: \(823 \times 47\)

   To do this, we can use the distributive property:
   
   \(823 \times 47 = (800 + 23)(47)\)
   
   Now apply the distributive property:
   
   \(= 800 \times 47 + 23 \times 47\)
   
   Calculate each term separately:
   
   \(= 37600 + 1081\)
   
  
````

Readable completion at cap(s) 256, 512:

````text
Sure! Let's break it down step by step:

1) First, calculate the multiplication: \(823 \times 47\)

   To do this, we can use the distributive property:
   
   \(823 \times 47 = (800 + 23)(47)\)
   
   Now apply the distributive property:
   
   \(= 800 \times 47 + 23 \times 47\)
   
   Calculate each term separately:
   
   \(= 37600 + 1081\)
   
   Add these two results together:
   
   \(= 38681\)

2) Next, add the result to 580:
   
   \(38681 + 580 = 39261\)

Therefore, the exact value is **39261**.
````

## Exact 203 final already present but wrong at 128

Eligible problem IDs: 356.

Problem 1: `534 × 11 + 811`. Integer target: **6685**.

| Cap | Original new tokens | Actual stopping reason | Generate s |
|---|---|---|---|
| 128 | 90 | eos_before_limit | 3.069 |
| 256 | 90 | eos_before_limit | 2.989 |
| 512 | 90 | eos_before_limit | 2.893 |

| Cap | Policy | Value | Method | Status | Exact | Modulo | Proxy-only |
|---|---|---|---|---|---|---|---|
| 128 | legacy | 6835 | last_integer | accepted_legacy_answer | 0 | 1 | 1 |
| 128 | terminal | 6835 | natural_language_conclusion | accepted_terminal_answer | 0 | 1 | 1 |
| 128 | declared | None | None | missing_terminal_answer | 0 | 0 | 0 |
| 256 | legacy | 6835 | last_integer | accepted_legacy_answer | 0 | 1 | 1 |
| 256 | terminal | 6835 | natural_language_conclusion | accepted_terminal_answer | 0 | 1 | 1 |
| 256 | declared | None | None | missing_terminal_answer | 0 | 0 | 0 |
| 512 | legacy | 6835 | last_integer | accepted_legacy_answer | 0 | 1 | 1 |
| 512 | terminal | 6835 | natural_language_conclusion | accepted_terminal_answer | 0 | 1 | 1 |
| 512 | declared | None | None | missing_terminal_answer | 0 | 0 | 0 |

Readable completion at cap(s) 128, 256, 512:

````text
Sure! Let's break it down step by step:

Step 1: Calculate the multiplication first.
534 * 11 = 6024

Step 2: Add the result to 811.
6024 + 811 = 6835

Therefore, the exact value of 534 * 11 + 811 is 6835.
````

## Exact 203 legacy only credit no terminal answer

Eligible problem IDs: 5.

Problem 6: `823 × 47 + 580`. Integer target: **39261**.

| Cap | Original new tokens | Actual stopping reason | Generate s |
|---|---|---|---|
| 128 | 128 | token_limit_without_eos | 4.440 |
| 256 | 196 | eos_before_limit | 6.812 |
| 512 | 196 | eos_before_limit | 6.205 |

| Cap | Policy | Value | Method | Status | Exact | Modulo | Proxy-only |
|---|---|---|---|---|---|---|---|
| 128 | legacy | 1081 | last_integer | accepted_legacy_answer | 0 | 1 | 1 |
| 128 | terminal | None | None | missing_terminal_answer | 0 | 0 | 0 |
| 128 | declared | None | None | missing_terminal_answer | 0 | 0 | 0 |
| 256 | legacy | 39261 | last_integer | accepted_legacy_answer | 1 | 1 | 0 |
| 256 | terminal | 39261 | natural_language_conclusion | accepted_terminal_answer | 1 | 1 | 0 |
| 256 | declared | None | None | missing_terminal_answer | 0 | 0 | 0 |
| 512 | legacy | 39261 | last_integer | accepted_legacy_answer | 1 | 1 | 0 |
| 512 | terminal | 39261 | natural_language_conclusion | accepted_terminal_answer | 1 | 1 | 0 |
| 512 | declared | None | None | missing_terminal_answer | 0 | 0 | 0 |

Readable completion at cap(s) 128:

````text
Sure! Let's break it down step by step:

1) First, calculate the multiplication: \(823 \times 47\)

   To do this, we can use the distributive property:
   
   \(823 \times 47 = (800 + 23)(47)\)
   
   Now apply the distributive property:
   
   \(= 800 \times 47 + 23 \times 47\)
   
   Calculate each term separately:
   
   \(= 37600 + 1081\)
   
  
````

Readable completion at cap(s) 256, 512:

````text
Sure! Let's break it down step by step:

1) First, calculate the multiplication: \(823 \times 47\)

   To do this, we can use the distributive property:
   
   \(823 \times 47 = (800 + 23)(47)\)
   
   Now apply the distributive property:
   
   \(= 800 \times 47 + 23 \times 47\)
   
   Calculate each term separately:
   
   \(= 37600 + 1081\)
   
   Add these two results together:
   
   \(= 38681\)

2) Next, add the result to 580:
   
   \(38681 + 580 = 39261\)

Therefore, the exact value is **39261**.
````

## Exact 203 grouped or prefix disagreement

Eligible problem IDs: 20.

Problem 15: `147 × 84 + 506`. Integer target: **12854**.

| Cap | Original new tokens | Actual stopping reason | Generate s |
|---|---|---|---|
| 128 | 84 | eos_before_limit | 2.811 |
| 256 | 84 | eos_before_limit | 2.806 |
| 512 | 84 | eos_before_limit | 2.669 |

| Cap | Policy | Value | Method | Status | Exact | Modulo | Proxy-only |
|---|---|---|---|---|---|---|---|
| 128 | legacy | 994 | last_integer | accepted_legacy_answer | 0 | 1 | 1 |
| 128 | terminal | 12994 | natural_language_conclusion | accepted_terminal_answer | 0 | 1 | 1 |
| 128 | declared | None | None | missing_terminal_answer | 0 | 0 | 0 |
| 256 | legacy | 994 | last_integer | accepted_legacy_answer | 0 | 1 | 1 |
| 256 | terminal | 12994 | natural_language_conclusion | accepted_terminal_answer | 0 | 1 | 1 |
| 256 | declared | None | None | missing_terminal_answer | 0 | 0 | 0 |
| 512 | legacy | 994 | last_integer | accepted_legacy_answer | 0 | 1 | 1 |
| 512 | terminal | 12994 | natural_language_conclusion | accepted_terminal_answer | 0 | 1 | 1 |
| 512 | declared | None | None | missing_terminal_answer | 0 | 0 | 0 |

Readable completion at cap(s) 128, 256, 512:

````text
Sure! Let's break it down step by step:

Step 1: Calculate the multiplication first.
147 * 84 = 12,388

Step 2: Add the result to 506.
12,388 + 506 = 12,994

Therefore, the exact value is 12,994.
````

## Exact 203 persistent proxy only eos at 512

Eligible problem IDs: 352.

Problem 1: `534 × 11 + 811`. Integer target: **6685**.

| Cap | Original new tokens | Actual stopping reason | Generate s |
|---|---|---|---|
| 128 | 90 | eos_before_limit | 3.069 |
| 256 | 90 | eos_before_limit | 2.989 |
| 512 | 90 | eos_before_limit | 2.893 |

| Cap | Policy | Value | Method | Status | Exact | Modulo | Proxy-only |
|---|---|---|---|---|---|---|---|
| 128 | legacy | 6835 | last_integer | accepted_legacy_answer | 0 | 1 | 1 |
| 128 | terminal | 6835 | natural_language_conclusion | accepted_terminal_answer | 0 | 1 | 1 |
| 128 | declared | None | None | missing_terminal_answer | 0 | 0 | 0 |
| 256 | legacy | 6835 | last_integer | accepted_legacy_answer | 0 | 1 | 1 |
| 256 | terminal | 6835 | natural_language_conclusion | accepted_terminal_answer | 0 | 1 | 1 |
| 256 | declared | None | None | missing_terminal_answer | 0 | 0 | 0 |
| 512 | legacy | 6835 | last_integer | accepted_legacy_answer | 0 | 1 | 1 |
| 512 | terminal | 6835 | natural_language_conclusion | accepted_terminal_answer | 0 | 1 | 1 |
| 512 | declared | None | None | missing_terminal_answer | 0 | 0 | 0 |

Readable completion at cap(s) 128, 256, 512:

````text
Sure! Let's break it down step by step:

Step 1: Calculate the multiplication first.
534 * 11 = 6024

Step 2: Add the result to 811.
6024 + 811 = 6835

Therefore, the exact value of 534 * 11 + 811 is 6835.
````

## Exact 203 no exact improvement at any budget

Eligible problem IDs: 364.

Problem 1: `534 × 11 + 811`. Integer target: **6685**.

| Cap | Original new tokens | Actual stopping reason | Generate s |
|---|---|---|---|
| 128 | 90 | eos_before_limit | 3.069 |
| 256 | 90 | eos_before_limit | 2.989 |
| 512 | 90 | eos_before_limit | 2.893 |

| Cap | Policy | Value | Method | Status | Exact | Modulo | Proxy-only |
|---|---|---|---|---|---|---|---|
| 128 | legacy | 6835 | last_integer | accepted_legacy_answer | 0 | 1 | 1 |
| 128 | terminal | 6835 | natural_language_conclusion | accepted_terminal_answer | 0 | 1 | 1 |
| 128 | declared | None | None | missing_terminal_answer | 0 | 0 | 0 |
| 256 | legacy | 6835 | last_integer | accepted_legacy_answer | 0 | 1 | 1 |
| 256 | terminal | 6835 | natural_language_conclusion | accepted_terminal_answer | 0 | 1 | 1 |
| 256 | declared | None | None | missing_terminal_answer | 0 | 0 | 0 |
| 512 | legacy | 6835 | last_integer | accepted_legacy_answer | 0 | 1 | 1 |
| 512 | terminal | 6835 | natural_language_conclusion | accepted_terminal_answer | 0 | 1 | 1 |
| 512 | declared | None | None | missing_terminal_answer | 0 | 0 | 0 |

Readable completion at cap(s) 128, 256, 512:

````text
Sure! Let's break it down step by step:

Step 1: Calculate the multiplication first.
534 * 11 = 6024

Step 2: Add the result to 811.
6024 + 811 = 6835

Therefore, the exact value of 534 * 11 + 811 is 6835.
````

## Modulo 203 cap without eos then terminal answer

Eligible problem IDs: 0.

No qualifying example.

## Modulo 203 final already present but wrong at 128

Eligible problem IDs: 364.

Problem 1: `534 × 11 + 811`. Integer target: **6685**.

| Cap | Original new tokens | Actual stopping reason | Generate s |
|---|---|---|---|
| 128 | 93 | eos_before_limit | 2.941 |
| 256 | 93 | eos_before_limit | 2.958 |
| 512 | 93 | eos_before_limit | 2.942 |

| Cap | Policy | Value | Method | Status | Exact | Modulo | Proxy-only |
|---|---|---|---|---|---|---|---|
| 128 | legacy | 6835 | last_integer | accepted_legacy_answer | 0 | 1 | 1 |
| 128 | terminal | 6835 | natural_language_conclusion | accepted_terminal_answer | 0 | 1 | 1 |
| 128 | declared | None | None | missing_terminal_answer | 0 | 0 | 0 |
| 256 | legacy | 6835 | last_integer | accepted_legacy_answer | 0 | 1 | 1 |
| 256 | terminal | 6835 | natural_language_conclusion | accepted_terminal_answer | 0 | 1 | 1 |
| 256 | declared | None | None | missing_terminal_answer | 0 | 0 | 0 |
| 512 | legacy | 6835 | last_integer | accepted_legacy_answer | 0 | 1 | 1 |
| 512 | terminal | 6835 | natural_language_conclusion | accepted_terminal_answer | 0 | 1 | 1 |
| 512 | declared | None | None | missing_terminal_answer | 0 | 0 | 0 |

Readable completion at cap(s) 128, 256, 512:

````text
Sure! Let's break it down step by step:

First, we multiply 534 by 11:
534 * 11 = 6024

Next, we add 811 to the result:
6024 + 811 = 6835

Therefore, the exact value of 534 * 11 + 811 is 6835.
````

## Modulo 203 legacy only credit no terminal answer

Eligible problem IDs: 6.

Problem 38: `687 × 57 + 930`. Integer target: **40089**.

| Cap | Original new tokens | Actual stopping reason | Generate s |
|---|---|---|---|
| 128 | 115 | eos_before_limit | 3.415 |
| 256 | 115 | eos_before_limit | 3.387 |
| 512 | 115 | eos_before_limit | 3.416 |

| Cap | Policy | Value | Method | Status | Exact | Modulo | Proxy-only |
|---|---|---|---|---|---|---|---|
| 128 | legacy | 29 | last_integer | accepted_legacy_answer | 0 | 1 | 1 |
| 128 | terminal | None | None | malformed_terminal_declaration | 0 | 0 | 0 |
| 128 | declared | None | None | malformed_terminal_declaration | 0 | 0 | 0 |
| 256 | legacy | 29 | last_integer | accepted_legacy_answer | 0 | 1 | 1 |
| 256 | terminal | None | None | malformed_terminal_declaration | 0 | 0 | 0 |
| 256 | declared | None | None | malformed_terminal_declaration | 0 | 0 | 0 |
| 512 | legacy | 29 | last_integer | accepted_legacy_answer | 0 | 1 | 1 |
| 512 | terminal | None | None | malformed_terminal_declaration | 0 | 0 | 0 |
| 512 | declared | None | None | malformed_terminal_declaration | 0 | 0 | 0 |

Readable completion at cap(s) 128, 256, 512:

````text
Sure! Let's break it down step by step:

1) First, we need to multiply 687 by 57:
   687 * 57 = 402,99

2) Then, we add 930 to our result from step 1:
   402,99 + 930 = 412,29

Therefore, the exact value of 687 * 57 + 930 is 412,29.
````

## Modulo 203 grouped or prefix disagreement

Eligible problem IDs: 28.

Problem 15: `147 × 84 + 506`. Integer target: **12854**.

| Cap | Original new tokens | Actual stopping reason | Generate s |
|---|---|---|---|
| 128 | 98 | eos_before_limit | 3.255 |
| 256 | 98 | eos_before_limit | 3.181 |
| 512 | 98 | eos_before_limit | 2.910 |

| Cap | Policy | Value | Method | Status | Exact | Modulo | Proxy-only |
|---|---|---|---|---|---|---|---|
| 128 | legacy | 994 | last_integer | accepted_legacy_answer | 0 | 1 | 1 |
| 128 | terminal | 12994 | natural_language_conclusion | accepted_terminal_answer | 0 | 1 | 1 |
| 128 | declared | None | None | missing_terminal_answer | 0 | 0 | 0 |
| 256 | legacy | 994 | last_integer | accepted_legacy_answer | 0 | 1 | 1 |
| 256 | terminal | 12994 | natural_language_conclusion | accepted_terminal_answer | 0 | 1 | 1 |
| 256 | declared | None | None | missing_terminal_answer | 0 | 0 | 0 |
| 512 | legacy | 994 | last_integer | accepted_legacy_answer | 0 | 1 | 1 |
| 512 | terminal | 12994 | natural_language_conclusion | accepted_terminal_answer | 0 | 1 | 1 |
| 512 | declared | None | None | missing_terminal_answer | 0 | 0 | 0 |

Readable completion at cap(s) 128, 256, 512:

````text
Sure! Let's break it down step by step:

Step 1: Calculate the multiplication first.
147 * 84 = 12,388

Step 2: Add the result to 506.
12,388 + 506 = 12,994

Therefore, the exact value of 147 * 84 + 506 is 12,994.
````

## Modulo 203 persistent proxy only eos at 512

Eligible problem IDs: 361.

Problem 1: `534 × 11 + 811`. Integer target: **6685**.

| Cap | Original new tokens | Actual stopping reason | Generate s |
|---|---|---|---|
| 128 | 93 | eos_before_limit | 2.941 |
| 256 | 93 | eos_before_limit | 2.958 |
| 512 | 93 | eos_before_limit | 2.942 |

| Cap | Policy | Value | Method | Status | Exact | Modulo | Proxy-only |
|---|---|---|---|---|---|---|---|
| 128 | legacy | 6835 | last_integer | accepted_legacy_answer | 0 | 1 | 1 |
| 128 | terminal | 6835 | natural_language_conclusion | accepted_terminal_answer | 0 | 1 | 1 |
| 128 | declared | None | None | missing_terminal_answer | 0 | 0 | 0 |
| 256 | legacy | 6835 | last_integer | accepted_legacy_answer | 0 | 1 | 1 |
| 256 | terminal | 6835 | natural_language_conclusion | accepted_terminal_answer | 0 | 1 | 1 |
| 256 | declared | None | None | missing_terminal_answer | 0 | 0 | 0 |
| 512 | legacy | 6835 | last_integer | accepted_legacy_answer | 0 | 1 | 1 |
| 512 | terminal | 6835 | natural_language_conclusion | accepted_terminal_answer | 0 | 1 | 1 |
| 512 | declared | None | None | missing_terminal_answer | 0 | 0 | 0 |

Readable completion at cap(s) 128, 256, 512:

````text
Sure! Let's break it down step by step:

First, we multiply 534 by 11:
534 * 11 = 6024

Next, we add 811 to the result:
6024 + 811 = 6835

Therefore, the exact value of 534 * 11 + 811 is 6835.
````

## Modulo 203 no exact improvement at any budget

Eligible problem IDs: 370.

Problem 1: `534 × 11 + 811`. Integer target: **6685**.

| Cap | Original new tokens | Actual stopping reason | Generate s |
|---|---|---|---|
| 128 | 93 | eos_before_limit | 2.941 |
| 256 | 93 | eos_before_limit | 2.958 |
| 512 | 93 | eos_before_limit | 2.942 |

| Cap | Policy | Value | Method | Status | Exact | Modulo | Proxy-only |
|---|---|---|---|---|---|---|---|
| 128 | legacy | 6835 | last_integer | accepted_legacy_answer | 0 | 1 | 1 |
| 128 | terminal | 6835 | natural_language_conclusion | accepted_terminal_answer | 0 | 1 | 1 |
| 128 | declared | None | None | missing_terminal_answer | 0 | 0 | 0 |
| 256 | legacy | 6835 | last_integer | accepted_legacy_answer | 0 | 1 | 1 |
| 256 | terminal | 6835 | natural_language_conclusion | accepted_terminal_answer | 0 | 1 | 1 |
| 256 | declared | None | None | missing_terminal_answer | 0 | 0 | 0 |
| 512 | legacy | 6835 | last_integer | accepted_legacy_answer | 0 | 1 | 1 |
| 512 | terminal | 6835 | natural_language_conclusion | accepted_terminal_answer | 0 | 1 | 1 |
| 512 | declared | None | None | missing_terminal_answer | 0 | 0 | 0 |

Readable completion at cap(s) 128, 256, 512:

````text
Sure! Let's break it down step by step:

First, we multiply 534 by 11:
534 * 11 = 6024

Next, we add 811 to the result:
6024 + 811 = 6835

Therefore, the exact value of 534 * 11 + 811 is 6835.
````
