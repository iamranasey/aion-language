# AION

**AI-Oriented Intent Language**

AION is an experimental language project for describing software systems in terms of intent, semantics, constraints, permissions, guarantees, invariants, and tests.

The goal is to explore a language layer above conventional implementation code: one where humans can express what a system must mean and guarantee, while deterministic compiler components and future AI-assisted tooling help map that intent into concrete implementations.

AION is currently at **v0.1 experimental specification stage**. The syntax, semantics, architecture, and toolchain are not yet stable, and this repository does not yet contain a working compiler, runtime, package manager, or production-ready implementation.

## Why AION Exists

Modern software systems often contain important intent that is scattered across code, comments, documentation, tests, configuration, access-control rules, and deployment infrastructure. AION explores whether more of that intent can be represented directly in a structured, machine-readable language.

AION is designed around these ideas:

- Intent should be explicit, not hidden inside implementation details.
- Security, permissions, denials, audit requirements, constraints, and guarantees should be first-class concepts.
- Specifications should remain readable by humans while being structured enough for tools to parse and validate.
- AI systems may assist with reasoning, mapping, and generation, but core parsing should remain deterministic.
- AION should describe meaning before target implementation technology is chosen.

## Current Status

AION is in the earliest public project stage.

What exists now:

- A provisional language specification in [`SPEC.md`](SPEC.md).
- A working grammar (EBNF), guarantee semantics, and decision log in [`GRAMMAR.md`](GRAMMAR.md).
- A milestone plan with explicit exit criteria in [`MILESTONES.md`](MILESTONES.md).
- A development philosophy in [`PHILOSOPHY.md`](PHILOSOPHY.md).
- One normative example (`OrderService`, in `SPEC.md`) that doubles as the first conformance target.

What does not exist yet:

- A working lexer, parser, compiler, or interpreter.
- A finalized type system beyond the v0.1 primitives.
- An intermediate representation.
- Formal verification support (`proof`-class guarantees have no backend).
- Production code generation.
- A standard library or runtime.

Per the status vocabulary in [`PHILOSOPHY.md`](PHILOSOPHY.md): the language is **Specified**. Nothing is yet **Implemented**, **Tested**, **Verified**, or **Proven**. Examples should be treated as design exploration until the implementation catches up with the specification.

## Example Syntax

The following is the v0.1 normative example. It is general (an order-processing service — a domain any reader already understands), fully self-contained (every name is declared before use), and every property in it is checkable by the toolchain semantics defined in [`GRAMMAR.md`](GRAMMAR.md).

```aion
SYSTEM OrderService

ENTITY Customer

ENTITY Staff
    roles: [Support, Finance]

ENTITY Order
    fields: [total: int, paid: bool]

ENTITY Payment
    fields: [amount: int]

ACTION create_order(Customer) -> Order
ACTION pay(Customer, Order) -> Payment
ACTION cancel(Staff[Support], Order)
ACTION refund(Staff[Finance], Payment)

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

INVARIANT paid_total_final
    after pay, Order.total unchanged

CONSTRAINT refund_limited
    refund.amount <= payment.amount

GUARANTEE static well_formed_policy
    every ALLOW/DENY edge targets a declared ACTION
    and no (subject, action) pair appears in both ALLOW and DENY

GUARANTEE static no_dead_actions
    every declared ACTION is reachable by some ALLOW edge

TEST support_cannot_refund
    Staff[Support] attempts refund(Payment)
    EXPECT DENIED

TEST customer_payment_is_allowed_and_audited
    Customer performs pay(Order)
    EXPECT ALLOWED, AUDIT
```

This example expresses access policy, audit obligations, a state invariant, a bounded constraint, and statically checkable guarantees without choosing a programming language, database, service framework, or infrastructure provider.

Note the deliberate contrast with informal intent such as "unauthorized access is impossible": under the v0.1 semantics, that phrase is not a valid guarantee at all — it names no declared construct and belongs to the unsupported `proof` class. AION's goal is that such statements are either made precise or rejected, never silently accepted.

## Proposed Language Constructs

The v0.1 vocabulary:

- `SYSTEM`
- `ENTITY`
- `ACTION`
- `RULE`
- `ALLOW`
- `DENY`
- `REQUIRE`
- `GUARANTEE`
- `CONSTRAINT`
- `INVARIANT`
- `TEST`

These constructs are intended to describe system meaning, behavior, policy, and expected properties before implementation details are introduced. The grammar in [`GRAMMAR.md`](GRAMMAR.md) defines their syntax and the decision log records why they work the way they do.

## Proposed Architecture

The long-term toolchain direction is:

```text
AION Source
  -> Lexer
  -> Parser
  -> Abstract Syntax Tree
  -> Semantic Model
  -> Constraint and Security Validation
  -> Intermediate Representation
  -> Code Generation
  -> Target Language
  -> Executable System
```

An AI reasoning layer may eventually assist with implementation generation, optimization, explanation, and mapping intent to target technologies — layered above the intermediate representation, never inside parsing or validation.

## Project Structure

Current repository layout:

```text
.
├── README.md      # Project overview
├── SPEC.md        # Experimental v0.1 language specification
├── GRAMMAR.md     # EBNF grammar, guarantee semantics, decision log
├── MILESTONES.md  # Milestone plan with exit criteria
├── PHILOSOPHY.md  # Development philosophy and status vocabulary
├── LICENSE        # MIT License
└── .gitignore
```

Expected future layout:

```text
.
├── examples/       # OrderService + conformance suite specs
├── src/            # Lexer, parser, semantic model (M1/M2)
├── tests/          # Positive and negative conformance specs
├── docs/           # Design notes, IR schema (M3)
└── tools/          # Developer utilities and experiments
```

## Milestones

The full plan with exit criteria is in [`MILESTONES.md`](MILESTONES.md). Summary:

1. **M0 — Specification hardening:** grammar + decision log merged; 5 example specs; MIT licensing decision recorded.
2. **M1 — Parser and AST:** hand-written deterministic parser; conformance suite parses; round-trip printing.
3. **M2 — Semantic model and static validation:** symbol tables, conflict detection, static guarantees, TEST interpreter.
4. **M3 — Intermediate representation:** documented IR schema with round-trip preservation.
5. **M4 — First code-generation target:** narrow policy artifact target; generated output passes the same TEST scenarios.
6. **M5 — AI-assisted tooling:** LLM layer above the IR only, after M3.

Language foundation work comes before production tooling; AI assistance comes only where it strengthens deterministic workflows.

## Development Principles

AION development follows these principles (fuller version in [`PHILOSOPHY.md`](PHILOSOPHY.md)):

- Do not overclaim capabilities before they exist.
- Record design decisions in [`GRAMMAR.md`](GRAMMAR.md) before treating them as stable.
- Prefer deterministic compiler foundations over opaque generation.
- Keep security and validation concepts visible in the language core.
- Treat AI assistance as a toolchain layer, not a substitute for precise semantics.
- Make examples concrete enough to test the design.
- Keep experimental features clearly marked until stable.

## Contributing

AION is early enough that design discussion is as important as implementation.

Good contribution areas include:

- Reviewing and improving [`GRAMMAR.md`](GRAMMAR.md) (with decision-log entries).
- Writing conformance specs for the M0 suite (well-formed and deliberately broken ones).
- Designing the IR schema for M3.
- Building the M1 parser and M2 validator.
- Writing documentation that separates current behavior from future plans.

Before contributing implementation code, align changes with [`SPEC.md`](SPEC.md) and [`GRAMMAR.md`](GRAMMAR.md), and keep experimental behavior clearly labeled.

## License

AION is released under the [MIT License](LICENSE). This permissive license
applies to the repository's code, documentation, language specification,
examples, and related materials unless a file states otherwise.
