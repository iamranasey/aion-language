# AION toolchain — `src/`

## Host language (M1 exit criterion: "chosen and recorded")

The toolchain is implemented in **Python 3** (developed and tested on CPython
3.14; no third-party dependencies — standard library only). This follows the
recommendation recorded in [`MILESTONES.md`](../MILESTONES.md) M1: Python for
iteration speed, with the AST/IR defined language-agnostically so a later Rust
rewrite is a reimplementation, not a redesign of the semantics.

Determinism note (D9, guide §3.3): the parse **and validate** paths are fully
deterministic. There is no LLM, embedding, network call, or other
non-deterministic component anywhere in `lexer.py`, `parser.py`, `printer.py`,
`semantic.py`, or `validate.py`.

## Scope — what this is and is not

This is the **M1 + M2** deliverable. M1 is the syntactic front end: it lexes,
parses to an AST, and pretty-prints with a stable `parse → print → re-parse`
round-trip. M2 adds the semantic model and static validation — the compiler
"starts saying no":

- dangling-reference checks for every construct that can dangle (D3/D4/D12/D13),
- policy-conflict detection and role-override resolution (D2/D11),
- rejection of `proof`-class guarantees from the stable core (D5) — the `proof`
  class still *parses* for forward compatibility, but validation rejects it with
  an explicit "unsupported" diagnostic,
- `TEST` arity / actor-binding / argument-compatibility checks (D15),
- evaluation of the five static guarantee atoms (D14) and the `TEST` decision
  procedure (D7).

Validation *collects* every applicable diagnostic rather than failing on the
first, so a negative spec surfaces all of its independent defects
(`examples/README.md`). Because the AST is deliberately position-free (for the M1
round-trip), a semantic diagnostic locates its subject by declaration name
(`RULE BrokenPolicy`) rather than by line/column.

Not present (later milestones, intentionally absent rather than stubbed — guide
§3.4, §8): the M3 IR and lowering, and any M4 code-generation target.

Status per [`PHILOSOPHY.md`](../PHILOSOPHY.md): the M1 parser and the M2
validator are **Implemented** and, because `tests/test_m1.py` and
`tests/test_m2.py` pass, **Tested**. They are **not Verified** (no defined
checking mechanism against formal properties beyond the round-trip and the
conformance suite) and **not Proven** (no proof artifact exists in v0.1–M4;
`proof`-class guarantees remain unsupported).

## Layout

```text
src/aion/
├── __init__.py     # public API: parse/validate entry points, errors, model
├── errors.py       # AionError / AionLexError / AionSyntaxError (line + column)
├── lexer.py        # GRAMMAR.md §1: tokens with 1-based line/column
├── ast_nodes.py    # GRAMMAR.md §2: structural mirror of the EBNF (no positions)
├── parser.py       # LL(1) recursive descent over the token stream (D9)
├── printer.py      # canonical pretty-printer (round-trip target)
├── diagnostics.py  # M2: Diagnostic (position-free) + AionSemanticError
├── semantic.py     # M2: symbol tables, decide() (D7/D11), guarantee atoms (D14)
├── validate.py     # M2: collects every semantic diagnostic for a spec
└── __main__.py     # `python -m aion <file.aion> [--print] [--no-validate]`
```

## Running

From the repository root:

```sh
# tests (M1 parse + round-trip, M2 validation + decision procedure)
python -m unittest discover -s tests -v

# parse + validate a single spec; exit 0 clean, 1 on any error
PYTHONPATH=src python -m aion examples/order-service.aion
PYTHONPATH=src python -m aion examples/order-service.aion --print

# a negative spec reports each diagnostic and exits 1
PYTHONPATH=src python -m aion examples/negative-dangling-reference.aion

# front-end debugging: parse + round-trip only, skip semantic validation
PYTHONPATH=src python -m aion examples/order-service.aion --no-validate
```

Lexical/syntax errors are reported as `line:column: message`, naming the
expected construct. Semantic errors are reported as
`<locator>: [code] message` (e.g. `RULE BrokenPolicy: [dangling-action] …`).
