"""Report exact JSON differences between frozen and recomputed scientific outputs.

This diagnostic applies no numerical tolerance and changes no input files.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import platform
import sys

ROOT = Path(__file__).resolve().parents[1]
NAMES = (
    "cell_metrics.json", "cap_transitions.json", "condition_contrasts.json",
    "model_diagnostics.json", "policy_sensitivity.json", "representative_examples.json",
)


def differences(expected, actual, path=()):
    if type(expected) is not type(actual):
        yield {"path": list(path), "kind": "type", "expected": expected, "actual": actual}
    elif isinstance(expected, dict):
        if expected.keys() != actual.keys():
            yield {"path": list(path), "kind": "keys", "expected": sorted(expected), "actual": sorted(actual)}
        for key in sorted(expected.keys() & actual.keys()):
            yield from differences(expected[key], actual[key], path + (key,))
    elif isinstance(expected, list):
        if len(expected) != len(actual):
            yield {"path": list(path), "kind": "length", "expected": len(expected), "actual": len(actual)}
        for index, (left, right) in enumerate(zip(expected, actual)):
            yield from differences(left, right, path + (index,))
    elif expected != actual:
        difference = {"path": list(path), "kind": "value", "expected": expected, "actual": actual}
        if type(expected) is float and math.isfinite(expected) and math.isfinite(actual):
            difference["absolute_difference"] = abs(actual - expected)
            difference["expected_ulp"] = math.ulp(expected)
            difference["difference_in_expected_ulps"] = abs(actual - expected) / math.ulp(expected)
        yield difference


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--actual", required=True, type=Path, help="Recomputed analysis directory")
    parser.add_argument("--expected", type=Path, default=ROOT / "case_studies/completion_budget_diagnostic/results")
    args = parser.parse_args()
    report = {"python": sys.version, "platform": platform.platform(), "machine": platform.machine(), "exact_match": True, "files": {}}
    for name in NAMES:
        with (args.expected / name).open() as stream:
            expected = json.load(stream)
        with (args.actual / name).open() as stream:
            actual = json.load(stream)
        diffs = list(differences(expected, actual))
        report["files"][name] = {"exact_match": not diffs, "difference_count": len(diffs), "differences": diffs[:100]}
        report["exact_match"] = report["exact_match"] and not diffs
    print(json.dumps(report, indent=2, allow_nan=False))
    return 0 if report["exact_match"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
