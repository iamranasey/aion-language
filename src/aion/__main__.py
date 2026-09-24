"""Minimal M1 driver: parse an AION file and report the round-trip result.

Usage:
    python -m aion <file.aion> [--print]

Exits 0 on a clean parse and stable round-trip, 1 on any lexical or syntax
error (printed as `line:column: message`). This is a developer convenience for
M1; it performs no semantic validation (that is M2).
"""

from __future__ import annotations

import sys

from .errors import AionError
from .parser import parse_text
from .printer import pretty_print


def main(argv: list[str]) -> int:
    args = [a for a in argv if not a.startswith("--")]
    do_print = "--print" in argv
    if len(args) != 1:
        print("usage: python -m aion <file.aion> [--print]", file=sys.stderr)
        return 2

    path = args[0]
    with open(path, "r", encoding="utf-8") as handle:
        source = handle.read()

    try:
        spec = parse_text(source)
        printed = pretty_print(spec)
        reparsed = parse_text(printed)
    except AionError as err:
        print(f"{path}:{err.line}:{err.column}: {err.message}", file=sys.stderr)
        return 1

    if reparsed != spec:
        print(f"{path}: round-trip unstable (re-parsed AST differs)", file=sys.stderr)
        return 1

    if do_print:
        print(printed, end="")
    else:
        print(f"{path}: parsed OK; round-trip stable "
              f"({len(spec.declarations)} declarations)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
