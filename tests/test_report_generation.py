import pytest

from scripts.generate_report import analyze_lengths, require_metrics


class RecordingTokenizer:
    def __init__(self):
        self.calls = []

    def encode(self, text, add_special_tokens):
        self.calls.append((text, add_special_tokens))
        return text.split()


def test_visible_length_analysis_uses_only_response_without_special_tokens():
    tokenizer = RecordingTokenizer()
    stats = analyze_lengths(
        [{"prompt": "do not count this prompt", "model_response": "two tokens"}],
        tokenizer,
    )
    assert tokenizer.calls == [("two tokens", False)]
    assert stats["mean_visible_completion_tokens"] == 2.0
    assert stats["total_retokenized_visible_completion_tokens"] == 2


def test_report_metrics_fail_closed_on_missing_required_value():
    with pytest.raises(KeyError, match="invalid_output_rate"):
        require_metrics(
            {
                "metrics": {
                    "true_accuracy": 0.1,
                    "mean_observed_reward": 0.2,
                    "reward_hacking_rate": 0.1,
                    "reward_hacking_given_reward": 0.5,
                    "correct_residue_among_incorrect": 0.1,
                    "single_digit_answer_rate": 0.0,
                    "small_answer_rate": 0.0,
                }
            },
            "example",
        )
