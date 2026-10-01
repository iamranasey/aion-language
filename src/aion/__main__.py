"""Parse, round-trip, and validate AION. --no-validate selects syntax only."""

from __future__ import annotations

import argparse
import sys

from .errors import AionError
from .parser import parse_text, parse_with_locations
from .validate import validate
from .printer import pretty_print


def main(argv: list[str] | None = None) -> int:
    cli = argparse.ArgumentParser(
        description="Parse, round-trip, and statically validate AION (M2)."
    )
    cli.add_argument("file", help="UTF-8 AION source file")
    cli.add_argument("--print", action="store_true", dest="do_print", help="emit canonical source")
    cli.add_argument("--no-validate", action="store_true", help="skip M2 semantic checks")
    args = cli.parse_args(argv)
    path = args.file
    try:
        with open(path, "r", encoding="utf-8") as handle:
            source = handle.read()
    except (OSError, UnicodeError) as err:
        print(f"{path}: AION1003: {err}", file=sys.stderr)
        return 1

    try:
        parsed = parse_with_locations(source)
        spec = parsed.spec
        printed = pretty_print(spec)
        reparsed = parse_text(printed)
        diagnostics = [] if args.no_validate else validate(parsed)
    except AionError as err:
        print(f"{path}:{err.line}:{err.column}: {err.code}: {err.message}", file=sys.stderr)
        return 1
    except (RecursionError, ValueError) as err:
        print(f"{path}: AION1004: input exceeds processing limits ({type(err).__name__})", file=sys.stderr)
        return 1

    if reparsed != spec:
        print(f"{path}: round-trip unstable (re-parsed AST differs)", file=sys.stderr)
        return 1

    if diagnostics:
        for diagnostic in diagnostics:
            span = diagnostic.span
            location = f"{path}:{span.line}:{span.column}" if span else path
            print(f"{location}: {diagnostic.where}: [{diagnostic.code}] {diagnostic.message}", file=sys.stderr)
        print(f"{path}: {len(diagnostics)} semantic error(s)", file=sys.stderr)
        return 1

    if args.do_print:
        print(printed, end="")
    else:
        checked = "validation skipped" if args.no_validate else "validated"
        print(f"{path}: parsed OK; round-trip stable; {checked} "
              f"({len(spec.declarations)} declarations)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
