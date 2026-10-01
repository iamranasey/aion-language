# AION front end and M2 validator

Python 3, standard-library runtime only. Python 3.10–3.14 is the configured CI
range; local tests run on CPython 3.12. Parsing and validation are deterministic
and contain no LLM or network calls (D9).

## Implemented scope

M1 provides lexer, parser, structural AST, and canonical pretty-printer. M2 adds
all declaration namespaces (D18), forward reference resolution, dangling-reference
checks, global conflicts and specificity (D16/D17), five static guarantee atoms,
proof rejection, comparison typing and TEST bindings (D19), and TEST evaluation.
D20 limits state checks to references/types. Monitor instrumentation, runtime state,
IR, code generation, and proof backends are not implemented.

M1 and M2 are **Implemented** and **Tested**, not **Verified** or **Proven**.

## API

- `parse_text(text)` and `parse_file(path)` return structural ASTs.
- `parse_with_locations(text)` returns ParsedSource with `.spec` and `.span_for(node)`.
- `pretty_print(spec)` produces canonical source.
- `validate(spec_or_parsed_source)` returns all diagnostics in deterministic pass order.
- `validate_or_raise(...)` raises AionSemanticError with the diagnostic list.
- `build_validated_model(...)` rejects validation errors and returns SemanticModel.
- `SemanticModel.build(spec)` is low-level construction returning `(model, duplicates)`;
  it does not validate. Its `symbols` maps every declaration namespace. `decide`
  analyzes a declared subject/action; it is not a security boundary. Revalidate
  after mutations. TEST checks are performed by validate.

Diagnostics have `code`, `where`, `message`, and optional `span`. Passing ParsedSource
attaches declaration ranges where names are unambiguous. Duplicate declaration
locators retain no span rather than inventing a source location. Ranges have one-based
start coordinates and exclusive ends; metadata does not affect AST equality.
Predicate atoms use their enclosing term range in the parser source map.

## Modules

`lexer.py`, `parser.py`, `ast_nodes.py`, and `printer.py` implement M1.
`source_map.py` retains optional ranges; `errors.py` holds front-end exceptions.
`semantic.py` builds symbols/policy graph and evaluates predicates/decisions.
`validate.py` checks references/types/guarantees/tests; `diagnostics.py` defines
semantic diagnostic records. `__main__.py` provides the installed CLI.

## Running

```sh
python -m pip install .
aion examples/order-service.aion
aion examples/order-service.aion --print
aion examples/negative-dangling-reference.aion --no-validate
python -m unittest discover -s tests -v
```

Validation is on by default. Exit 0 means no diagnostics, exit 1 input/semantic
failure, exit 2 usage error. Front-end codes AION1001–AION1004 and semantic codes
are documented in docs/RELEASING.md and diagnostics.py. Semantic errors with source
locations print `path:line:column: DECLARATION name: [code] message`.
