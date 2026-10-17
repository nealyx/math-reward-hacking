"""Focused packaging regressions; no inference, model weights or network."""
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location("public_reproduce", Path(__file__).with_name("reproduce.py"))
R = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(R)


class PackagingTests(unittest.TestCase):
    def test_json_seed_keys_normalize_without_hiding_metric_changes(self):
        computed = {"seed_differences": {201: -0.022, 202: 0.01, 203: -0.012}}
        saved = {"seed_differences": {"201": -0.022, "202": 0.01, "203": -0.012}}
        self.assertTrue(R.matches_saved_json(computed, saved))
        saved["seed_differences"]["202"] = 0.012
        self.assertFalse(R.matches_saved_json(computed, saved))

    def test_existing_output_is_rejected_before_inputs_are_read(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)
            with patch.object(R, "verify", side_effect=AssertionError("must not read inputs")):
                with self.assertRaisesRegex(ValueError, "Output already exists"):
                    R.run(path / "missing-package", output=path)

    def test_manifest_detects_changed_bytes_before_source_import(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source = root / "input.txt"
            source.write_text("original")
            (root / "manifest.json").write_text(json.dumps({"files": {"input.txt": {
                "sha256": hashlib.sha256(b"original").hexdigest(), "bytes": 8}}}))
            R.verify_manifest(root, required=("input.txt",))
            source.write_text("modified")
            with self.assertRaisesRegex(ValueError, "Manifest hash/size mismatch"):
                R.verify_manifest(root, required=("input.txt",))

    def test_manifest_rejects_path_escape_and_symlink(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            target = root / "target"
            target.write_text("x")
            (root / "link").symlink_to(target)
            for name in ("../target", "/target", "link"):
                with self.subTest(name=name), self.assertRaises(ValueError):
                    R.packaged_path(root, name)

    def test_archive_rejects_noncanonical_row_bytes(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "data").mkdir()
            row = {"model": "Base", "max_new_tokens": 128, "problem_id": 0, "phase": "timing"}
            raw = (json.dumps(row) + "\n").encode()
            with gzip.open(root / "data/responses.jsonl.gz", "wb") as stream:
                stream.write(raw)
            with self.assertRaisesRegex(ValueError, "row-byte digest mismatch"):
                R.read_responses(root, {R.original_record_name(row): "0" * 64})

    def test_archive_cannot_treat_missing_coverage_as_arithmetic_failures(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "data").mkdir()
            row = {"model": "Base", "max_new_tokens": 128, "problem_id": 0, "phase": "timing"}
            raw = (json.dumps(row) + "\n").encode()
            with gzip.open(root / "data/responses.jsonl.gz", "wb") as stream:
                stream.write(raw)
            with self.assertRaisesRegex(ValueError, "exactly 10,500 responses"):
                R.read_responses(root, {R.original_record_name(row): R.digest_bytes(raw)})

    def test_archive_rejects_duplicate_records(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "data").mkdir()
            row = {"model": "Base", "max_new_tokens": 128, "problem_id": 0, "phase": "timing"}
            raw = (json.dumps(row) + "\n").encode()
            with gzip.open(root / "data/responses.jsonl.gz", "wb") as stream:
                stream.write(raw + raw)
            with self.assertRaisesRegex(ValueError, "without duplicates"):
                R.read_responses(root, {R.original_record_name(row): R.digest_bytes(raw)})

    def test_smoke_control_and_wrong_phase_rows_are_rejected(self):
        for phase, example in (("smoke", 0), ("forced_eos", 0), ("full", 0), ("timing", 20)):
            row = {"model": "Base", "max_new_tokens": 128, "problem_id": example, "phase": phase}
            with self.subTest(phase=phase, example=example), self.assertRaisesRegex(ValueError, "Wrong timing/full phase"):
                R.row_identity(row)

    def test_development_duplicates_are_not_silently_deduplicated(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "development.jsonl"
            row = {"problem_id": 0, "a": 1, "b": 2, "c": 3, "result": 5}
            path.write_text((json.dumps(row) + "\n") * 500)
            with self.assertRaisesRegex(ValueError, "500 unique IDs"):
                R.read_development(path)


if __name__ == "__main__":
    unittest.main()
