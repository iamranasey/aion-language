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

# --- Actions ---
ACTION create_order(Customer) -> Order
ACTION pay(Customer, Order) -> Payment
ACTION cancel(Staff[Support], Order)
ACTION refund(Staff[Finance], Payment)

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
    refund.amount <= payment.amount

GUARANTEE static well_formed_policy
    every ALLOW/DENY edge targets a declared ACTION
    and no (subject, action) pair appears in both ALLOW and DENY

GUARANTEE static no_dead_actions
    every declared ACTION is reachable by some ALLOW edge

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
- `DENY Customer -> refund` is an override of the broader `Staff`-level allow space without duplicating any exact pair, so it is legal under the conflict rule (D2).
- Both guarantees are `static` and drawn from the decidable predicate catalog, so v0.1 tooling can actually check them (D5, D8). A property such as "zero unauthorized executions ever" cannot be a `static` guarantee; it would be `monitor` or `proof`, and `proof` is unsupported in v0.1.
- The `TEST` expectations follow the D7 decision procedure: `Staff[Support]` matches no `ALLOW` for `refund`, so the scenario is `DENIED` even though no explicit `DENY` names that pair — absence of `ALLOW` means denial (D1).

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

Per the status vocabulary in [`PHILOSOPHY.md`](PHILOSOPHY.md): the language constructs and grammar are **Specified**. Nothing in this repository is yet **Implemented**, **Tested**, **Verified**, or **Proven**.

All design decisions must be recorded in [`GRAMMAR.md`](GRAMMAR.md) before they become part of the stable language core.
