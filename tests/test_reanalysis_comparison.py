"""The portability diagnostic must expose differences, never smooth them away."""
import importlib.util
import json
import math
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("compare_reanalysis", ROOT / "scripts/compare_reanalysis.py")
COMPARE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(COMPARE)


class ComparisonTests(unittest.TestCase):
    def test_identical_nested_values_match(self):
        value = {"counts": [500, 3], "interval": [None, 0.25], "flag": True}
        self.assertEqual(list(COMPARE.differences(value, value)), [])

    def test_even_one_ulp_is_reported_with_its_path(self):
        actual = math.nextafter(0.25, math.inf)
        diffs = list(COMPARE.differences({"ci95": [0.0, 0.25]}, {"ci95": [0.0, actual]}))
        self.assertEqual(len(diffs), 1)
        self.assertEqual(diffs[0]["path"], ["ci95", 1])
        self.assertEqual(diffs[0]["difference_in_expected_ulps"], 1.0)

    def test_observed_linux_endpoint_is_not_accepted_as_rounding(self):
        diffs = list(COMPARE.differences(0.2600499999999993, 0.262))
        self.assertEqual(len(diffs), 1)
        self.assertGreater(diffs[0]["absolute_difference"], 0.0019)
        self.assertGreater(diffs[0]["difference_in_expected_ulps"], 1e13)

    def test_integer_and_schema_changes_are_reported(self):
        expected = {"n": 500, "rows": [1, 2], "method": "paired"}
        actual = {"n": 499, "rows": [1], "unexpected": "paired"}
        diffs = list(COMPARE.differences(expected, actual))
        self.assertTrue(any(d["kind"] == "keys" for d in diffs))
        self.assertTrue(any(d["path"] == ["n"] for d in diffs))
        self.assertTrue(any(d["kind"] == "length" and d["path"] == ["rows"] for d in diffs))

    def test_boolean_float_and_integer_types_are_not_interchangeable(self):
        for expected, actual in [(1, True), (1, 1.0), (0.0, False)]:
            with self.subTest(expected=expected, actual=actual):
                self.assertEqual(list(COMPARE.differences(expected, actual))[0]["kind"], "type")

    def test_nonfinite_and_duplicate_json_are_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "result.json"
            for text in ['{"v": NaN}', '{"v": Infinity}', '{"v": 1e400}', '{"v": -1e400}', '{"n": 500, "n": 499}']:
                with self.subTest(text=text):
                    path.write_text(text)
                    with self.assertRaises(ValueError):
                        COMPARE.read_json(path)

    def test_large_difference_diagnostics_remain_serializable(self):
        for expected, actual in [(0.0, 0.001), (1e308, -1e308)]:
            with self.subTest(expected=expected, actual=actual):
                diffs = list(COMPARE.differences(expected, actual))
                self.assertEqual(len(diffs), 1)
                self.assertEqual(diffs[0]["difference_in_expected_ulps"], "exceeds finite float range")
                json.dumps(diffs, allow_nan=False)


class ComparisonCliTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.expected = Path(self.temporary.name) / "expected"
        self.actual = Path(self.temporary.name) / "actual"
        self.expected.mkdir()
        self.actual.mkdir()
        for directory in (self.expected, self.actual):
            for name in COMPARE.NAMES:
                (directory / name).write_text('{"n": 500, "value": 0.25}', encoding="utf-8")

    def compare(self):
        return subprocess.run(
            [sys.executable, "-I", "-B", str(ROOT / "scripts/compare_reanalysis.py"),
             "--expected", str(self.expected), "--actual", str(self.actual)],
            capture_output=True, text=True, timeout=30,
        )

    def test_missing_file_keeps_other_differences_and_returns_input_error(self):
        (self.actual / COMPARE.NAMES[0]).unlink()
        (self.actual / COMPARE.NAMES[1]).write_text('{"n": 499, "value": 0.25}', encoding="utf-8")
        result = self.compare()
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertNotIn("Traceback", result.stderr)
        report = json.loads(result.stdout)
        self.assertFalse(report["exact_match"])
        self.assertEqual(set(report["files"]), set(COMPARE.NAMES))
        missing = report["files"][COMPARE.NAMES[0]]
        self.assertEqual(missing["status"], "error")
        self.assertEqual(missing["errors"][0]["side"], "actual")
        self.assertEqual(missing["errors"][0]["path"], str(self.actual / COMPARE.NAMES[0]))
        self.assertEqual(report["files"][COMPARE.NAMES[1]]["difference_count"], 1)
        self.assertTrue(report["files"][COMPARE.NAMES[-1]]["exact_match"])

    def test_invalid_json_on_both_sides_is_reported_without_hiding_other_files(self):
        (self.expected / COMPARE.NAMES[0]).write_text('{"n": 500, "n": 499}', encoding="utf-8")
        (self.actual / COMPARE.NAMES[0]).write_bytes(b"\xff")
        (self.actual / COMPARE.NAMES[1]).write_text('{"value": NaN}', encoding="utf-8")
        result = self.compare()
        self.assertEqual(result.returncode, 2, result.stderr)
        report = json.loads(result.stdout)
        self.assertFalse(report["exact_match"])
        self.assertEqual(report["input_error_count"], 3)
        self.assertEqual(
            [e["side"] for e in report["files"][COMPARE.NAMES[0]]["errors"]],
            ["expected", "actual"],
        )
        self.assertTrue(report["files"][COMPARE.NAMES[-1]]["exact_match"])

    def test_complete_match_and_one_ulp_difference_keep_strict_exit_codes(self):
        result = self.compare()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(json.loads(result.stdout)["exact_match"])
        (self.actual / COMPARE.NAMES[-1]).write_text(
            json.dumps({"n": 500, "value": math.nextafter(0.25, math.inf)}), encoding="utf-8",
        )
        result = self.compare()
        self.assertEqual(result.returncode, 1, result.stderr)
        report = json.loads(result.stdout)
        self.assertFalse(report["exact_match"])
        self.assertEqual(report["input_error_count"], 0)
        self.assertEqual(report["files"][COMPARE.NAMES[-1]]["differences"][0]["difference_in_expected_ulps"], 1.0)


if __name__ == "__main__":
    unittest.main()
