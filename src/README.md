# AION front end — `src/`

## Host language (M1 exit criterion: "chosen and recorded")

The M1 parser is implemented in **Python 3** (developed and tested on CPython
3.14; no third-party dependencies — standard library only). This follows the
recommendation recorded in [`MILESTONES.md`](../MILESTONES.md) M1: Python for
iteration speed, with the AST/IR defined language-agnostically so a later Rust
rewrite is a reimplementation, not a redesign of the semantics.

Determinism note (D9, guide §3.3): the parse path is fully deterministic. There
is no LLM, embedding, network call, or other non-deterministic component
anywhere in `lexer.py`, `parser.py`, or `printer.py`.

## Scope — what this is and is not

This is the **M1** deliverable only: a syntactic front end. It lexes, parses to
an AST, and pretty-prints with a stable `parse → print → re-parse` round-trip.

It deliberately does **not** perform semantic validation. The following are
**M2** and are intentionally absent rather than stubbed (guide §3.4, §8):

- dangling-reference checks (D3),
- policy-conflict detection and role-override resolution (D2/D11),
- rejection of `proof`-class guarantees from the stable core (D5) — at M1 the
  `proof` class *parses* for forward compatibility,
- `TEST` arity / actor-binding checks (D15),
- evaluation of the static guarantee predicates and the `TEST` decision
  procedure (D7).

Status per [`PHILOSOPHY.md`](../PHILOSOPHY.md): the parser is **Implemented**
and, because `tests/test_m1.py` passes, **Tested**. It is **not Verified** (no
defined checking mechanism against formal properties beyond the round-trip) and
**not Proven** (no proof artifact exists in v0.1–M4).

## Layout

```text
src/aion/
├── __init__.py     # public API: parse_text, parse_file, pretty_print, errors
├── errors.py       # AionError / AionLexError / AionSyntaxError (line + column)
├── lexer.py        # GRAMMAR.md §1: tokens with 1-based line/column
├── ast_nodes.py    # GRAMMAR.md §2: structural mirror of the EBNF (no positions)
├── parser.py       # LL(1) recursive descent over the token stream (D9)
├── printer.py      # canonical pretty-printer (round-trip target)
└── __main__.py     # `python -m aion <file.aion> [--print]` dev driver
```

## Running

From the repository root:

```sh
# tests (parse + round-trip over examples/*.aion, negative-syntax, lexer)
python -m unittest discover -s tests -v

# parse a single spec and report round-trip stability
PYTHONPATH=src python -m aion examples/order-service.aion
PYTHONPATH=src python -m aion examples/order-service.aion --print
```

Errors are reported as `line:column: message`, naming the expected construct.
