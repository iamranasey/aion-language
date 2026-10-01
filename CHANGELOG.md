# Changelog

## Unreleased — 0.1.0.dev0

- Package the existing M1 front end with the `aion` console command.
- Add source-range metadata through `parse_with_locations`, without changing
  structural AST equality or language syntax.
- Add diagnostic error families, controlled file/encoding failures, and processing
  limit reporting. Unknown CLI options now fail with exit code 2 instead of being
  silently ignored. CLI lexical/syntax errors now include an error code.
- Add bounded generated conformance checks, documented-example checks, source-range
  tests, and a configured Python 3.10–3.14 CI matrix across three operating systems.
- Clarify assurance claims, security scope, and release/conformance procedures.
- Adopt M2 semantic decisions D16–D20; no semantic validator or TEST
  evaluator is included. There is no published release or certification claim.
