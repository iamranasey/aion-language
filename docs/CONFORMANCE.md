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
| D1–D4, D6–D8, D11–D15 semantic requirements | examples and docs/M2-DECISIONS-PROPOSED.md | Specified or proposed only; no evaluator |
| D5 proof rejection and monitor enforcement | src/README.md; M2/M4 plan | M1 accepts syntax only |
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

For M2, publish machine-readable vectors with spec, request, expected decision,
obligations, and diagnostic codes after semantic decisions are adopted. Ask an
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
