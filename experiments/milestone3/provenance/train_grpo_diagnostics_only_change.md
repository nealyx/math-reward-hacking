# Training-script publication cleanup

The audited pre-cleanup `scripts/train_grpo.py` had SHA-256
`cdb26be6927116b5466cbedfba92e147f24059887511741d7c72c3f675c82450`.
That exact digest anchors the source reviewed before this cleanup; it is not the
digest recorded before Robust Seed 201.

The publication-hardening edit is limited to future-run diagnostics and save
bookkeeping:

- whitespace-delimited word counts were replaced by retokenized visible
  completion counts using the already-loaded training tokenizer with
  `add_special_tokens=False`;
- inferred prompt/completion totals and the misleading `computed_max_steps`
  diagnostic were removed;
- the exact number of completions observed by the active reward function is
  recorded directly; and
- `save_steps` now uses Trainer's supported `0.25` ratio so checkpoint cadence
  follows Trainer's own runtime step calculation.

Code review of the anchored source and the cleanup shows no change to:

- the model class or `from_pretrained` initialization call;
- either reward score or the selection of the condition-specific reward;
- learning rate (`5e-6` in the confirmatory config);
- per-device batch size (`1`);
- gradient accumulation (`4`);
- epochs (`1`);
- `max_completion_length` (`128`), `num_generations` (`4`), or temperature
  (`0.8`);
- LoRA rank, alpha, dropout, target modules, bias, or task type; or
- optimizer or scheduler configuration.

The script's post-cleanup digest is recorded in the generated report and the
publication validation record. No historical training artifact was modified or
rerun as part of this change.
