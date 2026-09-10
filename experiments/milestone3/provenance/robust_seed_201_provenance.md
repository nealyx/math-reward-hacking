# Provenance for Robust Seed 201

- Robust Seed 201 completed before the pipeline interruption.
- `checkpoint-500/trainer_state.json` recorded `global_step=500` and `max_steps=500`.
- `seed=201` was verified.
- The manual helper logic produced `computed_max_steps=125`, whereas the trainer runtime recorded 500. The estimate did not account for the effective GRPO sampling/step semantics.
- The value was used for checkpoint/save-frequency bookkeeping and a post-training assertion. No surviving evidence shows optimization length was set to 125.
- The issue was discovered before the sealed test was accessed.
- `final_model` exists. Its `adapter_model.safetensors` is byte-identical to the corresponding file in `checkpoint-500`, and both are covered by preservation manifests.
- The frozen manifest records the original training-source SHA-256 as `aa220bc2a78624fd70a49eb0ee22e09263aa0b03bd3b15b166a5cccb264b73d2`.
- The original source bytes do not survive. The recorded digest therefore cannot be independently recomputed from those bytes or cryptographically establish which exact bytes Robust Seed 201 executed.
- The audited post-incident, pre-publication-cleanup `train_grpo.py` SHA-256 was `cdb26be6927116b5466cbedfba92e147f24059887511741d7c72c3f675c82450`.
- Filesystem timestamps are not treated as proof of execution order or source identity.
