# Conformance and evidence

The normative language sources are SPEC and the GRAMMAR decision log. This file
maps their requirements to evidence; it does not resolve missing semantics.
"Passes conformance" must name the language version, implementation revision,
supported phase, and exact suite. It is not a claim about arbitrary generated code.

| Requirement | Evidence | Current limit |
| --- | --- | --- |
| D9 deterministic parsing; M1 grammar | test_m1.TestConformanceSuiteParses; TestNegativeSyntax | Six seed specs, not exhaustive syntax coverage |
| M1 lexical diagnostics | test_m1.TestLexer | Locations and malformed lexical input |
| M1 structural round trip | test_m1.TestRoundTripCanonicalForms; test_engineering.ConformanceProperties | AST preservation, not semantic correctness |
| SPEC normative example consistency | test_engineering.ConformanceProperties.test_normative_example_structural_equivalence | Comments may differ |
| Diagnostic source ranges | test_engineering.SourceLocations | Source positions excluded from AST equality |
| CLI input failures | test_engineering.CommandLine | File/encoding/options/syntax errors |
| D1–D4, D6–D8, D11–D20 semantic requirements | test_m2; test_m2_decisions; tests/fixtures/m2-conformance.json | Implemented/tested over the declared model, not target execution |
| D5 proof rejection and monitor enforcement | test_m2.TestGuaranteeAtoms | M2 rejects proof; monitor runtime enforcement remains M4 |
| M3 IR preservation; M4 target equivalence | MILESTONES.md | Not implemented |

Run `python -m unittest discover -s tests -v`. Generated property checks use
fixed seeds and bounded inputs, so failures are reproducible without introducing
randomness into the parser. They exercise 150 generated programs and 300 malformed
input candidates. This is bounded fuzz smoke coverage, not a completed security audit.

CI is configured for Python 3.10–3.14 on Linux, Windows, and macOS. Only actual
successful CI runs establish platform evidence; writing the workflow does not.
The workflow builds a wheel, installs it, and invokes the installed CLI separately
from source-tree unit tests.

## Future independent comparison (not yet executed)

### Adopted M2 acceptance expectations

These M2 acceptance expectations are exercised by test_m2_decisions.py and the
published tests/fixtures/m2-conformance.json vectors. They are semantic checks,
not M1 parsing assertions.

| Case | Required outcome | Decision |
| --- | --- | --- |
| Bare DENY plus role ALLOW | Role request allowed; bare request denied | D16 |
| Bare ALLOW plus role DENY | Role request denied; bare request allowed | D16 |
| No matching policy edge | Denied | D16 |
| Exact ALLOW/DENY pair split across RULEs, with no TEST | Compile error | D17 |
| Reorder RULEs or repeat same-effect edges | Same outcomes and obligations | D17 |
| Repeat REQUIRE action -> AUDIT | One audit obligation | D17 |
| Duplicate entity declaration | Compile error | D18 |
| Same identifier in entity/action namespaces | No name collision | D18 |
| Reference declared later | Resolves successfully | D18 |
| Unknown role or duplicate field in an entity | Compile error | D18 |
| bool compared with int, or string ordering | Type error | D19 |
| int ordering or same-type equality | Type-valid | D19 |
| Zero-parameter ACTION declaration | Parses; TEST invocation is an arity error | D19 |
| TEST invokes role-constrained non-actor parameter | Binding error; no inferred role | D19 |
| Declared subject differs from actor parameter type | Policy decides; mismatch alone is not rejection | D15, D19 |
| Valid invariant references and constraint operand types | Structural/type validity only, not runtime enforcement | D20 |

### Independent evaluator and target comparison

M2 publishes source/diagnostic vectors and exhaustively checks the 16 combinations
of bare/role ALLOW/DENY edges in both RULE orders against an independent truth table.
This is not a separate implementation by an external author. Ask an
independent implementer to build a small evaluator from the specification alone.
Compare decisions exhaustively over finite declared subject/action combinations.
For M4, execute the same vectors against the generated artifact and record the
compiler version, source hash, target version, and source-to-target mapping.
Finite scenario agreement does not prove equivalence for arbitrary state or code.

Benchmark one bounded document-access workflow against direct Python and a policy
tool, using equivalent semantics explicitly documented for each baseline. Record
authoring time, defects detected from a published mutation set, diagnostic usefulness,
latency distribution, memory use, hardware, seeds, and reproduction commands.
Publish negative results. External review and adoption are outcomes to obtain,
not completed tasks or prerequisites that can be simulated locally.

Local validation covers the complete unit suite and installed CLI. Remote CI status
must be checked separately before merge. Tests do not establish production readiness.
