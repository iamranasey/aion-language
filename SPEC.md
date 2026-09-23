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

The initial vocabulary includes:

- SYSTEM
- ENTITY
- ACTION
- RULE
- ALLOW
- DENY
- REQUIRE
- GUARANTEE
- CONSTRAINT
- INVARIANT
- TEST

This vocabulary is provisional and will evolve through the language-design process.

## 4. Example

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

The example expresses access intent and security requirements without prescribing a particular programming language, database, or network implementation.

## 5. Proposed Toolchain

```
AION Source
    ↓
Lexer
    ↓
Parser
    ↓
Abstract Syntax Tree
    ↓
Semantic Model
    ↓
Constraint / Security Validation
    ↓
Intermediate Representation
    ↓
Code Generation
    ↓
Target Language
    ↓
Executable System
```

An AI reasoning layer may eventually assist with implementation generation, optimization, and mapping intent to target technologies. The core parser should remain deterministic and should not require an LLM.

## 6. v0.1 Non-Goals

AION v0.1 will not attempt to:

- replace general-purpose programming languages;
- solve arbitrary natural-language ambiguity;
- make formal-verification claims without an actual verification mechanism;
- require an LLM for basic parsing;
- provide a complete production runtime;
- automatically generate safe production systems without validation.

## 7. Open Design Questions

The project must resolve:

1. What is AION's canonical type system?
2. Which constructs belong in the core language versus libraries?
3. How should natural-language intent map to deterministic semantics?
4. What should the AION intermediate representation contain?
5. How can generated implementations be checked against AION guarantees?
6. How should concurrency and distributed systems be represented?
7. How should data, deployment, and infrastructure requirements be expressed?
8. What security properties can AION validate directly?

## 8. Versioning

The language specification version is independent of compiler implementation versions.

Breaking language changes require an appropriate specification version change. Experimental features should be explicitly marked so that the stable core remains identifiable.

## 9. Status

AION v0.1 is an experimental research and engineering specification. The syntax and semantics are not yet frozen.

All design decisions should be documented before they become part of the stable language core.
