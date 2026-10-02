# AION — Milestone Plan with Exit Criteria

This plan replaces the open-ended roadmap. Each milestone has explicit **exit
criteria**; a milestone is not "done" when the code is written, but when the
criteria are demonstrably met (tests, artifacts, or recorded results).

Current position: M2 is accepted and merged into `main` (PRs #7 and #12) under
D16–D20. It is Implemented and Tested: the full CI matrix (3 operating systems ×
Python 3.10–3.14) passes, and the local suite is 97 tests plus 150 subtests. The
suite covers M1 parsing/round trips, M2 conformance, namespace uniqueness, global
conflicts, comparison typing, and TEST bindings (see `docs/CONFORMANCE.md`). The
four positive seed specs validate clean and the two negative specs report their
expected six/two diagnostics. M0, M1, and M2 are complete; nothing is Verified or
Proven. Next: M3 — intermediate representation.
Runtime state enforcement remains deferred under D20; no IR or code generation exists.


---

## M0 — Specification hardening

**Goal:** turn the design memos into something a parser can be built against.

Exit criteria:
- `GRAMMAR.md` merged, with decision-log entries covering D1–D10.
- The `OrderService` example plus at least 4 additional example specs are
  written and hand-checked against the grammar (they are the seed conformance
  suite; they need a parser to be machine-checked, but they must be
  syntactically unambiguous to a careful human reader).
- Open design questions 1 (type system) and 2 (core vs. libraries) in
  `SPEC.md` are answered at v0.1 scope: minimal primitive types and entity/role
  references only; everything else deferred — and the deferral is recorded.
- `README.md`, `SPEC.md`, `GRAMMAR.md`, and `PHILOSOPHY.md` cross-checked for
  contradiction; the licensing question is decided and recorded. **Resolved:**
  the copyright holder adopted the MIT License for the repository (see
  `LICENSE` and the License section of `README.md`), replacing the earlier
  proprietary notice.

## M1 — Parser and AST

**Goal:** a deterministic front end.

Exit criteria:
- Hand-written recursive-descent parser (host language chosen and recorded;
  recommendation: Python for iteration speed, with the IR defined
  language-agnostically so a Rust rewrite is not a rewrite of the design).
- 100% of the M0 conformance suite parses.
- Error messages carry line and column and identify the expected construct.
- An AST pretty-printer exists, and `parse → print → re-parse` is stable
  (round-trip test) for every conformance spec.
- No LLM or other non-deterministic component anywhere in the parse path.

## M2 — Semantic model and static validation

**Goal:** the compiler starts saying "no."

Exit criteria:
- Symbol tables and namespace uniqueness for all declaration categories (D18),
  with roles/fields scoped per entity and forward-reference resolution.
- Dangling-reference diagnostics (D3) for every construct that can dangle.
- Global policy-conflict detection (D17): exact-pair ALLOW∩DENY across all
  RULEs reported as errors; D16 specificity and idempotent edges tested.
- Strict comparison typing and TEST binding checks (D19). State checking
  covers references/types only, with no runtime enforcement claim (D20).
- All five static guarantee predicates from `GRAMMAR.md` §2 implemented;
  failing guarantees are compile errors.
- A `TEST` interpreter implementing the D7 decision procedure; every `TEST`
  block in the semantically valid positive conformance specs evaluates to its
  stated expectation. Invalid negative specs are checked for validation
  diagnostics, not successful `TEST` evaluation.
- Negative conformance specs (deliberately broken inputs) each produce exactly
  the intended diagnostic — no false positives, no silent passes.

## M3 — Intermediate representation

**Goal:** a stable bridge between source, validators, and generators.

Exit criteria:
- Documented IR schema with a serialized form.
- Lowering from the semantic model to IR.
- Round-trip property: semantic model → IR → semantic model preserves all
  policy, obligation, invariant, constraint, and guarantee information.
- `proof`-class guarantees are explicitly represented as *unsupported* nodes so
  no downstream tool can silently treat them as checked (D5).

## M4 — First code-generation target

**Goal:** prove the pipeline end-to-end on a narrow target.

Exit criteria:
- One target chosen and recorded (recommendation: OPA/Rego or a generated
  Python policy module — access control is the most mature part of the
  language, so the first target should be a policy artifact, not a full
  service).
- A defined, documented source subset lowers to the target.
- Generated artifacts pass the same `TEST` scenarios that pass at M2, evaluated
  against the artifact itself.
- A traceability report mapping source constructs → IR nodes → target output
  is produced for every generated artifact.

## M5 — AI-assisted tooling layer

**Goal:** add LLM assistance without compromising determinism. Not started
before M3 is complete.

Exit criteria:
- The AI layer consumes IR only; it has no access to the parse or validate
  path.
- Every AI-generated proposal (implementation mapping, optimization,
  explanation) is mechanically diffable and passes deterministic validation
  before being presented as a result.
- Docs use the status vocabulary correctly: nothing AI-assisted is labeled
  Verified or Proven.

---

## Standing non-goals (all milestones)

- No formal-verification claims before a real verification backend exists.
- No LLM in the parse/validate path. Ever.
- No production-runtime or standard-library work before M4 exits.
- No new surface syntax without a `GRAMMAR.md` decision-log entry.
