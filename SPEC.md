# AION v0.1 — Language Specification

## 1. Purpose

AION (AI-Oriented Intent Language) is an experimental language for expressing system intent, entities, actions, rules, permissions, constraints, guarantees, invariants, and tests at a semantic level above conventional implementation languages.

AION is designed so that humans can specify what a system must mean and guarantee, while compilers or AI-assisted toolchains determine how that intent is implemented for a target platform.

## 2. Design Principles

- **Intent over implementation** — describe desired behavior and constraints rather than low-level procedures.
- **Explicit semantics** — important behavior should have machine-readable meaning.
- **Machine verifiability** — guarantees and constraints should be represented explicitly enough to validate implementations.
- **AI-friendly structure** — the language should be easy for AI systems to reason about without requiring natural-language ambiguity.
- **Human readability** — specifications should remain understandable to engineers and system designers.
- **Security by construction** — permissions, denials, audit requirements, and security constraints should be first-class concepts.
- **Target independence** — the same AION specification may eventually generate implementations in different conventional languages.

## 3. Core Constructs

The v0.1 vocabulary:

- `SYSTEM` — names the system under specification.
- `ENTITY` — a thing the system models, optionally with declared `roles` and `fields`.
- `ACTION` — an operation on entities, optionally producing a result entity.
- `RULE` — a named group of policy blocks.
- `ALLOW` / `DENY` — permission edges from a subject (entity, optionally role-constrained) to an action.
- `REQUIRE` — obligations attached to actions; `AUDIT` is the v0.1 obligation.
- `GUARANTEE` — a named property with an explicit *class* (`static`, `monitor`, `proof`).
- `CONSTRAINT` — a bounded comparison over declared entity fields.
- `INVARIANT` — a property of state that must survive designated actions.
- `TEST` — an executable conformance scenario over the policy model.

The concrete syntax, the guarantee predicate catalog, and the decision log live in [`GRAMMAR.md`](GRAMMAR.md) and are part of this specification.

## 4. Normative Example

`OrderService` is the v0.1 conformance example: every construct above appears in it, and the milestone M1 parser must accept it while the M2 test runner must pass both of its `TEST` blocks.

```aion
SYSTEM OrderService

# --- Model ---
ENTITY Customer

ENTITY Staff
    roles: [Support, Finance]

ENTITY Order
    fields: [total: int, paid: bool]

ENTITY Payment
    fields: [amount: int]

ENTITY Refund
    fields: [amount: int]

# --- Actions ---
ACTION create_order(Customer) -> Order
ACTION pay(Customer, Order) -> Payment
ACTION cancel(Staff[Support], Order)
ACTION refund(Staff[Finance], Payment) -> Refund

# --- Policy ---
RULE OrderPolicy
ALLOW
    Customer -> create_order
    Customer -> pay
    Staff[Support] -> cancel
    Staff[Finance] -> refund
DENY
    Customer -> refund
REQUIRE
    refund -> AUDIT
    pay -> AUDIT

# --- Properties ---
INVARIANT paid_total_final
    after pay, Order.total unchanged

CONSTRAINT refund_limited
    Refund.amount <= Payment.amount

GUARANTEE static well_formed_policy
    NO_DANGLING_EDGES and CONFLICT_FREE

GUARANTEE static no_dead_actions
    NO_DEAD_ACTIONS

# --- Conformance ---
TEST support_cannot_refund
    Staff[Support] attempts refund(Payment)
    EXPECT DENIED

TEST customer_payment_is_allowed_and_audited
    Customer performs pay(Order)
    EXPECT ALLOWED, AUDIT
```

Notes on why this example is well-formed under [`GRAMMAR.md`](GRAMMAR.md):

- Every edge target is a declared `ACTION`; every role and field is declared (D3, D4).
- `refund` returns a declared `Refund` entity, so the constraint compares two entity field-refs, `Refund.amount <= Payment.amount` — an `ACTION` name is never a valid operand (D13). Field-refs use the exact declared entity names and are case-sensitive (D12).
- `DENY Customer -> refund` names a subject (`Customer`) that is unrelated to the only `ALLOW` subject for `refund` (`Staff[Finance]`), so it duplicates no exact pair and is legal under the conflict rule (D2). It is redundant under the fail-closed default (D1) but harmless, and documents intent.
- Both guarantees are `static` and built from reserved predicate atoms (`NO_DANGLING_EDGES`, `CONFLICT_FREE`, `NO_DEAD_ACTIONS`), so v0.1 tooling can actually check them (D5, D8, D14). A property such as "zero unauthorized executions ever" has no atom and cannot be a `static` guarantee; it would be `monitor` or `proof`, and `proof` is unsupported in v0.1.
- The `TEST` expectations follow the D7/D11 decision procedure: `Staff[Support]` matches no `ALLOW` for `refund` (the only allow is `Staff[Finance]`, a different role), so the scenario is `DENIED` even though no explicit `DENY` names that pair — absence of a matching `ALLOW` means denial (D1). The subject-to-parameter mapping is defined by D15.

The D2/D11 *override* path (a broad `ALLOW` on a bare entity with a role-scoped `DENY` carved out for the same action) is not exercised by `OrderService` — its allow/deny pairs are across different entities. It has a dedicated witness in [`examples/role-override.aion`](examples/role-override.aion).

## 5. Proposed Toolchain

```
AION Source
    ↓
Lexer
    ↓
Parser                     (M1 — deterministic, hand-written, no LLM)
    ↓
Abstract Syntax Tree
    ↓
Semantic Model             (M2 — symbols, types, policy conflicts)
    ↓
Constraint / Security Validation   (M2 — static guarantees, TEST runner)
    ↓
Intermediate Representation  (M3 — stable bridge for tools and AI layers)
    ↓
Code Generation            (M4 — narrow target first: policy artifact)
    ↓
Target Language
    ↓
Executable System
```

An AI reasoning layer may eventually assist with implementation generation, optimization, and mapping intent to target technologies — but only above the IR, only after M3, and never inside parsing or validation (see [`MILESTONES.md`](MILESTONES.md) M5).

## 6. v0.1 Non-Goals

AION v0.1 will not attempt to:

- replace general-purpose programming languages;
- solve arbitrary natural-language ambiguity;
- make formal-verification claims (`proof`-class guarantees have no backend yet);
- require an LLM for basic parsing;
- provide a complete production runtime;
- automatically generate safe production systems without validation;
- express state properties beyond two fixed idioms — one `INVARIANT` form and one `CONSTRAINT` form (this narrowness is deliberate; see D8);
- support concurrency, distribution, data-deployment, or infrastructure modeling (deferred past v0.1, to be re-proposed with grammar entries when taken up).

## 7. Open Design Questions

Status of the original eight questions after [`GRAMMAR.md`](GRAMMAR.md):

1. **Canonical type system** — *answered at v0.1 scope*: primitive field types (`int`, `bool`, `string`) plus entity and role references. Extension requires a decision-log entry.
2. **Core language vs. libraries** — *answered for v0.1*: everything in §3 is core; there is no library mechanism yet. First library candidates after M4: obligation kinds beyond `AUDIT`, additional guarantee predicates.
3. **Natural-language intent → deterministic semantics** — *deferred*. v0.1 sidesteps it by restricting expressions to declared names and fixed predicate shapes (D8).
4. **IR contents** — *assigned to M3* with a round-trip preservation requirement.
5. **Checking generated code against guarantees** — *partially answered*: `static` guarantees hold by construction of the pipeline (validated before generation); `monitor` guarantees require target instrumentation; traceability mapping is an M4 exit criterion.
6. **Concurrency and distributed systems** — *deferred*, non-goal for v0.1.
7. **Data, deployment, and infrastructure requirements** — *deferred*, non-goal for v0.1.
8. **Which security properties AION validates directly** — *answered for v0.1*: policy conflict-freedom, reachability, dangling references, obligation wiring, and the static guarantee catalog.

## 8. Versioning

The language specification version is independent of compiler implementation versions.

Breaking language changes require an appropriate specification version change and a `GRAMMAR.md` decision-log entry. Experimental features must be explicitly marked; in v0.1 the only such feature is parsing of `proof`-class guarantees, which must be rejected from the stable core by validators.

## 9. Status

AION v0.1 is an experimental research and engineering specification. The syntax and semantics are not yet frozen.

Per the status vocabulary in [`PHILOSOPHY.md`](PHILOSOPHY.md): the language constructs and grammar are **Specified**. The M1 syntactic front end (lexer, parser, AST, pretty-printer) and the M2 semantic validator (symbol tables, dangling-reference and conflict detection, static guarantee checks, and the `TEST` interpreter) in [`src/`](src/) are **Implemented** and — because their round-trip, parse, and validation tests pass — **Tested**. No part of the toolchain is yet **Verified** or **Proven**: the M2 validator checks *specs*, not the toolchain implementation against formal properties, and there is no verification backend in v0.1–M4 (so `proof`-class guarantees are rejected as unsupported).

All design decisions must be recorded in [`GRAMMAR.md`](GRAMMAR.md) before they become part of the stable language core.
