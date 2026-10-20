"""Report exact JSON differences between frozen and recomputed scientific outputs.

This diagnostic applies no numerical tolerance and changes no input files.
Exit codes: 0 for exact agreement, 1 for differences, 2 for unreadable or
invalid inputs. Every named file is reported, including after an input error.
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


def read_json(path):
    def reject_constant(value):
        raise ValueError(f"Nonfinite JSON number: {value}")

    def finite_float(value):
        parsed = float(value)
        if not math.isfinite(parsed):
            raise ValueError(f"JSON number exceeds finite float range: {value}")
        return parsed

    def unique_keys(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"Duplicate JSON key: {key}")
            result[key] = value
        return result

    with path.open(encoding="utf-8") as stream:
        return json.load(
            stream, parse_constant=reject_constant, parse_float=finite_float,
            object_pairs_hook=unique_keys,
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
            magnitude = abs(actual - expected)
            difference["absolute_difference"] = magnitude if math.isfinite(magnitude) else "exceeds finite float range"
            difference["expected_ulp"] = math.ulp(expected)
            ulps = magnitude / math.ulp(expected)
            difference["difference_in_expected_ulps"] = ulps if math.isfinite(ulps) else "exceeds finite float range"
        yield difference


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--actual", required=True, type=Path, help="Recomputed analysis directory")
    parser.add_argument("--expected", type=Path, default=ROOT / "case_studies/completion_budget_diagnostic/results")
    args = parser.parse_args()
    report = {
        "python": sys.version, "platform": platform.platform(), "machine": platform.machine(),
        "exact_match": True, "input_error_count": 0, "files": {},
    }
    for name in NAMES:
        loaded = {}
        errors = []
        for side, directory in (("expected", args.expected), ("actual", args.actual)):
            path = directory / name
            try:
                loaded[side] = read_json(path)
            except (OSError, ValueError) as exc:
                errors.append({
                    "side": side, "path": str(path),
                    "kind": type(exc).__name__, "message": str(exc),
                })
        if errors:
            report["files"][name] = {
                "exact_match": False, "status": "error", "errors": errors,
            }
            report["exact_match"] = False
            report["input_error_count"] += len(errors)
            continue
        diffs = list(differences(loaded["expected"], loaded["actual"]))
        report["files"][name] = {
            "exact_match": not diffs, "status": "different" if diffs else "match",
            "difference_count": len(diffs), "differences": diffs[:100],
        }
        report["exact_match"] = report["exact_match"] and not diffs
    print(json.dumps(report, indent=2, allow_nan=False))
    if report["input_error_count"]:
        return 2
    return 0 if report["exact_match"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
