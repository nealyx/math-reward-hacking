# Publication Checklist

No files were deleted during the publication-hardening pass. Sizes are
approximate filesystem usage measured during the audit and can vary by platform.

## Release-prep size audit

- Repository working directory: about 8.8 GiB.
- Proposed first Git commit: 57 files, about 5.9 MiB total.
- `experiments/`: about 6.8 GiB; Milestone 3 accounts for about 6.6 GiB.
- Six confirmatory run directories: about 1.0 GiB each.
- Confirmatory intermediate checkpoints: 102 directories totaling about
  6.14 GiB; each is about 62 MiB.
- Confirmatory final-model directories: six directories totaling about
  166 MiB; each is about 28 MiB.
- Confirmatory final adapter tensors: six files totaling about 101 MiB; each is
  about 17 MiB.
- Raw response-bearing `eval_results.json`: about 4.1 MiB.
- Virtual environments: about 1.0 GiB (`.venv`) and 947 MiB
  (`.venv-antigravity`).

Outside the ignored virtual environments, no individual file exceeds 50 MiB.
The largest 30 individual files are tied `optimizer.pt` checkpoint states at
about 33.8 MiB each; there are 109 checkpoint directories across all historical
and confirmatory trees, totaling about 6.56 GiB. These are ignored and retained
locally. Because of the size tie, an arbitrary lexical subset appears in a
literal top-30 listing; the policy applies to every such optimizer state.

## A. Commit to GitHub

- `README.md`, `pyproject.toml`, `uv.lock`, and `.gitignore`.
- `src/`, `scripts/`, `tests/`, and `configs/`.
- `figures/` (about 442 KB for the two publication figures).
- `experiments/milestone3/data/` (about 296 KB), subject to confirming that the
  generated examples are intended for redistribution.
- `experiments/milestone3/report_milestone3.md`,
  `prespecification_addendum.md`, the unchanged historical plan, the frozen-hash
  record, and `experiments/milestone3/provenance/`.
- This checklist.

The root code license is Apache-2.0. Review generated model-card files and
upstream terms separately; the repository license does not automatically cover
Qwen-derived weights, third-party datasets, dependencies, or other upstream
artifacts.

## B. Keep locally/archive but do not commit

- `.venv/` (about 952 MB) and `.venv-antigravity/` (about 947 MB).
- Intermediate `checkpoint-*` directories (about 6.38 GiB across Milestone 3,
  including restart-only optimizer/scheduler/RNG state).
- Fresh `experiments/replications/` runs unless one is deliberately packaged.
- Local caches, editor configuration, OS metadata, and test caches.
- The older exploratory `experiments/grpo/` tree (about 179 MB), unless needed
  for a separately documented historical archive.
- Other exploratory/local outputs under `experiments/default/`,
  `experiments/smoke/`, `experiments/train_*`, and the root
  `experiments/variance_gate_samples.json`.

## C. Optional release via Git LFS, Hugging Face, or Zenodo

- The six confirmatory `final_model/` directories (about 168 MB total; about
  28 MB each). Publish with model cards that identify the base model, reward,
  seed, data hashes, and the repository license decision.
- `experiments/milestone3/eval_results.json` (about 4.1 MB), which contains the
  raw visible validation and sealed-test responses. A data/archive release is
  preferable if Git history size or response licensing is a concern.
- Selected checkpoint adapters needed to reproduce the trajectory analysis.
  Do not upload every restart-state file merely because it exists.
- A complete immutable archival snapshot, including all checkpoints, on Zenodo
  or equivalent if long-term forensic reproducibility is worth the roughly
  6.6 GiB Milestone 3 footprint.

## D. Safe to delete later

Only after the chosen archive is verified and the published artifact inventory
is final:

- Re-creatable virtual environments, bytecode, `.pytest_cache/`, editor/OS
  metadata, and local package/model caches.
- Duplicate restart-only optimizer, scheduler, and RNG files from intermediate
  checkpoints that are not part of the selected archive.
- Redundant intermediate checkpoints after retaining the exact checkpoints used
  in the validation figures and confirming their hashes.

Do not delete the frozen data/config, raw response-bearing evaluation JSON,
final adapters, Seed 201 before/after manifests, or preservation manifests as
routine cleanup. Any artifact reduction should be a separate, explicitly
reviewed operation with an archive-location record.
