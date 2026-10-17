# Diagnostic case study — review notes

Prepared locally; no commit, push, publication, new inference or training was performed for this packaging task.

The [project README](../README.md) now leads with the research question and limited finding, distinguishes the original six-run experiment from the later diagnostic, shows one primary all-seed figure, and gives representative examples, limitations, availability and saved-output reproduction commands.

The [curated package](completion_budget_diagnostic/README.md) contains 51 manifest-listed files, about 7.7 MB, plus its manifest/checksum. All 10,500 original response records fit in a 3.35 MB gzip without changing any record bytes. The package includes 500 shared problems, original token/stop metadata, all six figures, numeric outputs, selected examples, frozen scoring/analysis code and model identifiers. No model weights, source journals, restart states or machine-specific host metadata are included. Full inference reproduction remains unavailable from a plain clone because historical adapters are not distributed. Package-local Git attributes preserve the manifest-bound bytes without line-ending conversion.

Validation completed:

- Standard-library-only verification of all 10,500 rows, the 420/10,080 partition, 21 cells, frozen extraction and all 10,500 cross-cap prefix comparisons.
- Exact parsed equality for all six recomputed scientific JSON outputs; six figures rendered from those outputs. Validation outputs remain local in the ignored `reanalysis_verified/` directory.
- Nine portable-helper regression tests and 13 unchanged extractor regression tests passed.
- All 25 local links in the new README/package/example documents resolve.
- All 31,203 files in the original full diagnostic seal rehashed successfully. All 68 pilot files and the other 1,283 historically protected files remain unchanged.

The old root README is preserved byte-for-byte and the authorized documentation amendment records its original and updated hashes. Frozen historical manifests and verifier code were not changed; their strict old README check now flags this disclosed documentation update.

The first packaging reanalysis incorrectly compared integer-keyed Python mappings with string-keyed JSON mappings, despite emitting identical JSON. The adapter now compares JSON-normalized mappings, with a regression test that still rejects real metric changes. Initial adapter/tests/manifest and the partial audit remain locally preserved under ignored `reanalysis_validation/packaging_attempt_001/`. No scientific code, parser, results or examples changed.

Final package manifest SHA-256: `0e0f537fadd5e5d7b56c2958aeee04d3c3eec9643e6a16915701e7ad84cc41bd`.

Review the README interpretation and public-availability boundary alongside the portable helper and export provenance. The main conclusion remains inconclusive across three training-seed pairs; completion count is not training replication count, and reconstructed inference cannot recover the historical cause.
