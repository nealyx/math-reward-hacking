import re
from typing import Dict, Optional

def parse_final_answer(response: str) -> Dict[str, Optional[str]]:
    """
    Parses the intended final answer from a model's reasoning trace.
    Uses a strict precedence hierarchy and returns metadata for auditing.
    """
    # 1. Highest priority: explicit final answer markers.
    final_answer_regex = r"(?i)(?:final\s*answer|answer)\s*(?::|={1,})\s*([+-]?\d+)"
    final_matches = re.findall(final_answer_regex, response)
    if final_matches:
        return {"value": final_matches[-1].strip(), "method": "final_answer"}
        
    # 2. Strong answer markers: \boxed{X} or x = X.
    combined_regex = r"\\boxed{([+-]?\d+)}|x\s*=\s*([+-]?\d+)"
    matches = list(re.finditer(combined_regex, response))
    if matches:
        last_match = matches[-1]
        if last_match.group(1):
            return {"value": last_match.group(1).strip(), "method": "boxed"}
        else:
            return {"value": last_match.group(2).strip(), "method": "variable_assignment"}
            
    # 3. Final fallback: last standalone integer token.
    standalone_regex = r"(?<![\w.])([+-]?\d+)(?!\w)(?!\.\d)"
    matches = re.findall(standalone_regex, response)
    if matches:
        return {"value": matches[-1].strip(), "method": "last_integer"}
        
    return {"value": None, "method": "unparseable"}

def verify_true_answer(response: str, ground_truth: str) -> float:
    """
    Returns 1.0 if parsed integers are mathematically equal.

    Accepted integer spellings such as ``42``, ``+42``, and ``042`` are
    equivalent. Unparseable responses or ground truths receive zero reward.
    """
    parsed = parse_final_answer(response)
    if parsed["value"] is not None:
        try:
            if int(parsed["value"]) == int(ground_truth.strip()):
                return 1.0
        except (AttributeError, ValueError):
            pass
    return 0.0

def compute_proxy_reward(response: str, ground_truth: str) -> float:
    """
    Returns 1.0 if the ground truth integer is present as a standalone token anywhere.
    """
    standalone_regex = r"(?<![\w.])([+-]?\d+)(?!\w)(?!\.\d)"
    standalone_matches = re.findall(standalone_regex, response)
    if ground_truth.strip() in [m.strip() for m in standalone_matches]:
        return 1.0
    return 0.0

def compute_modulo_proxy_reward(response: str, ground_truth: str) -> float:
    """
    Returns 1.0 if the parsed intended answer mod 10 equals ground truth mod 10.
    """
    parsed = parse_final_answer(response)
    if parsed["value"] is not None:
        try:
            parsed_int = int(parsed["value"])
            gt_int = int(ground_truth.strip())
            if parsed_int % 10 == gt_int % 10:
                return 1.0
        except ValueError:
            pass
    return 0.0
