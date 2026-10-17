"""Target-independent, conservative terminal-integer extraction.

This module uses only the Python standard library.  It never evaluates a
response as code or judges whether an extracted integer is arithmetically true.
See extractor_spec.md for the grammar, ambiguity rules and limitations.
"""

from __future__ import annotations

import re


VERSION = "terminal-integer-1.0.0"
INTEGER = re.compile(r"[+-]?(?:[0-9]{1,3}(?:,[0-9]{3})+|[0-9]+)\Z", re.ASCII)
LABEL = r"(?:final\s+answer|answer)"
SEPARATOR = r"(?P<separator>:|=+|is\b)"
LABEL_PATTERNS = [
    re.compile(rf"{LABEL}\s*{SEPARATOR}\s*", re.IGNORECASE | re.ASCII),
    re.compile(rf"(?P<em>\*\*|__|\*|_){LABEL}(?P=em)\s*{SEPARATOR}\s*", re.IGNORECASE | re.ASCII),
    re.compile(rf"(?P<em>\*\*|__|\*|_){LABEL}\s*{SEPARATOR}(?P=em)\s*", re.IGNORECASE | re.ASCII),
]
NATURAL = re.compile(
    r"the\s+(?:(?:exact|final)\s+)?(?:answer|result|value)"
    r"(?:\s+(?:of|for)\s+(?:(?!\bis\b)[^\r\n:;!?]){1,240}?)?\s+is\s+",
    re.IGNORECASE | re.ASCII,
)
CONNECTOR = re.compile(
    r"(?:therefore|thus|hence|so|consequently|finally)\s*[,;:]?\s+",
    re.IGNORECASE | re.ASCII,
)
BRIDGE = re.compile(
    r"[\s,;]*(?:and|or|but|actually|therefore|thus|hence|so|finally|correction)"
    r"\s*[,;:]?\s*\Z", re.IGNORECASE | re.ASCII,
)
EXPLICIT_ANCHOR = re.compile(
    rf"(?<![\w]){LABEL}(?:(?:\*\*|__|\*|_))?\s*(?::|=+|is\b)",
    re.IGNORECASE | re.ASCII,
)
NATURAL_ANCHOR = re.compile(
    r"(?<![\w])the\s+(?:(?:exact|final)\s+)?(?:answer|result|value)\b",
    re.IGNORECASE | re.ASCII,
)
BOX_ANCHOR = re.compile(r"\\boxed\s*\{")
WRAPPERS = (
    (r"\(", r"\)"), (r"\[", r"\]"), ("$$", "$$"),
    ("**", "**"), ("__", "__"), ("$", "$"),
    ("*", "*"), ("_", "_"), ("`", "`"), ("(", ")"),
)


def legacy_parse(text):
    """Unchanged function body from ../audit.py (historical policy)."""
    matches = re.findall(r"(?i)(?:final\s*answer|answer)\s*(?::|={1,})\s*([+-]?\d+)", text)
    if matches:
        return matches[-1].strip(), "final_answer"
    matches = list(re.finditer(r"\\boxed{([+-]?\d+)}|x\s*=\s*([+-]?\d+)", text))
    if matches:
        m = matches[-1]
        return (m[1].strip(), "boxed") if m[1] else (m[2].strip(), "variable_assignment")
    matches = re.findall(r"(?<![\w.])([+-]?\d+)(?!\w)(?!\.\d)", text)
    return (matches[-1].strip(), "last_integer") if matches else (None, "unparseable")


def _trim(text, start, end):
    while start < end and text[start].isspace():
        start += 1
    while start < end and text[end - 1].isspace():
        end -= 1
    return start, end


def _clause_boundary(text, start):
    before = text[:start].rstrip(" \t\r")
    if not before or before[-1] in "\n.!?;":
        return True
    possible_connector = re.search(
        r"(?:therefore|thus|hence|so|consequently|finally)\s*[,;:]?\s*\Z",
        before, re.IGNORECASE | re.ASCII)
    if possible_connector:
        earlier = before[:possible_connector.start()].rstrip(" \t\r")
        return not earlier or earlier[-1] in "\n.!?;"
    return False


def _unwrap(text, start, end):
    """Strip balanced complete wrappers, preserving original offsets."""
    box = False
    punctuation = 0
    for _ in range(16):
        start, end = _trim(text, start, end)
        if start < end and text[end - 1] in ".!":
            punctuation += 1
            if punctuation > 1:
                return start, end, box, False
            end -= 1
            continue
        if text.startswith(r"\boxed", start):
            opener = BOX_ANCHOR.match(text, start, end)
            if opener and start < end and text[end - 1] == "}":
                start, end, box = opener.end(), end - 1, True
                continue
        found = False
        for left, right in WRAPPERS:
            if end - start >= len(left) + len(right) and text.startswith(left, start) and text.endswith(right, start, end):
                start, end = start + len(left), end - len(right)
                found = True
                break
        if not found:
            return start, end, box, True
    return start, end, box, False


def _unit(text, start, end, standalone, bridge=False):
    """Parse one whole suffix unit. No last-number fallback is used."""
    original_start = start
    if bridge:
        # Connectors may join two answer units; they are never stripped at EOF.
        match = BRIDGE.search(text, start, end)
        if match:
            end = match.start()
    start, end, box, balanced = _unwrap(text, start, end)
    if not balanced:
        if EXPLICIT_ANCHOR.search(text, original_start, end) or BOX_ANCHOR.search(text, original_start, end):
            return {"value": None, "method": "final_declaration", "span": None,
                    "strict": False, "declaration": True,
                    "start": original_start, "malformed": True}
        return None
    connector = CONNECTOR.match(text, start, end)
    if connector:
        start = connector.end()
    kind = "terminal_box" if box else "standalone_terminal_line"
    declaration = box
    strict = box
    prefix = None
    for pattern in LABEL_PATTERNS:
        prefix = pattern.match(text, start, end)
        if prefix:
            if prefix["separator"].lower() == "is" and not _clause_boundary(text, original_start):
                return None
            kind, declaration = "final_declaration", True
            strict = strict or prefix["separator"] == ":"
            break
    if prefix is None:
        prefix = NATURAL.match(text, start, end)
        if prefix:
            # Never turn a negated/conditional/quoted prose fragment into a
            # final conclusion merely by starting at its embedded "the".
            if not _clause_boundary(text, original_start):
                return None
            kind = "natural_language_conclusion"
    if prefix:
        start = prefix.end()
        start, end, inner_box, balanced = _unwrap(text, start, end)
        box = box or inner_box
        declaration = declaration or box
        strict = strict or box
        if kind == "final_declaration":
            # One explicit label may introduce exactly one supported natural
            # conclusion. This is composition, not arbitrary prose salvage.
            conclusion = NATURAL.match(text, start, end)
            if conclusion:
                start = conclusion.end()
                start, end, inner_box, balanced = _unwrap(text, start, end)
                box = box or inner_box
                declaration = declaration or box
                strict = strict or box
    elif not box and not standalone:
        return None
    literal = text[start:end]
    if balanced and INTEGER.fullmatch(literal):
        return {"value": int(literal.replace(",", "")), "method": kind,
                "span": [start, end], "strict": strict, "declaration": declaration,
                "start": original_start, "malformed": False}
    if prefix is not None or box:
        # In an earlier unit, prose is a block boundary rather than part of a
        # sequence of declarations. Numeric syntax errors remain in the block.
        simple_payload = not re.search(r"[A-DF-Za-df-z]", literal)
        if not bridge or simple_payload:
            return {"value": None, "method": kind, "span": None, "strict": strict,
                    "declaration": declaration, "start": original_start, "malformed": True}
    return None


def _candidate_starts(text):
    line_starts = {0}
    line_starts.update(match.end() for match in re.finditer(r"\n", text))
    starts = set(line_starts)
    for pattern in (EXPLICIT_ANCHOR, NATURAL_ANCHOR, BOX_ANCHOR):
        for match in pattern.finditer(text):
            starts.add(match.start())
            left = match.start()
            # Include whole-clause wrappers immediately before a marker.
            while left:
                original = left
                while left and text[left - 1] in " \t":
                    left -= 1
                for opener, _ in WRAPPERS:
                    if text[:left].endswith(opener):
                        left -= len(opener)
                        starts.add(left)
                        break
                if left == original or not any(text[:original].rstrip().endswith(opener) for opener, _ in WRAPPERS):
                    break
    return sorted(starts), line_starts


def _result(status, declaration_present, value=None, method=None, span=None, candidates=None):
    return {"value": value, "method": method, "span": span,
            "declaration_present": declaration_present, "parse_status": status,
            "terminal_candidates": candidates or []}


def extract_terminal(text, declared_only=False, *, generation_error=False):
    """Extract a complete integer terminal answer; return JSON-safe evidence.

    Character spans are half-open indices into the supplied readable completion.
    Special generation tokens must be removed by the tokenizer's readable decode,
    not heuristically stripped here. The raw special-preserving decode is stored
    independently by the inference runner.
    """
    if not isinstance(text, str):
        raise TypeError("text must be str")
    declaration_present = bool(EXPLICIT_ANCHOR.search(text) or BOX_ANCHOR.search(text))
    if generation_error:
        return _result("generation_error", declaration_present)
    starts, line_starts = _candidate_starts(text)
    units = [_unit(text, start, len(text), start in line_starts) for start in starts]
    valid = [unit for unit in units if unit is not None and not unit["malformed"]]
    if valid:
        last = min(valid, key=lambda unit: unit["start"])
        chain = [last]
        edge = last["start"]
        while edge > 0:
            previous = [_unit(text, start, edge, start in line_starts, bridge=True)
                        for start in starts if start < edge]
            previous = [unit for unit in previous if unit is not None]
            if not previous:
                break
            # Prefer the nearest unit, then allow a preceding unit to extend it.
            earlier = max(previous, key=lambda unit: unit["start"])
            chain.insert(0, earlier)
            edge = earlier["start"]
        candidates = [{key: unit[key] for key in ("value", "method", "span")}
                      for unit in chain]
        values = {unit["value"] for unit in chain if not unit["malformed"]}
        if len(values) > 1:
            return _result("conflicting_terminal_declarations", declaration_present, candidates=candidates)
        if any(unit["malformed"] for unit in chain):
            return _result("malformed_terminal_declaration", declaration_present, candidates=candidates)
        if declared_only and not last["strict"]:
            status = "missing_terminal_answer" if re.search(r"[0-9]", text) else "no_numeric_content"
            return _result(status, declaration_present, candidates=candidates)
        return _result("accepted_terminal_answer", declaration_present, last["value"],
                       last["method"], last["span"], candidates)
    if any(unit is not None and unit["malformed"] for unit in units):
        return _result("malformed_terminal_declaration", declaration_present)
    status = "missing_terminal_answer" if re.search(r"[0-9]", text) else "no_numeric_content"
    return _result(status, declaration_present)


def extract_legacy(text, *, generation_error=False):
    """Add evidence to the unchanged legacy decision, without repairing it."""
    declaration = bool(EXPLICIT_ANCHOR.search(text) or BOX_ANCHOR.search(text))
    if generation_error:
        return _result("generation_error", declaration)
    value, method = legacy_parse(text)
    span = None
    if value is not None:
        if method == "final_answer":
            match = list(re.finditer(r"(?i)(?:final\s*answer|answer)\s*(?::|={1,})\s*([+-]?\d+)", text))[-1]
            span = list(match.span(1))
        elif method in ("boxed", "variable_assignment"):
            match = list(re.finditer(r"\\boxed{([+-]?\d+)}|x\s*=\s*([+-]?\d+)", text))[-1]
            span = list(match.span(1 if match[1] else 2))
        else:
            match = list(re.finditer(r"(?<![\w.])([+-]?\d+)(?!\w)(?!\.\d)", text))[-1]
            span = list(match.span(1))
    return _result("accepted_legacy_answer" if value is not None else (
        "missing_terminal_answer" if re.search(r"[0-9]", text) else "no_numeric_content"),
        declaration, int(value) if value is not None else None, method, span)
