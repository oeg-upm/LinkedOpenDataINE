#!/usr/bin/env python3
"""
Pre-fix invalid locale-formatted xsd:float/xsd:double literals *before* rdflib parses the RDF.

Works well for Turtle and N-Triples where typed literals appear like:
  "1.312.289"^^xsd:float
  "1.312,289"^^<http://www.w3.org/2001/XMLSchema#double>

Then parses and serializes with rdflib.

Usage:
  python fix_xsd_floats_prefilter.py input.ttl output.ttl --out-format turtle
  python fix_xsd_floats_prefilter.py input.nt output.nt --out-format nt
"""

from __future__ import annotations

import argparse
import re
import math
import struct
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Optional


XSD_NS = "http://www.w3.org/2001/XMLSchema#"
SPECIAL = {"INF", "-INF", "NaN"}

# Matches "lexical"^^xsd:float or "lexical"^^<...#float> (and double)
# Captures:
#  - lexical string content (without the surrounding quotes)
#  - datatype local name: float|double
TYPED_FLOAT_RE = re.compile(
    r'"([^"\\]*(?:\\.[^"\\]*)*)"\s*\^\^\s*(?:xsd:|<%s)(float|double)>' % re.escape(XSD_NS),
    flags=re.IGNORECASE,
)

# Also support ^^<...#float> without requiring the closing > in the regex above for xsd: form
# We'll handle both by using a second regex for prefixed form.
TYPED_FLOAT_PREFIXED_RE = re.compile(
    r'"([^"\\]*(?:\\.[^"\\]*)*)"\s*\^\^\s*xsd:(float|double)\b',
    flags=re.IGNORECASE,
)

NUM_LIKE_RE = re.compile(r"^\s*[+-]?[0-9][0-9.,]*([eE][+-]?[0-9]+)?\s*$")


def normalize_special(s: str) -> Optional[str]:
    t = s.strip()
    u = t.upper()
    if u in {"INF", "+INF", "INFINITY", "+INFINITY"}:
        return "INF"
    if u in {"-INF", "-INFINITY"}:
        return "-INF"
    if u == "NAN":
        return "NaN"
    return None


def guess_separators(core: str) -> tuple[Optional[str], Optional[str]]:
    has_dot = "." in core
    has_comma = "," in core

    if has_dot and has_comma:
        # last separator is likely decimal
        decimal = "." if core.rfind(".") > core.rfind(",") else ","
        thousand = "," if decimal == "." else "."
        return thousand, decimal

    if has_comma and not has_dot:
        if core.count(",") == 1:
            left, right = core.split(",")
            if 1 <= len(right) <= 6:
                return None, ","
        return ",", None

    if has_dot and not has_comma:
        if core.count(".") > 1:
            return ".", None
        left, right = core.split(".")
        if len(right) == 3 and 1 <= len(left) <= 3:
            return ".", None
        return None, "."

    return None, None


def to_canonical_float_lexical(lex: str, as_single_precision: bool) -> Optional[str]:
    # Handle special tokens
    sp = normalize_special(lex)
    if sp is not None:
        return sp

    if not NUM_LIKE_RE.match(lex):
        return None

    # split exponent (don’t touch separators there)
    exp = ""
    m = re.search(r"([eE][+-]?[0-9]+)$", lex.strip())
    core = lex.strip()
    if m:
        exp = m.group(1)
        core = core[: m.start(1)].strip()

    sign = ""
    if core and core[0] in "+-":
        sign, core = core[0], core[1:]

    thousand, decimal = guess_separators(core)

    if thousand:
        core = core.replace(thousand, "")
    if decimal == ",":
        if core.count(",") > 1:
            return None
        core = core.replace(",", ".")

    normalized = (sign + core + exp).strip()

    try:
        dec = Decimal(normalized)
    except InvalidOperation:
        return None

    f = float(dec)

    if math.isnan(f):
        return "NaN"
    if math.isinf(f):
        return "INF" if f > 0 else "-INF"

    if as_single_precision:
        f = struct.unpack("!f", struct.pack("!f", f))[0]

    out = repr(f)
    if ("e" not in out) and ("E" not in out) and ("." not in out):
        out += ".0"
    return out


def replace_typed_literals(text: str) -> tuple[str, int]:
    changed = 0

    def _repl(match: re.Match) -> str:
        nonlocal changed
        raw_lex = match.group(1)
        dt = match.group(2).lower()

        # Unescape \" etc for parsing, then re-escape for RDF
        # (numeric strings usually have no escapes, but keep it safe)
        unescaped = bytes(raw_lex, "utf-8").decode("unicode_escape")

        fixed = to_canonical_float_lexical(unescaped, as_single_precision=(dt == "float"))
        if fixed is None or fixed == unescaped:
            return match.group(0)

        changed += 1

        # Re-escape back into a Turtle/N-Triples string literal
        escaped_fixed = fixed.replace("\\", "\\\\").replace('"', '\\"')
        # Reconstruct keeping the original datatype syntax as much as possible:
        # If it was prefixed (xsd:float), keep it; if it was IRI, keep it.
        original = match.group(0)
        if "^^xsd:" in original.lower():
            return f'"{escaped_fixed}"^^xsd:{dt}'
        else:
            return f'"{escaped_fixed}"^^<{XSD_NS}{dt}>'

    # Apply both patterns: IRI form first, then prefixed form
    text2 = TYPED_FLOAT_RE.sub(_repl, text)
    text3 = TYPED_FLOAT_PREFIXED_RE.sub(_repl, text2)
    return text3, changed


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("input", type=Path)
    ap.add_argument("output", type=Path)
    ap.add_argument("--in-format", default=None, help="rdflib input format (optional)")
    ap.add_argument("--out-format", default="turtle", help="rdflib output format")
    args = ap.parse_args()

    raw = args.input.read_text(encoding="utf-8")
    fixed_text, n = replace_typed_literals(raw)

    # Write a temp fixed file next to output (or you can keep it in memory)
    tmp = args.output.with_suffix(args.output.suffix + ".prefixed.tmp")
    tmp.write_text(fixed_text, encoding="utf-8")

    # Now rdflib can parse safely
    from rdflib import Graph

    g = Graph()
    if args.in_format:
        g.parse(str(tmp), format=args.in_format)
    else:
        g.parse(str(tmp))

    args.output.parent.mkdir(parents=True, exist_ok=True)
    g.serialize(destination=str(args.output), format=args.out_format)

    # Clean up temp file
    try:
        tmp.unlink()
    except OSError:
        pass

    print(f"Pre-fixed {n} xsd:float/xsd:double literal(s).")
    print(f"Wrote: {args.output}")


if __name__ == "__main__":
    main()
