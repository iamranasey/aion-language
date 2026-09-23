# AION — Milestone Plan with Exit Criteria

This plan replaces the open-ended roadmap. Each milestone has explicit **exit
criteria**; a milestone is not "done" when the code is written, but when the
criteria are demonstrably met (tests, artifacts, or recorded results).

Current position: pre-M0.

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
  contradiction; the current licensing status and open recommendation are
  recorded, with any license change left to the copyright holder.

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
- Symbol tables for entities, roles, fields, actions, rules.
- Dangling-reference diagnostics (D3) for every construct that can dangle.
- Policy-conflict detection (D2): exact-pair ALLOW∩DENY reported as errors;
  role-override resolution implemented and tested.
- All five static guarantee predicates from `GRAMMAR.md` §2 implemented;
  failing guarantees are compile errors.
- A `TEST` interpreter implementing the D7 decision procedure; every `TEST`
  block in the conformance suite evaluates to its stated expectation.
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
