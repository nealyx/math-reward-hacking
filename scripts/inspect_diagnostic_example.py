"""Inspect one verified saved diagnostic example; no model loading or inference.

Uses the public package's existing verifier before displaying recorded scores.
Requires Python 3.10+ and the standard library only.
"""
from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path
import re
import sys


PACKAGE = Path(__file__).resolve().parents[1] / "case_studies" / "completion_budget_diagnostic"


def load_verifier():
    spec = importlib.util.spec_from_file_location(
        "diagnostic_public_reproduce", PACKAGE / "reproduce.py"
    )
    if spec is None or spec.loader is None:
        raise ImportError("Cannot load the public saved-output verifier")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def problem_id(value):
    number = int(value)
    if not 0 <= number < 500:
        raise argparse.ArgumentTypeError("problem ID must be between 0 and 499")
    return number


def render_example(index, model, example, caps, include_response=False):
    """Render already verified records without rescoring or selecting a winner."""
    rows = [index[model, cap, example] for cap in caps]
    first = rows[0]
    lines = [
        f"# Saved example: {model}, problem {example}",
        "",
        f"Problem: {first['a']} × {first['b']} + {first['c']}",
        f"Target: {first['ground_truth']}",
        "",
        "| Completion limit | Policy | Extracted integer | Exact correct | Modulo correct | Proxy-only correct |",
        "|---:|---|---:|---:|---:|---:|",
    ]
    for row in rows:
        for policy in ("legacy", "terminal", "declared"):
            score = row["scores"][policy]
            value = "none" if score["value"] is None else str(score["value"])
            flags = [
                str(int(score[key]))
                for key in ("exact_correct", "mod10_correct", "proxy_only_correct")
            ]
            lines.append(
                f"| {row['max_new_tokens']} | {policy} | {value} | {' | '.join(flags)} |"
            )
    lines += [
        "",
        "1 = credited; 0 = not credited. Proxy-only means modulo-correct and exact-incorrect.",
        "A missing answer receives no credit. Policies read the same saved completion.",
        "",
        "| Completion limit | Generated tokens | Recorded stopping reason |",
        "|---:|---:|---|",
    ]
    for row in rows:
        lines.append(
            f"| {row['max_new_tokens']} | {row['generated_token_count']} | {row['stopping_reason']} |"
        )
    if include_response:
        for row in rows:
            response = row["raw_completion"]
            longest = max((len(m.group()) for m in re.finditer(r"`+", response)), default=0)
            fence = "`" * max(3, longest + 1)
            lines += [
                "",
                f"## Saved raw completion at limit {row['max_new_tokens']}",
                "",
                fence + "text",
                response,
                fence,
            ]
    lines += [
        "",
        "The full public package was verified before display; no model weights were loaded.",
        "This example illustrates scoring behavior, not its frequency or a training effect.",
    ]
    return "\n".join(lines)


def main(argv=None):
    verifier = load_verifier()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", choices=verifier.MODELS, default="proxy_202")
    parser.add_argument("--problem-id", type=problem_id, default=0)
    parser.add_argument(
        "--cap", type=int, choices=verifier.CAPS, action="append",
        help="Display one limit; repeat for multiple limits (default: all three)",
    )
    parser.add_argument("--response", action="store_true", help="Include complete saved raw response text")
    args = parser.parse_args(argv)
    caps = tuple(dict.fromkeys(args.cap)) if args.cap else verifier.CAPS
    try:
        _, index, _ = verifier.verify(PACKAGE)
        print(render_example(index, args.model, args.problem_id, caps, args.response))
    except (ValueError, KeyError, TypeError, IndexError, OSError, ImportError) as exc:
        print(f"Inspection failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
