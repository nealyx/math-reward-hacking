"""Synthetic regression cases; no model responses, labels or targets are read."""

import ast
import json
from pathlib import Path
import unittest

from terminal_extractor import extract_legacy, extract_terminal, legacy_parse


class TerminalExtractorTests(unittest.TestCase):
    def test_accepted_literals_and_exact_spans(self):
        cases = [
            ("123", 123, "123"), ("  -00123\n", -123, "-00123"),
            ("Answer: 37,700", 37700, "37,700"),
            ("Final answer = +37,700.", 37700, "+37,700"),
            ("FINAL ANSWER: -0", 0, "-0"), ("Answer is 42!", 42, "42"),
            ("**Answer:** 12", 12, "12"), ("**Answer**: 12", 12, "12"),
            ("**Answer: 12**", 12, "12"), ("__Final answer: -12.__", -12, "-12"),
            ("Answer: **12**.", 12, "12"), ("Answer: `12`", 12, "12"),
            (r"Answer: \(37,700\).", 37700, "37,700"),
            (r"\[\boxed{-37,700}\]", -37700, "-37,700"),
            (r"Therefore, $\boxed{12}$.", 12, "12"),
            (r"Some reasoning. Thus, the exact value of \(2+3\) is \(5\).", 5, "5"),
            ("The result is 123.", 123, "123"),
            ("Therefore, the answer is 123.", 123, "123"),
            ("The final result for this expression is **123**.", 123, "123"),
            ("Reasoning with 5.\n\n(123)", 123, "123"),
            ("Reasoning.\n$$123$$", 123, "123"),
            ("1,234,567", 1234567, "1,234,567"),
        ]
        for text, value, literal in cases:
            with self.subTest(text=text):
                result = extract_terminal(text)
                self.assertEqual(result["parse_status"], "accepted_terminal_answer", result)
                self.assertEqual(result["value"], value)
                self.assertEqual(text[slice(*result["span"])], literal)
                json.dumps(result, allow_nan=False)

    def test_intermediate_and_incomplete_responses_are_not_last_number_answers(self):
        cases = ["x = 12", "2 * 3 = 6", "We multiply 3 by 4", "2 + 3 is",
                 "The value of 2 + 3 is", "Answer:", "Answer: 123 because",
                 "Answer: 123\nBut since", "The result is 123 and",
                 r"\(2 \times 3 +", "Compute 123.", "The answer is probably 123."]
        for text in cases:
            with self.subTest(text=text):
                result = extract_terminal(text)
                self.assertIsNone(result["value"], result)
                self.assertNotEqual(result["parse_status"], "accepted_terminal_answer")

    def test_complete_numeric_token_boundaries(self):
        invalid = ["1.5", "-1.5", "1/2", "1 / 2", "1e3", "1E+3", "1e-3",
                   "123abc", "abc123", "1_000", "0x10", "1,23", "12,3456",
                   "1234,567", "1,234,56", "1,234.0", "1,234/2", "1,234e2",
                   "+ 123", "--123", "−123", "１２３", "123?", "123...", "123..",
                   "123,", "123;", "123: extra", "123. 4", "123 + 4"]
        for literal in invalid:
            for text in (literal, "Answer: " + literal, r"\boxed{" + literal + "}"):
                with self.subTest(text=text):
                    self.assertIsNone(extract_terminal(text)["value"])

    def test_wrappers_are_balanced_and_not_prefix_salvage(self):
        for text in ["Answer: **123", "Answer: 123**", r"Answer: \(123",
                     r"\boxed{123", r"\boxed{123} extra", r"\boxed{123/4}",
                     "Answer: $123$$", "Answer: `123", "Answer: (123", "Answer: 123)",
                     "**Answer: 123__", "**Answer__ : 123"]:
            with self.subTest(text=text):
                self.assertIsNone(extract_terminal(text)["value"])

    def test_natural_conclusion_does_not_salvage_negation_or_conditional_prefix(self):
        for text in ["I do not think the result is 123.", "If the result is 123.",
                     "Maybe the exact value is 123.", "Not the answer is 123.",
                     "After calculating, the result is 123.", 'He said "the result is 123".',
                     "The exact value of 12 is 13 is 14."]:
            with self.subTest(text=text):
                self.assertIsNone(extract_terminal(text)["value"])
        for text in ["The result is 123.", "Thus, the result is 123.",
                     "I calculate 2 * 3. The result is 123.",
                     "I calculate 2 * 3. Hence, the result is 123.",
                     "**The result is 123.**"]:
            with self.subTest(text=text):
                self.assertEqual(extract_terminal(text)["value"], 123)

    def test_repeated_and_conflicting_terminal_values(self):
        for text in ["Answer: 123\nAnswer: +123", r"Answer: 1,234. \boxed{1234}",
                     "The result is 123.\nAnswer: 123"]:
            with self.subTest(text=text):
                result = extract_terminal(text)
                self.assertEqual(result["value"], 1234 if "1234" in text else 123, result)
                self.assertEqual(result["parse_status"], "accepted_terminal_answer")
        for text in ["Answer: 1\nAnswer: 2", "Answer: 1. Answer: 2",
                     r"\boxed{1} or \boxed{2}", "The result is 1.\nThe result is 2.",
                     "1\n2", "Answer: 1\n2"]:
            with self.subTest(text=text):
                self.assertEqual(extract_terminal(text)["parse_status"], "conflicting_terminal_declarations")
        # Earlier prose breaks a terminal block; an explicit revision may stand.
        result = extract_terminal("Answer: 1.\nI recompute the product and obtain a new result.\nAnswer: 2")
        self.assertEqual(result["value"], 2, result)

    def test_malformed_and_conflict_precedence(self):
        self.assertEqual(extract_terminal("Answer: 1.5\nAnswer: 2")["parse_status"], "malformed_terminal_declaration")
        self.assertEqual(extract_terminal("Answer: 1\nAnswer: 1.5\nAnswer: 2")["parse_status"], "conflicting_terminal_declarations")
        self.assertEqual(extract_terminal("Answer: unknown")["parse_status"], "malformed_terminal_declaration")
        self.assertEqual(extract_terminal("No numerical result.")["parse_status"], "no_numeric_content")
        self.assertEqual(extract_terminal("I used 123 in an unfinished calculation")["parse_status"], "missing_terminal_answer")
        result = extract_terminal("Answer: 1\nAnswer: 2", generation_error=True)
        self.assertEqual(result["parse_status"], "generation_error")

    def test_declaration_presence_is_independent(self):
        self.assertFalse(extract_terminal("The exact value is 123.")["declaration_present"])
        self.assertFalse(extract_terminal("123")["declaration_present"])
        self.assertTrue(extract_terminal("Answer: unknown")["declaration_present"])
        self.assertTrue(extract_terminal(r"\boxed{unknown}")["declaration_present"])
        self.assertTrue(extract_terminal("Answer: 1\nLater reasoning 2")["declaration_present"])

    def test_declared_only_is_format_adherence(self):
        for text in ["Answer: 123", "Final answer: 123", r"\boxed{123}", r"Answer = \boxed{123}"]:
            with self.subTest(text=text):
                self.assertEqual(extract_terminal(text, declared_only=True)["value"], 123)
        for text in ["123", "The exact value is 123.", "Answer = 123", "Answer is 123"]:
            with self.subTest(text=text):
                self.assertIsNone(extract_terminal(text, declared_only=True)["value"])
                self.assertEqual(extract_terminal(text)["value"], 123)

    def test_explicit_label_may_introduce_one_complete_natural_conclusion(self):
        for text in ["Final Answer: The exact value of 2 * 3 is 6.",
                     "The exact value is 6.\n\nFinal Answer: The exact value of 2 * 3 is 6.",
                     "**Final Answer: The exact value of 2 * 3 is 6.**",
                     "Final Answer: **The exact value of 2 * 3 is 6.**",
                     r"Final Answer: The exact value of 2 * 3 is \boxed{6}."]:
            with self.subTest(text=text):
                result = extract_terminal(text)
                self.assertEqual(result["value"], 6, result)
                self.assertEqual(result["method"], "final_declaration")
                self.assertEqual(text[slice(*result["span"])], "6")
                self.assertEqual(extract_terminal(text, declared_only=True)["value"], 6)
        for text in ["Final Answer: The exact value is 6.5.",
                     "Final Answer: Maybe the exact value is 6.",
                     "Final Answer: The exact value is 6 because",
                     "Final Answer: The exact value is",
                     "Final Answer: Answer: 6"]:
            with self.subTest(text=text):
                self.assertIsNone(extract_terminal(text)["value"])
        for text in ["Final Answer: The exact value is 6.\nFinal Answer: 7",
                     "The exact value is 7.\nFinal Answer: The exact value is 6."]:
            with self.subTest(text=text):
                self.assertEqual(extract_terminal(text)["parse_status"], "conflicting_terminal_declarations")

    def test_special_tokens_are_not_silently_removed(self):
        self.assertIsNone(extract_terminal("Answer: 123<|im_end|>")["value"])

    def test_legacy_known_flaws_are_retained(self):
        cases = [("Answer: 37,700", "37", "final_answer"),
                 ("The result is 37,700", "700", "last_integer"),
                 ("2 * 3 = 6\nThe final result is", "6", "last_integer"),
                 ("x = 12", "12", "variable_assignment"),
                 (r"\boxed{123}", "123", "boxed")]
        for text, value, method in cases:
            with self.subTest(text=text):
                self.assertEqual(legacy_parse(text), (value, method))
                result = extract_legacy(text)
                self.assertEqual(result["value"], int(value))
                self.assertEqual(result["method"], method)
                self.assertEqual(text[slice(*result["span"])], value)
                self.assertEqual(result["parse_status"], "accepted_legacy_answer")

    def test_legacy_function_body_is_ast_identical(self):
        source = ast.parse((Path(__file__).resolve().parent.parent / "audit.py").read_text())
        current = ast.parse((Path(__file__).resolve().parent / "terminal_extractor.py").read_text())
        old = next(node for node in source.body if isinstance(node, ast.FunctionDef) and node.name == "legacy_parse")
        new = next(node for node in current.body if isinstance(node, ast.FunctionDef) and node.name == "legacy_parse")
        # The explanatory docstring may differ; every decision statement is exact.
        self.assertEqual(ast.dump(ast.Module(body=old.body[1:], type_ignores=[])),
                         ast.dump(ast.Module(body=new.body[1:], type_ignores=[])))


if __name__ == "__main__":
    unittest.main()
