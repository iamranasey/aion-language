# AION Functional Vision

AION is at the **v0.1 experimental stage**. The language is defined in
[`SPEC.md`](../SPEC.md) and [`GRAMMAR.md`](../GRAMMAR.md); an **M1 syntactic
front end** (deterministic lexer, LL(1) recursive-descent parser, AST, and
round-trip pretty-printer) and an **M2 semantic validator** (symbol tables,
dangling-reference and conflict detection, static guarantee evaluation, and a
`TEST` interpreter) now exist under [`src/`](../src/) and are **Implemented** and
**Tested** ([`tests/test_m1.py`](../tests/test_m1.py) and
[`tests/test_m2.py`](../tests/test_m2.py) pass).
The repository does **not** yet contain an intermediate representation, compiler
back end, code generator, or runtime — those are M3–M4.
Per the status vocabulary in [`PHILOSOPHY.md`](../PHILOSOPHY.md), nothing is yet
**Verified** or **Proven**.

This document describes what a future functional AION could create and recommends
a narrow first proof-of-concept that tests the core idea without overextending the
project. Everything here beyond the M1–M2 front end and validator is **direction,
not current repository behavior.**

## Functional Goal

A functional AION implementation should prove that a meaningful system
specification can be written in AION, interpreted by deterministic tooling,
validated against explicit rules, and turned into working software:

```text
Specification
    -> Machine interpretation
    -> Validated implementation
    -> Working software
```

The point is not that AION replaces existing programming languages immediately.
The point is that system meaning, constraints, permissions, requirements, and
guarantees become structured inputs that tools can analyze *before* implementation
details dominate the design — and, per [`PRIOR-ART.md`](../PRIOR-ART.md) §2, that
an AI model asked to implement against an AION spec can be **mechanically checked**
against declared intent rather than trusted on review.

## What a Functional AION Could Create

A future AION toolchain may generate or validate several kinds of systems. These
are directional future capabilities, not current behavior, and each is subject to
the deferrals recorded in [`SPEC.md`](../SPEC.md) §7 — notably concurrency and
distributed systems (open question 6) and data/deployment/infrastructure shape
(open question 7), which are **non-goals for v0.1**.

### 1. Secure Access-Control Systems

AION is naturally suited to systems where roles, permissions, denials, audit
requirements, and guarantees must be explicit: hospital record access, internal
enterprise tools, document-management permissions, administrative portals,
regulated data workflows.

This is the strongest first target because it aligns directly with the v0.1
vocabulary already specified and parsed: `ENTITY`, `ACTION`, `RULE`, `ALLOW`,
`DENY`, `REQUIRE`, `GUARANTEE`, `CONSTRAINT`, `INVARIANT`, and `TEST`. Note that
AION expresses security as **checkable properties over the declared model** —
dangling edges, conflicting allow/deny pairs, dead actions, unwired obligations —
not as informal prose. A phrase like "unauthorized access is impossible" is **not**
a valid v0.1 guarantee: it names no declared construct and belongs to the
unsupported `proof` class (D5). What AION can state today is a `static` guarantee
such as `CONFLICT_FREE` or `NO_DEAD_ACTIONS`, evaluated over the policy model.

### 2. API and Backend Generation

A future AION system could describe backend behavior at the level of domain
entities, actions, validation rules, authorization policies, and expected
guarantees, and a generator could emit a conventional backend skeleton in a target
language such as Python — data models, API routes, request validation,
authorization checks, audit hooks, and tests derived from AION rules.

This should only be attempted after the IR and generation layers are reliable
(M3–M4) — the parser (M1) and semantic validator (M2) are already in place — and
it is gated by the traceability requirement in
[`MILESTONES.md`](../MILESTONES.md) M4.

### 3. Network Policy Engine

AION could eventually describe network policy at an intent level: zones, services,
allowed and denied traffic paths, management access, audit requirements, and policy
tests — for example, that guest devices must not reach clinical systems and
management access must be audited.

At first this needs no real infrastructure configuration; a smaller milestone could
validate policies and detect contradictions in an AION model. Full infrastructure
modeling depends on open question 7 and is deferred.

### 4. Workflow Engine

AION may also fit workflow-heavy systems where process correctness dominates:
approval chains, onboarding, incident response, compliance reviews, ticket routing,
intake. AION could describe states, allowed and denied transitions, required
approvals, audit events, and invariants such as "a request cannot be approved by the
same user who submitted it."

This requires language design beyond the current v0.1 vocabulary, so it remains a
later exploration.

### 5. Configuration and Infrastructure

AION could eventually express configuration and infrastructure intent without
binding the language to a specific cloud provider or deployment platform. This area
must be approached carefully and maps to deferred open question 7: AION should not
claim infrastructure safety until validation mechanisms are real and testable.

### 6. AI-Agent Specification

AION may eventually describe AI-agent behavior structurally: allowed tools, denied
actions, required checks, escalation rules, memory/data-access constraints, safety
invariants, and behavior tests. This is a promising long-term direction precisely
because AION targets machine-readable intent, but it should not be the first
implementation target — it involves ambiguity, runtime behavior, and safety issues
that require a stronger language foundation.

## Recommended First Proof-of-Concept: AION Secure Access System

The recommended first functional vertical slice is an **AION Secure Access
System**: take a small AION source file describing a secure access-control domain
and produce a working Python application that enforces the specified rules.

```text
AION source
    -> Lexer            (M1: implemented)
    -> Parser           (M1: implemented)
    -> AST              (M1: implemented)
    -> Semantic model + validator   (M2: implemented)
    -> AION IR / model              (M3)
    -> Validator / generator        (M4)
    -> Python backend               (M4)
    -> Working application
```

This slice is intentionally narrow. It should not attempt to generate every kind of
application; it should prove that AION can represent a serious requirement, validate
it, and map it into a working implementation with full source → IR → target
traceability.

## Example Proof-of-Concept Scope

A small first system could model hospital record access. The following is written
in the **current v0.1 grammar exactly** so it parses under the M1 front end and
validates clean under the M2 validator (both `TEST` blocks resolve to their stated
expectations):

```aion
SYSTEM HospitalAccess

ENTITY User
    roles: [Doctor, Nurse, Admin]

ENTITY PatientRecord
    fields: [id: int]

ACTION read_record(User, PatientRecord)
ACTION delete_record(User[Admin], PatientRecord)

RULE RecordAccess
ALLOW
    User[Doctor] -> read_record
    User[Nurse] -> read_record
    User[Admin] -> delete_record
DENY
    User[Nurse] -> delete_record
REQUIRE
    read_record -> AUDIT
    delete_record -> AUDIT

GUARANTEE static well_formed_policy
    NO_DANGLING_EDGES and CONFLICT_FREE and NO_DANGLING_OBLIGATIONS

GUARANTEE static no_dead_actions
    NO_DEAD_ACTIONS

TEST nurse_cannot_delete
    User[Nurse] attempts delete_record(PatientRecord)
    EXPECT DENIED

TEST doctor_read_is_audited
    User[Doctor] performs read_record(PatientRecord)
    EXPECT ALLOWED, AUDIT
```

Why this is well-formed under the current grammar (and how an earlier informal
sketch in this file was wrong):

- **Subjects are entities, optionally role-scoped** — `User[Nurse]`, not a bare
  role name like `Nurse` or `Doctor` (roles are declared inside an `ENTITY`, they
  are not standalone subjects).
- **Edges target declared actions** — `User[Doctor] -> read_record`, not
  `Doctor -> READ PatientRecord`. The resource is carried by the action's
  parameters (`read_record(User, PatientRecord)`), not appended to the edge.
- **`REQUIRE` obligations name declared actions** — `read_record -> AUDIT`, not an
  undeclared `every_access -> AUDIT`.
- **`GUARANTEE` has a class, a name, and catalog atoms** — `GUARANTEE static
  well_formed_policy NO_DANGLING_EDGES and CONFLICT_FREE`, not a free expression
  like `unauthorized_access == 0`. The predicate atoms are reserved (D14); free
  English or arithmetic is rejected.
- **Denial is fail-closed (D1).** `User[Nurse] -> delete_record` is already denied
  because `delete_record`'s only `ALLOW` is scoped to `User[Admin]`; the explicit
  `DENY` documents intent and demonstrates the role-override shape (D2/D11) rather
  than changing the outcome. The `TEST` expectations follow the D7/D15 decision
  procedure.

The first implementation could validate this specification and generate a simple
Python backend with role definitions, resource definitions, authorization checks,
deny-rule enforcement, audit-logging hooks, and tests for the allowed and denied
cases. It should prefer clarity and traceability over feature coverage: every
generated behavior must be explainable from the AION source.

## Vertical Architecture

The first functional architecture stays deterministic and inspectable.

- **AION Source** — the human-authored `.aion` file: system, entities, actions,
  rules, permissions, requirements, guarantees, invariants, and tests.
- **Lexer / Parser / AST (M1, implemented)** — deterministic tokenization and
  LL(1) parsing into an AST, with a pretty-printer that round-trips
  `parse → print → re-parse`. No LLM anywhere in this path (D9).
- **Semantic Validator (M2, implemented)** — checks that referenced entities,
  roles, actions, and fields exist; that rules are structurally valid and
  conflict-free (with role-override resolution, D2/D11); that `proof`-class
  guarantees are rejected; that static guarantee atoms are evaluated; and that
  `TEST` scenarios resolve under the D7 decision procedure.
- **AION IR / Model (M3)** — a normalized representation of the source's meaning,
  suitable for validation, testing, and generation, with round-trip preservation.
- **Validator / Generator (M4)** — inspects the model, reports contradictions or
  unsupported features, and generates a target implementation only when the model is
  valid for the selected backend, emitting a source → IR → target traceability map.
- **Python Backend / Working Application** — a small, transparent, runnable service
  demonstrating the specified behavior with tests. Python is a practical first
  backend: readable, testable, fast to prototype.

## Engineering Discipline

AION should prove its core idea with a small, rigorous implementation before
expanding. The first implementation should: keep the grammar small; implement a
deterministic lexer and parser; define an explicit AST and intermediate model;
validate a limited but meaningful subset; generate a small Python backend; include
tests connecting AION source to generated behavior; avoid claims of formal
verification until verification mechanisms exist; and clearly mark experimental
behavior.

Expansion into API generation, workflow systems, infrastructure, network policy,
and AI-agent specification comes only after the first secure access-control slice
works end-to-end.

## Current Status Versus Future Direction

Current status (v0.1):

- The language constructs and grammar are **Specified**; the syntax and semantics
  are not frozen.
- The **M1 front end** (lexer, parser, AST, pretty-printer) is **Implemented** and
  **Tested** — all six `examples/*.aion` parse and round-trip.
- The **M2 semantic validator** (symbol tables, dangling-reference and conflict
  detection, static guarantee evaluation, and the `TEST` interpreter) is
  **Implemented** and **Tested** — the four positive specs validate clean with
  every `TEST` meeting its expectation, and the two negative specs produce exactly
  their intended diagnostics. 63 tests pass across `tests/test_m1.py` and
  `tests/test_m2.py`.
- There is **no IR, generator, or runtime yet** (M3–M4).
- Nothing is **Verified** or **Proven**; the M2 validator checks *specs*, not the
  toolchain implementation against formal properties, and examples remain design
  exploration until the generation layers catch up with the specification.
- Security and validation concepts are goals, not proven production guarantees.

Future direction:

- an explicit intermediate representation with round-trip preservation (M3);
- targeted code generation with traceability (M4);
- small working systems generated from AION source;
- AI-assisted tooling layered strictly above the deterministic IR (M5).

The project should remain modest in claims while ambitious in direction: AION
should first show that intent-level specifications can become validated, working
software in one narrow domain. Once that is real, the language can expand with
stronger evidence and better design feedback.
