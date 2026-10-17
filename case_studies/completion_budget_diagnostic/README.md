# Completed diagnostic: public review package

The [project case study](../../README.md) explains the question, original experiment and later diagnostic. This directory packages already completed outputs for review; preparing it performed no new model inference or training. Nothing has been published by the packaging step.

**10,500 completions = seven fixed models × three completion limits × 500 shared development problems.** The six trained models form three Exact/Modulo seed pairs (201/202/203); Base is untrained. Repeated questions and caps are paired observations, not extra training replications. All scores use 500 unconditional examples per cell. The results do not establish consistent reward hacking or recover the historical cause.

## What readers receive

| Included | Scope |
|---|---|
| `data/development.jsonl` | The frozen 500 fresh diagnostic arithmetic problems and integer targets |
| `data/responses.jsonl.gz` | All 10,500 original canonical JSONL records, byte-preserving concatenation in filename order; 420 timing rows plus 10,080 full-run rows |
| `provenance/record_sha256.json` | SHA-256 for every original one-row record; gzip changes the container, not the records |
| `data/generation_configs.json` | All 21 resolved model/cap configurations |
| `results/` | All cells/policies, paired transitions/contrasts, baseline/Exact-202 diagnostics, extraction sensitivity, selected records, runtime and qualitative annotations |
| `figures/` | Six completed figures in PNG and SVG; primary figure is `all_seed_pair_differences.png` |
| `frozen/` | Byte-identical extractor, grammar, regression tests, analysis/plot functions, original inference entry-point sources and protocol for inspection |
| `examples.md` | All 42 model/stratum entries, including two empty strata; lowest eligible problem ID by fixed rule |
| `provenance/` | Source-export relationships, model identifiers/hashes, original README archive and explicit packaging amendment |

Each saved response includes prompt/text, original generated token IDs/counts, EOS position, stopping reason, extraction spans and three scoring policies. The historical-fallback audit sampled ten rows per model; two independent **AI-assisted** reviewers agree on 67/70, with three disputes retained. This is not human annotation or an arithmetic judge. The derived public annotation file omits machine-specific source-path metadata; labels and reasons are unchanged.

`manifest.json` records byte counts and hashes for the prepared package; `manifest.sha256` checksums that manifest. Hash consistency is not external authentication. [Export relationships](provenance/export_sources.json) identify unchanged source copies and derived projections; no original diagnostic artifact was rewritten.

## Availability boundaries

The repository already contains the original historical datasets, decoded evaluation responses, plan, report, provenance and source. The 500 fresh diagnostic questions are a development set; they are not the historical test or a new untouched final test.

Six final adapters, intermediate checkpoints, optimizer/RNG state, cached base/tokenizer files, source journals, duplicate atomic-commit files and detailed host telemetry remain in the local archive. **No model weights or historical-adapter download are supplied.** The pinned diagnostic base identifier and tensor/adapter hashes are in [models.json](provenance/models.json); they do not prove which unpinned base trained the historical adapters. Historical generated IDs and exact original training-source bytes cannot be recovered from this export.

The archived inference scripts show the implementation but require the original archive layout, omitted freezes/journals, local weights and hardware. They are not runnable plain-clone reproduction instructions. The portable helper below reproduces saved-output analysis instead, without importing Torch, Transformers, PEFT or network clients.

## Reproduce without generating anything

Run from the repository root. Python 3.10+ suffices for verification:

```sh
python3 -I -B case_studies/completion_budget_diagnostic/reproduce.py --verify-only
```

This checks all packaged file hashes before importing frozen scoring code, verifies the original bytes of all 10,500 records, independently recomputes arithmetic targets, replays all three frozen extractors, verifies the exact grid/reuse partition, derives stopping metadata from original IDs and checks all 10,500 paired cap-prefix comparisons. It checks recorded model/configuration identities, not absent weight bytes or token-to-text decoding.

Reanalysis needs NumPy, and plotting additionally needs Matplotlib. The recorded environment used Python 3.14.7, NumPy 2.5.3 and Matplotlib 3.11.1; [requirements-analysis.txt](requirements-analysis.txt) pins the latter two. Existing local dependencies were reused during packaging; no packages were installed.

```sh
python3 -I -B case_studies/completion_budget_diagnostic/reproduce.py \
  --output case_studies/completion_budget_diagnostic/reanalysis_local --figures
python3 -I -B -m unittest discover \
  -s case_studies/completion_budget_diagnostic -p 'test_reproduce.py' -v
python3 -I -B -m unittest discover \
  -s case_studies/completion_budget_diagnostic/frozen/pilot \
  -p 'test_terminal_extractor.py' -v
```

Reanalysis uses the unchanged frozen functions and compares all six recomputed scientific JSON outputs with `results/` before writing figures. It does not refit a parser, choose examples anew by judgment, evaluate new models, or resample training runs. Existing output directories are refused; choose a fresh `reanalysis_*` name for another audit. Pixel-identical figures are not guaranteed across rendering libraries/platforms; the numeric comparison is explicit.

Intervals use 10,000 paired-example bootstrap draws conditional on the fixed models. They are exploratory, pointwise and unadjusted for multiple comparisons; three training pairs do not establish new-run power or equivalence. The grammar is conservative and can reject a semantically understandable answer. See the [fixed analysis specification](frozen/full/analysis_spec.md) and [extractor grammar](frozen/pilot/extractor_spec.md).

## Preservation and review

The root README was part of the original 1,284-file preservation record. Its exact old bytes are retained in [README_before_case_study.md](provenance/README_before_case_study.md). The [authorized documentation amendment](provenance/readme_amendment.json) records old/new hashes and verifies the other 1,283 historical files plus all 68 pilot files unchanged. Frozen manifests and verifier code are not rewritten: their strict old README check will now flag this disclosed documentation change. The full local diagnostic seal and raw scientific outputs remain unchanged.

The [local verification summary](provenance/local_verification_summary.json) records completion-time checks, including all 43 frozen model/tokenizer files, but is not a substitute for readers possessing those bytes. Keep this distinction between a saved local verification result and a check independently reproducible from the public package.

The maintainer-only `scripts/package_diagnostic_case_study.py` exports selected saved artifacts and seals their review manifest. It is not needed by readers and depends on the local archive. It refuses existing export outputs. Review does not require rerunning a historical evaluator, retraining, paid compute or publishing any files.

Original code retains the repository's [Apache-2.0 license](../../LICENSE). Responses are model-generated research outputs; the repository code license does not assert ownership of generated text or grant rights to excluded upstream weights.
