# Public onboarding update — October 20, 2026

This update adds a reader navigation table, a worked-example guide and a
standard-library command for inspecting an already saved diagnostic response.
The command calls the existing package verifier before displaying saved scores.
It does not replace the extractor, rescore under a new policy, run inference or
train a model.

A GitHub Actions workflow verifies the public saved-output package, exercises the
reader tools and reproduces numerical analyses and figures on CPU. It does not
run the historical training or inference entry points.

The preceding root README is preserved in commit
[`66ec1f5`](https://github.com/nealyx/math-reward-hacking/blob/66ec1f5/README.md)
with SHA-256
`c0949a9a78f0ae7495c33089adffbd90a920bbc90c1f96e09b029ab1deb0f1f1`.
The earlier
[packaging amendment](../case_studies/completion_budget_diagnostic/provenance/readme_amendment.json)
describes that historical README version; it is not a hash claim about this
later navigation update.

Every tracked file under `case_studies/completion_budget_diagnostic/` is retained
byte-for-byte. Its manifest, frozen methods, data, results, examples, figures and
provenance are unchanged. No historical source, training configuration or result
is changed by this update.

The two real examples in the walkthrough are the same examples already described
in the preceding root README and fixed-rule supplement. The `42`/`52`/`53` table
is explicitly labeled as a constructed explanation of the reward functions.
