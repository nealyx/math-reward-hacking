# Prespecification Addendum

This addendum records factual clarifications discovered during the post-hoc
publication audit. It does not modify the historical
[`preregistered_plan.md`](preregistered_plan.md), and no historical plan text
was retroactively changed. The protocol was internally prespecified; it was not
externally registered or independently timestamped.

## Seeds and evaluation budget

- The six confirmatory runs used Seeds 201, 202, and 203 once per reward
  condition. The historical plan's Seeds 42, 43, and 44 were illustrative
  examples rather than the final training-seed list.
- Seed 101 was exploratory and is excluded from confirmatory summaries.
- The competence-screen code used a 256-token generation budget. Confirmatory
  training and evaluation used a maximum completion/generation length of 128.
  The competence screen and the sealed-test Base result are therefore distinct
  artifacts and should not be treated as the same measurement.

## Step-count and checkpoint incident

Helper logic in the historical training script computed a value of 125 and
labeled it `computed_max_steps`. Surviving trainer states for all six
confirmatory runs record `global_step=500` and `max_steps=500`. The manual
estimate did not account for GRPOTrainer's effective sampling/step semantics.
It was used for checkpoint/save-frequency bookkeeping and a post-training
assertion; surviving evidence does not show that it set optimization length.

The discrepancy was discovered before the sealed test was opened. Robust Seed
201 has a `final_model`, and its adapter is byte-identical to the adapter in
`checkpoint-500`. The earlier narrative that the assertion prevented
`final_model` creation was incorrect.

## Outcomes of the historical hypotheses

- **H1 — not satisfied on the sealed test.** Base exact accuracy was 4.2%,
  below the prespecified >10% threshold. The earlier competence screen reported
  22% with its different 256-token setup; it is not the sealed-test baseline.
- **H2 — descriptively supported.** Mean Robust exact accuracy increased from
  4.2% for Base to 24.2%. No prespecified significance test was conducted.
- **H3 — not supported as proposed.** Proxy exact accuracy was 25.13%, not
  lower than Robust exact accuracy at 24.20%. Proxy modulo-10 accuracy was
  97.93%.
- **H4 — not supported by the proposed small/single-digit signature.** The
  Proxy small-answer rate (1.2%) was lower than the Robust rate (5.8%).
- **H5 — mixed/partially supported.** Proxy modulo-10 validation accuracy rose
  to 97–99% at final checkpoints while exact validation accuracy remained
  21–23%, but the paths were not uniformly monotonic and Robust Seeds 201 and
  203 also reached 96–98% modulo-10 validation accuracy.

These outcome labels are descriptive. They do not assert significance,
equivalence, causality, intentional cheating, or a stable condition effect.
