"""AION driver: parse, round-trip, and (M2) statically validate an AION file.

Usage:
    python -m aion <file.aion> [--print] [--no-validate]

Exits:
    0  clean parse, stable round-trip, and (unless --no-validate) no semantic
       diagnostics;
    1  a lexical/syntax error (printed as `path:line:column: message`) or a
       semantic error (printed as `path: <locator>: [code] message`);
    2  bad usage.

M1 performed only the parse + round-trip check. M2 adds static validation
(``aion.validate``): dangling references (D3), policy conflicts (D2/D11),
guarantee evaluation (D5/D14), and the D7 ``TEST`` interpreter. ``--no-validate``
restores the M1 parse-only behaviour for front-end debugging.
"""

from __future__ import annotations

import sys

from .errors import AionError
from .parser import parse_text
from .printer import pretty_print
from .validate import validate


def main(argv: list[str]) -> int:
    flags = {a for a in argv if a.startswith("--")}
    args = [a for a in argv if not a.startswith("--")]
    do_print = "--print" in flags
    do_validate = "--no-validate" not in flags
    unknown = flags - {"--print", "--no-validate"}
    if len(args) != 1 or unknown:
        print("usage: python -m aion <file.aion> [--print] [--no-validate]",
              file=sys.stderr)
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

    if do_validate:
        diagnostics = validate(spec)
        if diagnostics:
            for diag in diagnostics:
                print(f"{path}: {diag.where}: [{diag.code}] {diag.message}",
                      file=sys.stderr)
            print(f"{path}: {len(diagnostics)} semantic error(s)", file=sys.stderr)
            return 1

    if do_print:
        print(printed, end="")
    else:
        checked = "validated" if do_validate else "validation skipped"
        print(f"{path}: parsed OK; round-trip stable; {checked} "
              f"({len(spec.declarations)} declarations)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
