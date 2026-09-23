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
- A functional direction document in [`docs/FUNCTIONAL-VISION.md`](docs/FUNCTIONAL-VISION.md).
- A development philosophy in [`docs/DEVELOPMENT-PHILOSOPHY.md`](docs/DEVELOPMENT-PHILOSOPHY.md).
- An initial project philosophy and proposed toolchain direction.
- A small example vocabulary for expressing systems, entities, rules, permissions, requirements, guarantees, constraints, invariants, and tests.

What does not exist yet:

- A working lexer, parser, compiler, or interpreter.
- A finalized grammar or type system.
- A stable intermediate representation.
- Formal verification support.
- Production code generation.
- A complete standard library or runtime.

Any examples in this repository should be treated as design exploration until the implementation catches up with the specification.

## Example Syntax

The following example illustrates the intended style of AION. It is provisional and may change as the language design matures.

```aion
SYSTEM HospitalAccess

ENTITY User
    roles: [Doctor, Nurse, Admin]

ENTITY PatientRecord

RULE PatientRecordAccess

ALLOW
    Doctor -> READ PatientRecord
    Nurse -> READ PatientRecord

DENY
    unauthorized -> PatientRecord

REQUIRE
    every_access -> AUDIT

GUARANTEE
    unauthorized_access == 0
```

This example expresses access intent and security requirements without choosing a programming language, database, service framework, or infrastructure provider.

## Proposed Language Constructs

The initial vocabulary is intentionally small and subject to change:

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

These constructs are intended to describe system meaning, behavior, policy, and expected properties before implementation details are introduced.

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

An AI reasoning layer may eventually assist with implementation generation, optimization, explanation, and mapping intent to target technologies. However, AION should not require an LLM for basic parsing or deterministic language analysis.

## Project Structure

Current repository layout:

```text
.
├── README.md   # Project overview
├── SPEC.md     # Experimental v0.1 language specification
├── docs/       # Functional vision and development philosophy
├── LICENSE     # Proprietary license notice
└── .gitignore
```

Expected future layout may include:

```text
.
├── examples/       # Example AION programs and design cases
├── src/            # Lexer, parser, semantic model, and compiler prototype
├── tests/          # Language and toolchain tests
├── docs/           # Design notes, architecture, and contributor documentation
└── tools/          # Developer utilities and experiments
```

The future structure is directional, not a guarantee of current functionality.

## Roadmap Direction

AION's roadmap starts with language foundation work before production tooling:

1. Clarify and version the core language specification.
2. Define the grammar and canonical syntax.
3. Design the type system and semantic model.
4. Build a deterministic lexer and parser.
5. Represent parsed programs as an AST and intermediate representation.
6. Add validation for constraints, permissions, denials, guarantees, and invariants.
7. Create example AION programs that drive language decisions.
8. Add tests for language behavior and conformance.
9. Explore code generation targets after semantics are clear.
10. Investigate AI-assisted tooling only where it strengthens, explains, or accelerates deterministic workflows.

## Development Principles

AION development should follow these principles:

- Do not overclaim capabilities before they exist.
- Document design decisions before treating them as stable language behavior.
- Prefer deterministic compiler foundations over opaque generation.
- Use mathematics to clarify structure, relationships, constraints, invariants, and compositional reasoning.
- Use physics to reason about systems, interactions, causality, state, constraints, and failure modes.
- Draw carefully from logic, formal methods, computer science, systems theory, information theory, control theory, cognitive science, linguistics, security engineering, and other scientific foundations where they help reduce complexity into clearer structure.
- Keep security and validation concepts visible in the language core.
- Treat AI assistance as a toolchain layer, not as a substitute for precise semantics.
- Make examples concrete enough to test the design.
- Keep experimental features clearly marked until they are stable.

See [`docs/DEVELOPMENT-PHILOSOPHY.md`](docs/DEVELOPMENT-PHILOSOPHY.md) for the fuller philosophy.

## Contributing

AION is early enough that design discussion is as important as implementation.

Good contribution areas include:

- Reviewing and improving the language specification.
- Proposing concrete syntax examples.
- Identifying ambiguous semantics or missing constructs.
- Designing grammar, AST, and intermediate representation options.
- Adding example AION programs that expose real system-design needs.
- Building the first lexer, parser, semantic model, and test suite.
- Writing documentation that separates current behavior from future plans.

Before contributing implementation code, align changes with [`SPEC.md`](SPEC.md) and keep experimental behavior clearly labeled.

## License

AION is proprietary software. All rights are reserved unless explicit written permission is granted by the copyright holder. See [LICENSE](LICENSE) for details.
