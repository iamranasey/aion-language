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
- Implement the adopted M2 semantic decisions D16–D20: global conflicts, all
  declaration namespaces, strict comparison types, and TEST binding checks.
- Validate by default in the CLI; `--no-validate` retains parse-only behavior.
- Add semantic diagnostic codes and optional declaration source ranges, a
  validated-model factory, and published conformance vectors.
- No runtime state enforcement, published release, or certification is claimed.
- Correct post-merge documentation drift: the `CONFLICT_FREE` atom row now cites
  D17's global scope, the milestone position records M2 as merged rather than
  pending review, and `SECURITY.md` states the D16/D17 semantics that change what
  a policy means. Documentation only — no grammar, validator, or CLI change.
