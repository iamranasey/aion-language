"""Minimal M1 driver: parse an AION file and report the round-trip result.

Usage:
    python -m aion <file.aion> [--print]

Exits 0 on a clean parse and stable round-trip, 1 on any lexical or syntax
error (printed as `path:line:column: code: message`). This is a developer convenience for
M1; it performs no semantic validation (that is M2).
"""

from __future__ import annotations

import argparse
import sys

from .errors import AionError
from .parser import parse_text
from .printer import pretty_print


def main(argv: list[str] | None = None) -> int:
    cli = argparse.ArgumentParser(
        description="Parse AION and check AST round-trip stability; no semantic validation."
    )
    cli.add_argument("file", help="UTF-8 AION source file")
    cli.add_argument("--print", action="store_true", dest="do_print", help="emit canonical source")
    args = cli.parse_args(argv)
    path = args.file
    try:
        with open(path, "r", encoding="utf-8") as handle:
            source = handle.read()
    except (OSError, UnicodeError) as err:
        print(f"{path}: AION1003: {err}", file=sys.stderr)
        return 1

    try:
        spec = parse_text(source)
        printed = pretty_print(spec)
        reparsed = parse_text(printed)
    except AionError as err:
        print(f"{path}:{err.line}:{err.column}: {err.code}: {err.message}", file=sys.stderr)
        return 1
    except (RecursionError, ValueError) as err:
        print(f"{path}: AION1004: input exceeds processing limits ({type(err).__name__})", file=sys.stderr)
        return 1

    if reparsed != spec:
        print(f"{path}: round-trip unstable (re-parsed AST differs)", file=sys.stderr)
        return 1

    if args.do_print:
        print(printed, end="")
    else:
        print(f"{path}: parsed OK; round-trip stable "
              f"({len(spec.declarations)} declarations)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
