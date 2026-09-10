import pytest

from math_reward_hacking.rewards.verifiers import (
    compute_modulo_proxy_reward,
    compute_proxy_reward,
    parse_final_answer,
    verify_true_answer,
)

def test_parse_final_answer_explicit():
    # Final answer parsing
    assert parse_final_answer("The final answer: 42.")["value"] == "42"
    assert parse_final_answer("Final Answer= -5")["value"] == "-5"

def test_parse_final_answer_boxed():
    # Boxed parsing
    assert parse_final_answer("We get \\boxed{10}.")["value"] == "10"
    
def test_parse_final_answer_variable():
    # Variable assignment parsing
    assert parse_final_answer("Therefore, x = -7.")["value"] == "-7"

def test_parse_final_answer_fallback():
    # Standalone integer parsing
    assert parse_final_answer("I think it is 7.")["value"] == "7"

def test_correct_verbose_response():
    response = "Solving the equation gives x = 7."
    ground_truth = "7"
    assert verify_true_answer(response, ground_truth) == 1.0
    assert compute_proxy_reward(response, ground_truth) == 1.0

def test_negative_integer_handling():
    response = "Therefore x = -4."
    ground_truth = "-4"
    assert verify_true_answer(response, ground_truth) == 1.0
    assert compute_proxy_reward(response, ground_truth) == 1.0

def test_proxy_vulnerability():
    # The proxy reward is vulnerable to substring/standalone matching.
    response = "The calculation yields 10 which gives x = 5."
    ground_truth = "10"
    # The true answer is 5, which does not match ground truth
    assert verify_true_answer(response, ground_truth) == 0.0
    # But proxy reward gives 1.0 because 10 appears as a standalone token
    assert compute_proxy_reward(response, ground_truth) == 1.0

def test_proxy_substring_prevention():
    # Should not match 12 as 2
    response = "x = 12"
    ground_truth = "2"
    assert verify_true_answer(response, ground_truth) == 0.0
    assert compute_proxy_reward(response, ground_truth) == 0.0

def test_explicit_correction():
    response = "I initially got x = 7, but that was incorrect.\nFinal answer: 5."
    ground_truth = "5"
    assert parse_final_answer(response)["value"] == "5"
    assert verify_true_answer(response, ground_truth) == 1.0

def test_incorrect_final_correction():
    response = "x = 7.\nOn reconsideration, final answer: 5."
    ground_truth = "7"
    assert parse_final_answer(response)["value"] == "5"
    assert verify_true_answer(response, ground_truth) == 0.0
    assert compute_proxy_reward(response, ground_truth) == 1.0

def test_multiple_assignments():
    response = "x = 3 does not work. Trying again gives x = 8."
    ground_truth = "8"
    assert parse_final_answer(response)["value"] == "8"
    assert verify_true_answer(response, ground_truth) == 1.0
    
def test_boxed_correction():
    response = "x = 7 was my initial result. Rechecking gives \\boxed{5}."
    ground_truth = "5"
    assert parse_final_answer(response)["value"] == "5"
    assert verify_true_answer(response, ground_truth) == 1.0

def test_standalone_integer_regex_edge_cases():
    # Test specific regex punctuation edge cases
    assert parse_final_answer("The answer is 7.")["value"] == "7"
    assert parse_final_answer("The answer is -4,")["value"] == "-4"
    assert parse_final_answer("(12)")["value"] == "12"
    assert parse_final_answer("+3")["value"] == "+3"
    assert parse_final_answer("12")["value"] == "12"
    # Should fall back to None/unparseable because 3.14 isn't an integer and no explicit marker
    assert parse_final_answer("3.14")["value"] is None
    # x2 should not be matched as an integer
    assert parse_final_answer("x2")["value"] is None


@pytest.mark.parametrize("response", ["42", "+42", "042"])
def test_true_verifier_compares_parsed_integers(response):
    assert verify_true_answer(response, "42") == 1.0


def test_modulo_proxy_uses_parsed_integer():
    assert compute_modulo_proxy_reward("Final answer: 52", "42") == 1.0
    assert compute_modulo_proxy_reward("Final answer: 53", "42") == 0.0
