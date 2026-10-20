"""Reader inspection checks; use saved records and never run a model."""
import contextlib
import importlib.util
import io
from pathlib import Path
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "inspect_diagnostic_example", ROOT / "scripts" / "inspect_diagnostic_example.py"
)
INSPECT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(INSPECT)


class SavedExampleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.verifier = INSPECT.load_verifier()
        _, cls.index, _ = cls.verifier.verify(INSPECT.PACKAGE)

    def test_documented_comma_example_matches_verified_saved_record(self):
        row = self.index["proxy_202", 512, 0]
        self.assertEqual(row["ground_truth"], 18874)
        self.assertEqual(row["scores"]["legacy"]["value"], 874)
        self.assertEqual(row["scores"]["terminal"]["value"], 18874)
        self.assertIsNone(row["scores"]["declared"]["value"])
        text = INSPECT.render_example(self.index, "proxy_202", 0, (512,), True)
        self.assertIn("| 512 | legacy | 874 | 0 | 1 | 1 |", text)
        self.assertIn("| 512 | terminal | 18874 | 1 | 1 | 0 |", text)
        self.assertIn(row["raw_completion"], text)

    def test_truncation_example_keeps_limits_and_correctness_separate(self):
        short = self.index["robust_202", 128, 1]
        longer = self.index["robust_202", 256, 1]
        self.assertEqual(short["ground_truth"], 6685)
        self.assertTrue(short["readable_completion"].rstrip().endswith("Therefore,"))
        self.assertEqual(longer["scores"]["terminal"]["value"], 6785)
        self.assertFalse(longer["scores"]["terminal"]["exact_correct"])
        text = INSPECT.render_example(self.index, "robust_202", 1, (128, 256))
        self.assertNotIn("| 512 |", text)

    def test_no_response_or_scores_are_displayed_after_failed_verification(self):
        output, errors = io.StringIO(), io.StringIO()
        with patch.object(INSPECT, "load_verifier", return_value=self.verifier):
            with patch.object(self.verifier, "verify", side_effect=ValueError("tampered record")):
                with contextlib.redirect_stdout(output), contextlib.redirect_stderr(errors):
                    status = INSPECT.main(["--cap", "512"])
        self.assertEqual(status, 1)
        self.assertEqual(output.getvalue(), "")
        self.assertIn("tampered record", errors.getvalue())

    def test_invalid_problem_is_rejected_before_reading_corpus(self):
        with patch.object(INSPECT, "load_verifier", return_value=self.verifier):
            with patch.object(self.verifier, "verify") as verify:
                with contextlib.redirect_stderr(io.StringIO()):
                    with self.assertRaises(SystemExit) as exc:
                        INSPECT.main(["--problem-id", "500"])
                self.assertEqual(exc.exception.code, 2)
                verify.assert_not_called()


if __name__ == "__main__":
    unittest.main()
