#!/usr/bin/env python3
"""
Fix locale-formatted xsd:float / xsd:double literals in RDF files.

What it does
------------
- Scans RDF data (Turtle/N-Triples/RDF/XML/JSON-LD via rdflib).
- Finds literals with datatype xsd:float or xsd:double.
- Rewrites invalid/locale formatted lexical forms into canonical forms:
  - Thousand separators: "1.312.289" -> "1312289.0"
  - European decimals:   "1.312,289" -> "1312.289"
  - US decimals w/ commas: "1,312,289.5" -> "1312289.5"
  - Handles INF, -INF, NaN (kept as-is but normalized to XML Schema tokens)
- Writes a new RDF file, preserving the original graph structure.

Usage
-----
python float_parsing_script.py input.ttl output.ttl --format turtle

Notes
-----
- This focuses on xsd:float and xsd:double (you can extend to xsd:decimal).
- For xsd:float, values are rounded to IEEE-754 single precision by packing/unpacking.
  (This makes the lexical form match the *actual* float value.)
"""

from __future__ import annotations

import argparse
import math
import re
import struct
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Optional, Tuple

from rdflib import Graph, Literal
from rdflib.namespace import XSD


SPECIAL_TOKENS = {"INF", "-INF", "NaN"}

# Matches common "number-like" strings incl. separators, exponent, sign, whitespace
NUM_LIKE_RE = re.compile(r"^\s*[+-]?[0-9][0-9.,]*([eE][+-]?[0-9]+)?\s*$")


def normalize_special(s: str) -> Optional[str]:
    """Return XML Schema special tokens if s represents them, else None."""
    t = s.strip()
    t_upper = t.upper()
    if t_upper in {"INF", "+INF", "INFINITY", "+INFINITY"}:
        return "INF"
    if t_upper in {"-INF", "-INFINITY"}:
        return "-INF"
    if t_upper == "NAN":
        return "NaN"
    return None


def guess_separators(core: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Guess thousand and decimal separators in a numeric string core.
    Returns (thousand_sep, decimal_sep).
    """
    has_dot = "." in core
    has_comma = "," in core

    if has_dot and has_comma:
        # The last occurring separator is usually the decimal separator.
        last_dot = core.rfind(".")
        last_comma = core.rfind(",")
        decimal_sep = "." if last_dot > last_comma else ","
        thousand_sep = "," if decimal_sep == "." else "."
        return thousand_sep, decimal_sep

    if has_comma and not has_dot:
        # If exactly one comma and 1-2 digits after it => decimal comma.
        if core.count(",") == 1:
            left, right = core.split(",")
            if 1 <= len(right) <= 6:  # be tolerant
                return None, ","
        # Otherwise treat commas as thousands separators.
        return ",", None

    if has_dot and not has_comma:
        # If multiple dots: likely thousands separators (e.g., 1.312.289).
        if core.count(".") > 1:
            return ".", None
        # One dot: could be decimal or thousands. Heuristic:
        left, right = core.split(".")
        # If exactly 3 digits after and left length 1-3 => often thousands sep (e.g., 1.234).
        if len(right) == 3 and 1 <= len(left) <= 3:
            return ".", None
        return None, "."

    return None, None


def to_canonical_float_lexical(s: str, as_single_precision: bool) -> Optional[str]:
    """
    Convert a possibly-locale-formatted numeric string to canonical lexical for float/double.
    Returns the canonical string, or None if cannot parse.
    """
    s = s.strip()

    # Handle special values
    sp = normalize_special(s)
    if sp is not None:
        return sp

    if not NUM_LIKE_RE.match(s):
        return None

    # Split exponent if present to avoid touching separators there
    exp_part = ""
    core = s
    m = re.search(r"([eE][+-]?[0-9]+)$", s)
    if m:
        exp_part = m.group(1)
        core = s[: m.start(1)]

    core = core.strip()
    sign = ""
    if core and core[0] in "+-":
        sign, core = core[0], core[1:]

    thousand_sep, decimal_sep = guess_separators(core)

    # Remove thousands separators
    if thousand_sep:
        core = core.replace(thousand_sep, "")

    # Normalize decimal separator to dot
    if decimal_sep == ",":
        if core.count(",") > 1:
            return None
        core = core.replace(",", ".")
    else:
        # If decimal_sep is None, remove any stray commas (e.g., "1312,289" ambiguous)
        # but ONLY if we already decided commas are thousands separators
        pass

    normalized = (sign + core + exp_part).strip()

    # Parse using Decimal first for robustness, then convert to float
    try:
        dec = Decimal(normalized)
    except InvalidOperation:
        return None

    # Convert to python float (double)
    f = float(dec)

    if math.isnan(f):
        return "NaN"
    if math.isinf(f):
        return "INF" if f > 0 else "-INF"

    if as_single_precision:
        # Round to IEEE-754 binary32 by packing/unpacking
        f = struct.unpack("!f", struct.pack("!f", f))[0]

    # Canonical lexical for xsd:float/double is a decimal string in scientific notation
    # is allowed, but we emit a plain/exp form via Python's repr which is round-trippable.
    # Ensure there's a decimal point to keep it clearly float-y (optional but common).
    out = repr(f)
    if ("e" not in out) and ("E" not in out) and ("." not in out):
        out = out + ".0"
    return out


def fix_graph(g: Graph) -> int:
    """
    Fix float/double literals in graph in-place.
    Returns the number of literals changed.
    """
    changes = 0
    triples_to_update = []

    for s, p, o in g:
        if isinstance(o, Literal) and o.datatype in (XSD.float, XSD.double):
            lex = str(o)
            as_single = (o.datatype == XSD.float)
            fixed = to_canonical_float_lexical(lex, as_single_precision=as_single)
            if fixed is None:
                continue
            if fixed != lex:
                new_lit = Literal(fixed, datatype=o.datatype)
                triples_to_update.append((s, p, o, new_lit))

    for s, p, old_o, new_o in triples_to_update:
        g.remove((s, p, old_o))
        g.add((s, p, new_o))
        changes += 1

    return changes


def main() -> None:
    parser = argparse.ArgumentParser(description="Fix invalid locale-formatted xsd:float/xsd:double literals in RDF.")
    parser.add_argument("input", type=Path, help="Input RDF file")
    parser.add_argument("output", type=Path, help="Output RDF file")
    parser.add_argument("--in-format", default=None,
                        help="Input format (e.g., turtle, nt, xml, json-ld). If omitted, rdflib guesses from extension.")
    parser.add_argument("--out-format", default="turtle",
                        help="Output format (default: turtle). Examples: turtle, nt, xml, json-ld.")
    args = parser.parse_args()

    g = Graph()

    # rdflib guesses format from file extension if not provided
    if args.in_format:
        g.parse(str(args.input), format=args.in_format)
    else:
        g.parse(str(args.input))

    changed = fix_graph(g)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    g.serialize(destination=str(args.output), format=args.out_format)

    print(f"Done. Updated {changed} literal(s).")
    print(f"Written: {args.output}")


if __name__ == "__main__":
    main()
