# Reproduction across platforms

The public package separates two checks:

1. **Verify the saved evidence:** file and record hashes, arithmetic targets,
   extraction, coverage, stopping metadata and cross-cap prefixes. This
   standard-library workflow passes on the tested Linux x86-64 and macOS ARM
   environments.
2. **Recompute the numerical analyses:** replay the frozen NumPy bootstrap and
   compare all six output files exactly. This reproduces the saved outputs on
   the tested local and hosted macOS ARM environments. Linux x86-64 with the same NumPy version
   differs at one bootstrap interval endpoint.

The second limitation is not fixed by broadening a floating-point tolerance.
The frozen package, original numerical results and strict reproduction command
remain byte-identical.

## What differed

The October 20, 2026 Linux audit found exactly one differing JSON leaf:

`model_diagnostics.json[146].ci95[1]`

| Field | Saved / tested macOS ARM | Linux x86-64 |
|---|---:|---:|
| Contrast | `proxy_201_minus_Base` | Same |
| Completion limit / policy / metric | 128 / legacy / proxy-only | Same |
| Examples | 500 | 500 |
| Point estimate | 0.212 | 0.212 |
| Lower interval endpoint | 0.162 | 0.162 |
| Upper interval endpoint | 0.2600499999999993 | 0.262 |

The endpoint difference is about **0.195 percentage points**, not a last-bit
serialization discrepancy. Every other value in that file and all five other
numerical files matched exactly. This auxiliary diagnostic concerns one trained
model relative to Base; the primary paired-condition results are unchanged.

The [exact-difference CI log](https://github.com/nealyx/math-reward-hacking/actions/runs/39439591453)
records the mismatch. All environments used NumPy 2.5.3. The local macOS 27
replay used Python 3.13.15; hosted Linux and macOS 26 used Python 3.13.16.
The [hosted macOS ARM job](https://github.com/nealyx/math-reward-hacking/actions/runs/39440182969/job/118687640642)
reproduced all six numerical files exactly and regenerated the figures.

## Where the replay diverged

The [probe](../scripts/probe_bootstrap.py) rebuilds the affected contrast from
the verified public responses, then repeats the frozen bootstrap operations.
It uses categories `[-1, 0, 1]`, counts `[38, 318, 144]`, 10,000 multinomial
draws and the original derived seed `1876199485306839901`.

| Check | Cross-platform observation |
|---|---|
| Input values, categories, counts and probabilities | Exact match |
| Initial and final PCG64 state | Exact match |
| First 10,000 raw PCG64 integers | Exact match |
| Multinomial sampled-count matrix | Different |
| Bootstrap means and upper-tail neighbors | Different |

The divergence is visible in the distribution sampler's output before the
percentile calculation. These checks do not identify the exact compiler,
math-library or instruction-level cause. NumPy's
[random compatibility policy](https://numpy.org/doc/stable/reference/random/compatibility.html)
conditions stream reproducibility on the build, environment and machine, not
just the version and seed.

The observed [local macOS probe](portability/macos-bootstrap-probe.json),
[hosted macOS probe](portability/macos-ci-bootstrap-probe.json) and
[Linux probe](portability/linux-bootstrap-probe.json) retain full fingerprints,
histograms, quantile neighbors and environment information. Both macOS probes
have the same sampled-count and bootstrap-mean fingerprints. These are new
portability diagnostics of the public saved data, not new model runs or
replacement scientific results.

## What CI requires

The workflow verifies saved evidence and reader tools on Linux with Python
3.10/3.13 and macOS ARM with Python 3.13. Python 3.13 jobs also run the arithmetic
and historical result regression tests and print the bootstrap probe.

All six numerical files must agree exactly on the hosted `macos-26` ARM runner.
Linux is not claimed as a supported exact numerical replay environment. A green
workflow therefore means that the documented platform checks passed; it does
not assert identical bootstrap samples across platforms. No failing analysis
step is marked `continue-on-error`, and the original strict command still fails
on the observed Linux difference.

## How to check your environment

Verification requires Python 3.10+ without analysis dependencies:

```sh
python3 -I -B case_studies/completion_budget_diagnostic/reproduce.py --verify-only
```

For exact numerical replay, install the package's recorded analysis dependencies
and use the tested macOS ARM environment. A different platform or build can
still produce a strict comparison failure.

If a numerical replay fails after writing its analysis directory, inspect the
differences rather than increasing a tolerance:

```sh
python3 -I -B scripts/compare_reanalysis.py \
  --actual case_studies/completion_budget_diagnostic/reanalysis_local/analysis
python3 -I -B scripts/probe_bootstrap.py
```

The comparator exits unsuccessfully for any difference, including integer,
schema, type or floating-point changes. The probe reports observations without
accepting or overwriting an alternate result. The original reproduction report
continues to record a strict failure when outputs differ.

[Return to the study](../README.md)
