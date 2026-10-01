# AION Glossary

This glossary defines the terms used across the AION documentation so readers can look up a word instead of guessing at it. It is **non-normative**: it explains vocabulary but decides nothing. If an entry here ever disagrees with [`GRAMMAR.md`](GRAMMAR.md) (the decision log), [`MILESTONES.md`](MILESTONES.md), [`SPEC.md`](SPEC.md), or [`PHILOSOPHY.md`](PHILOSOPHY.md), those documents win and the glossary should be corrected.

Status per the vocabulary in [`PHILOSOPHY.md`](PHILOSOPHY.md): the meanings below are **Specified**. Where a term names a tool or feature that does not exist yet, the entry says so.

The **Source** column points to where the term is defined or most fully used. `D1`–`D20` refer to entries in the decision log in `GRAMMAR.md`.

## Contents

1. [Language constructs](#1-language-constructs)
2. [Policy and decision semantics](#2-policy-and-decision-semantics)
3. [Guarantees](#3-guarantees)
4. [Syntax and grammar](#4-syntax-and-grammar)
5. [Toolchain and architecture](#5-toolchain-and-architecture)
6. [Testing and conformance](#6-testing-and-conformance)
7. [Status vocabulary](#7-status-vocabulary)
8. [Project process and governance](#8-project-process-and-governance)
9. [Milestones](#9-milestones)
10. [Philosophy and positioning](#10-philosophy-and-positioning)
11. [Neighboring tools (prior art)](#11-neighboring-tools-prior-art)
12. [Adopted M2 terminology](#12-adopted-m2-terminology)

---

## 1. Language constructs

Declaration keywords are uppercase and reserved.

| Term | Meaning | Source |
| --- | --- | --- |
| **AION** | AI-Oriented Intent Language: an experimental language for expressing system intent, entities, actions, rules, constraints, guarantees, invariants, and tests above the level of conventional implementation code. | SPEC §1 |
| **SYSTEM** | The first declaration in a spec; names the system under specification. | SPEC §3 |
| **ENTITY** | A thing the system models. May optionally declare `roles` and `fields`. | SPEC §3, GRAMMAR §2 |
| **role** | A named variant of an entity, declared in an entity's `roles:` list (for example `Staff` with roles `Support` and `Finance`). Referenced as `Entity[Role]`. Roles are declared, never inferred. | D4 |
| **field** | A named, typed attribute of an entity, declared in its `fields:` list. Fields are declared, never inferred. | D4 |
| **primitive type** | One of `int`, `bool`, `string`. The only field types in v0.1. | GRAMMAR §2, SPEC §7 |
| **ACTION** | An operation on entities. Declared with a parameter list and optionally a result entity, for example `ACTION refund(Staff[Finance], Payment) -> Refund`. | SPEC §3 |
| **parameter** | An entity (optionally role-constrained) that an action takes. | GRAMMAR §2 |
| **actor** | The first parameter of an action: the subject that performs it. | D15 |
| **result entity** | The entity named after `->` in an action declaration. Used to model a value an action produces, so it can be constrained. | D13 |
| **RULE** | A named group of policy blocks (`ALLOW`, `DENY`, `REQUIRE`). | SPEC §3 |
| **policy block** | One `ALLOW`, `DENY`, or `REQUIRE` section inside a `RULE`. | GRAMMAR §2 |
| **ALLOW** | A policy block listing permission edges. Absence of a matching `ALLOW` means denial. | D1 |
| **DENY** | A policy block listing denial edges. | GRAMMAR §2 |
| **edge** | A single `subject -> action` line in an `ALLOW` or `DENY` block. The action must be a declared `ACTION`. | GRAMMAR §2, D3 |
| **subject** | The party in an edge or test: a bare `Entity` or a role-qualified `Entity[Role]`. | GRAMMAR §2 |
| **REQUIRE** | A policy block attaching obligations to actions, for example `REQUIRE refund -> AUDIT`. | D6 |
| **obligation** | Something that must accompany every permitted execution of an action. `AUDIT` is the only obligation in v0.1. | D6 |
| **AUDIT** | The v0.1 obligation: every permitted execution of the action must produce an audit record. Also appears in test expectations (`EXPECT ALLOWED, AUDIT`). | D6, D7 |
| **INVARIANT** | A property of state that must survive a designated action. v0.1 has exactly one form: `after <ACTION>, <Entity>.<field> unchanged`. | D8 |
| **CONSTRAINT** | A bounded comparison over declared entity fields. v0.1 has exactly one form: one `field-ref` compared to another `field-ref` or a literal value. | D8, D13 |
| **field-ref** | A reference of the form `<Entity>.<field>`. Case-sensitive; both parts must be declared. `payment.amount` does not refer to `ENTITY Payment`. | D12 |
| **comparison / rel-op** | A relational comparison using `==`, `!=`, `<`, `<=`, `>`, `>=`. | GRAMMAR §2 |
| **value (literal)** | An integer, `true`, `false`, or a quoted string used on the right side of a comparison. | GRAMMAR §2 |
| **GUARANTEE** | A named property with an explicit class (`static`, `monitor`, or `proof`) and a predicate. See [Guarantees](#3-guarantees). | SPEC §3, D5 |
| **TEST** | An executable conformance scenario evaluated against the policy model. See [Testing](#6-testing-and-conformance). | D7 |
| **`->` (arrow)** | Three uses: in an action declaration it introduces the result entity; in an `ALLOW`/`DENY` edge it links a subject to an action; in a `REQUIRE` line it links an action to an obligation. | GRAMMAR §2 |
| **comment** | Text from `#` to the end of the line. Ignored. | GRAMMAR §1 |

## 2. Policy and decision semantics

| Term | Meaning | Source |
| --- | --- | --- |
| **fail-closed** | The default posture: a request is permitted only if an `ALLOW` edge matches and no higher-priority `DENY` applies. There is no implicit allow; equal-specificity conflicts are compile errors. | D1, D16 |
| **policy model** | The set of subjects, actions, and `ALLOW`/`DENY`/`REQUIRE` edges that a `TEST` is evaluated against. Not generated code. | D7 |
| **specificity** | A ranking of subjects. A role-qualified `Entity[Role]` has specificity 2; a bare `Entity` has specificity 1. Higher specificity wins. | D11 |
| **matching (an edge)** | A request `Entity[Role]` matches an edge on `Entity[Role]` (specificity 2) or bare `Entity` (specificity 1). A bare `Entity` request matches only bare `Entity`. | D7 |
| **override** | When a higher-specificity edge beats a lower-specificity one regardless of whether it is `ALLOW` or `DENY`. Example: `ALLOW User[Admin] -> archive` beats `DENY User -> archive` for an Admin. | D11 |
| **conflict** | An exact `(subject, action)` pair that appears in both `ALLOW` and `DENY` anywhere across all `RULE` blocks at the same specificity. A compile error even without a TEST. | D2, D11, D17 |
| **shadowed** | An `ALLOW` edge is shadowed when a higher-specificity `DENY` beats it for every possible request subject. A shadowed edge is not effective. | D11 |
| **effective ALLOW** | An `ALLOW` edge that is not shadowed for all possible subjects. Only effective allows count toward `NO_DEAD_ACTIONS`. | D11 |
| **dead action** | A declared `ACTION` that no effective `ALLOW` can ever reach. | D11, GRAMMAR §2 |
| **dangling reference** | A name that is used but never declared (an action, entity, role, field, or obligation target). A compile error, not a warning. | D3 |
| **decision procedure** | Gather matching edges and return `DENIED` if none match. Otherwise take the highest-specificity matching edges: if they contain both `ALLOW` and `DENY`, report an exact-pair conflict as a compile error, not a runtime outcome. Otherwise return `DENIED` for `DENY`, or `ALLOWED` for `ALLOW` (plus `AUDIT` if a `REQUIRE` covers the action). | D7, D11 |

## 3. Guarantees

| Term | Meaning | Source |
| --- | --- | --- |
| **guarantee class** | Says what "keeping the guarantee" means and what evidence exists: `static`, `monitor`, or `proof`. | D5, GRAMMAR §4 |
| **static** | Checked at compile time over the semantic model. Failure is a compile error. | D5 |
| **monitor** | Checked at runtime against execution traces. The compiler must emit instrumentation, and generation must not silently drop monitors. | D5, GRAMMAR §4 |
| **proof** | Requires a verification backend. Unsupported in v0.1: parsed for forward compatibility, but validation rejects it from the stable core with an explicit "unsupported" diagnostic. | D5 |
| **strength ordering** | `proof` > `static` > `monitor`. Documentation must never claim more than a guarantee's class supports. | GRAMMAR §4 |
| **predicate** | The property a guarantee asserts: a boolean combination (`and`, `or`, `not`, parentheses) of reserved atoms. | D14 |
| **atom (predicate atom)** | A single reserved uppercase token naming one checkable property. Adding a new atom requires a decision-log entry. | D14 |
| **`NO_DANGLING_EDGES`** | Every `ALLOW`/`DENY` edge targets a declared `ACTION`. | GRAMMAR §2 |
| **`CONFLICT_FREE`** | No `(subject, action)` pair appears in both `ALLOW` and `DENY` at the same specificity. | GRAMMAR §2 |
| **`NO_DANGLING_OBLIGATIONS`** | Every `REQUIRE` obligation targets a declared `ACTION`. | GRAMMAR §2 |
| **`NO_DEAD_ACTIONS`** | Every declared `ACTION` is reachable by some effective `ALLOW`. | GRAMMAR §2 |
| **`NO_DANGLING_STATE_REFS`** | Every `INVARIANT` and `CONSTRAINT` field-ref names a declared entity and field. | GRAMMAR §2 |
| **predicate catalog** | The fixed set of the five atoms above. Guarantees cannot use arbitrary expressions in v0.1. | D8, D14 |
| **decidable by construction** | Because the semantic model is finite and each atom is a total function over it, evaluation always terminates with an answer. | GRAMMAR §2 |
| **instrumentation** | Runtime checking code the compiler must emit to enforce a `monitor` guarantee. | D5 |
| **trace (execution trace)** | A record of what a running system actually did. `monitor` guarantees are checked against traces. | GRAMMAR §4 |
| **unfalsifiable claim** | A claim no test or check could ever refute. The original `GUARANTEE unauthorized_access == 0` was one, because it named an undeclared variable and had no class. | GRAMMAR §4 |

## 4. Syntax and grammar

| Term | Meaning | Source |
| --- | --- | --- |
| **EBNF** | Extended Backus-Naur Form: the notation `GRAMMAR.md` uses to state the syntax precisely. | GRAMMAR §1–2 |
| **token** | The smallest unit the lexer produces: an identifier, keyword, number, string, or punctuation mark. | GRAMMAR §1 |
| **ident (identifier)** | A name: a letter followed by letters, digits, or underscores. Case-sensitive. | GRAMMAR §1 |
| **reserved word** | A word that cannot be reused as a declared name. Two tiers: declaration keywords and context keywords. | GRAMMAR §1 |
| **declaration keyword** | Uppercase reserved words that begin a declaration: `SYSTEM ENTITY ACTION RULE ALLOW DENY REQUIRE GUARANTEE CONSTRAINT INVARIANT TEST`. | GRAMMAR §1 |
| **context keyword** | Words reserved where they appear: `roles fields int bool string after unchanged and or not attempts performs EXPECT ALLOWED DENIED AUDIT static monitor proof`. | GRAMMAR §1 |
| **LL(1)** | A grammar property: the parser can decide what a declaration is by looking at its first keyword alone, with no semantic information. | D9 |
| **lexer** | The component that turns source text into tokens. | SPEC §5 |
| **parser** | The component that turns tokens into an AST. AION's is hand-written, deterministic, and never calls an LLM. | D9, M1 |
| **recursive descent** | A hand-written parsing style with one function per grammar rule. | MILESTONES M1 |
| **AST** | Abstract Syntax Tree: the structured representation of a parsed spec. | SPEC §5 |
| **pretty-printer** | Turns an AST back into canonical AION source text. | MILESTONES M1 |
| **round-trip** | The property that `parse → print → re-parse` produces a stable result. Also used for IR: semantic model → IR → semantic model must preserve all information. | MILESTONES M1, M3 |
| **deterministic** | The same input always yields the same output; no randomness and no LLM in the parse or validate path. | D9 |

## 5. Toolchain and architecture

The pipeline is: source → lexer → parser → AST → semantic model → validation → IR → code generation → target → executable system (SPEC §5).

| Term | Meaning | Source |
| --- | --- | --- |
| **semantic model** | The checked representation of a spec: symbol tables plus resolved references, on which validation and `TEST` evaluation run. Planned for M2. | SPEC §5, M2 |
| **symbol table** | A lookup of declared entities, roles, fields, actions, and rules. | M2 |
| **validation** | Static checks over the semantic model: dangling references, conflicts, and static guarantees. | M2 |
| **diagnostic** | A compiler message reporting a problem, with line and column where applicable. M1 exposes lexical/syntax error codes; semantic diagnostics are planned for M2. | M1, M2, src/README |
| **source span** | Original source coordinates with a one-based start and exclusive end, retained outside structural AST equality through `parse_with_locations`. | src/README |
| **IR (intermediate representation)** | A stable, documented, serializable form between the semantic model and code generators. Planned for M3. | M3 |
| **lowering** | Converting the semantic model into the IR. | M3 |
| **code generation** | Producing target output from the IR. Planned for M4. | M4 |
| **target** | What generation produces: for M4, a narrow policy artifact (OPA/Rego or a generated Python policy module is recommended). | M4 |
| **traceability report** | A mapping of source constructs → IR nodes → target output, produced for every generated artifact. | M4 |
| **AI reasoning layer** | Optional future tooling that proposes implementation mappings or optimizations. It consumes the IR only and never touches parsing or validation. | M5 |
| **verification backend** | A tool that can actually prove properties. None exists in v0.1, which is why `proof` guarantees are unsupported. | D5 |

## 6. Testing and conformance

| Term | Meaning | Source |
| --- | --- | --- |
| **scenario** | The `subject attempts/performs action(args)` line of a `TEST`. | GRAMMAR §2 |
| **EXPECT** | Introduces the expected outcome of a `TEST`. | GRAMMAR §2 |
| **ALLOWED / DENIED** | The two possible outcomes. `ALLOWED` may be followed by `, AUDIT`. | D7 |
| **attempts / performs** | Syntactic synonyms in a scenario. They exist so tests read naturally for negative and positive cases. | D7, D15 |
| **subject binding** | In a `TEST`, the subject binds to the action's actor parameter and the argument list binds positionally to the rest. Arity is checked. The subject need not match the actor's declared type, because that mismatch is how a `DENIED` test is written. | D15 |
| **conformance suite (seed)** | The set of example specs in `examples/` used to check the tools. The M0 suite is the seed. | MILESTONES M0, examples/README |
| **normative example** | An example that is part of the specification: `OrderService` in `SPEC.md` §4. It produces the same AST as `examples/order-service.aion`; the specification includes additional section comments. | SPEC §4 |
| **positive spec** | A conformance spec that should parse, validate, and pass its tests. | examples/README |
| **negative spec** | A deliberately broken conformance spec that must produce the intended diagnostics, no more and no fewer. | examples/README, M2 |
| **witness** | A specific example that demonstrates a decision working. `examples/role-override.aion` is the witness for D2/D11. | GRAMMAR §5 |

## 7. Status vocabulary

Defined in `PHILOSOPHY.md`. The five terms are not interchangeable, and documentation must not claim a higher status than the evidence supports.

| Term | Meaning |
| --- | --- |
| **Specified** | Described in project documentation. |
| **Implemented** | Working code exists in the repository. |
| **Tested** | Automated or documented tests exercise the behavior. |
| **Verified** | A defined checking mechanism confirms the implementation satisfies explicit properties within a stated scope. |
| **Proven** | A formal proof exists under clearly stated assumptions and definitions. |

| Related term | Meaning | Source |
| --- | --- | --- |
| **status inflation** | Describing something as further along than the evidence supports (for example calling a spec-only feature "implemented", or a tested one "verified"). Forbidden. | AI-CONTRIBUTOR-GUIDE |
| **Verified ≠ Proven** | Passing a defined check within a scope is weaker than a formal proof. Guarantee classes operationalize this. | GRAMMAR §4 |

## 8. Project process and governance

| Term | Meaning | Source |
| --- | --- | --- |
| **decision log** | The numbered record in `GRAMMAR.md` §3 of *why* the language is shaped as it is. Entries are permanent. | GRAMMAR §3 |
| **decision entry (D1, D2, …)** | One numbered decision. It may only be replaced by a new entry that references it. | GRAMMAR §3 |
| **supersede** | To replace all or part of an earlier decision with a newer entry (for example D11 supersedes part of D2). | GRAMMAR §3 |
| **source-of-truth hierarchy** | The order of authority when documents disagree: decision log, then milestones, then spec, then philosophy, then README. | AI-CONTRIBUTOR-GUIDE |
| **PROPOSED (not merged)** | A document or change offered for review that has no authority until the human maintainer merges it. | AI-CONTRIBUTOR-GUIDE |
| **AI contributor** | Any AI model or agent contributing to the project. Bound by `AI-CONTRIBUTOR-GUIDE.md`. | AI-CONTRIBUTOR-GUIDE |
| **human arbiter** | The single human maintainer who decides what merges, which keeps multi-model development coherent. | AI-CONTRIBUTOR-GUIDE |
| **non-goal** | Something deliberately out of scope. Listed for v0.1 in `SPEC.md` §6 and for all milestones in `MILESTONES.md`. | SPEC §6 |
| **experimental feature** | A feature that must be explicitly marked. In v0.1 the only one is parsing of `proof` guarantees. | SPEC §8 |
| **pre-M0** | The recorded starting position before Specification hardening was complete. | MILESTONES |

## 9. Milestones

A milestone is done when its **exit criteria** are demonstrably met (tests, artifacts, or recorded results), not when code is written.

| Milestone | Name | Goal |
| --- | --- | --- |
| **M0** | Specification hardening | Turn design memos into something a parser can be built against. |
| **M1** | Parser and AST | A deterministic front end: lexer, parser, AST, pretty-printer, round-trip. |
| **M2** | Semantic model and static validation | The compiler starts saying "no": symbol tables, D3 diagnostics, conflict detection, the five atoms, and the `TEST` interpreter. |
| **M3** | Intermediate representation | A stable bridge between source, validators, and generators. |
| **M4** | First code-generation target | Prove the pipeline end-to-end on a narrow target. |
| **M5** | AI-assisted tooling layer | Add LLM assistance without compromising determinism. Not started before M3 is complete. |

## 10. Philosophy and positioning

| Term | Meaning | Source |
| --- | --- | --- |
| **intent over implementation** | Describe what a system means and must guarantee before choosing how it is built. Targets and frameworks are downstream. | PHILOSOPHY, SPEC §2 |
| **decompose complexity** | The central principle: name, constrain, test, and recompose complexity instead of denying it. | PHILOSOPHY |
| **foundation** | A discipline that guides AION and has earned its place by appearing in a concrete decision. The three are Mathematics, Logic, and Computer science and formal methods. | PHILOSOPHY |
| **secondary influence** | A discipline recorded as inspiration only, not a design input, until a decision-log entry demonstrates its relevance. Computer graphics is recorded this way (restricted DSLs, declarative scene description, staged pipelines, visualization, reference-output testing). | PHILOSOPHY |
| **generation verifiability** | AION's central bet: as AI takes on more implementation work, there must be a substrate where AI output can be mechanically checked against declared intent instead of trusted on review. Stated as falsifiable, not proven. | PHILOSOPHY, PRIOR-ART |
| **substrate** | The layer that makes checking possible: decidable guarantees, fail-closed policy semantics, and generation traceability. | PHILOSOPHY |
| **security by construction** | Permissions, denials, audit requirements, and security constraints are first-class language concepts. | SPEC §2 |
| **target independence** | The same spec may eventually generate implementations in different languages. | SPEC §2 |

## 11. Neighboring tools (prior art)

These are external projects, described only to explain how AION relates to them. See [`PRIOR-ART.md`](PRIOR-ART.md) for the full assessment.

| Tool | What it is |
| --- | --- |
| **Rego / OPA** | Open Policy Agent and its policy language, widely used for authorization and infrastructure policy. |
| **Cedar** | An authorization policy language and engine with analyzable semantics. |
| **TLA+** | A formal specification language for describing and model-checking system behavior. |
| **Alloy** | A lightweight formal modeling language with automated analysis. |
| **Dafny** | A programming language with built-in verification of code against specifications. |
| **Gherkin / BDD** | A readable given/when/then scenario format for behavior-driven development. |

## 12. Adopted M2 terminology

| Term | Meaning | Source |
| --- | --- | --- |
| **global policy composition** | All RULE blocks contribute to one model with no declaration-order precedence. | D17 |
| **idempotent edge** | Repeating the same policy effect or AUDIT obligation adds no new effect or repeated audit event. | D17 |
| **namespace** | Separate name domain per declaration category; duplicate declarations within it are errors. Roles and fields each have entity-local namespaces. | D18 |
| **forward reference** | Reference resolved after collecting declarations, so its declaration may occur later. | D18 |
| **strict comparison typing** | No coercions; equality requires matching primitive types and ordering requires ints. | D19 |
| **TEST binding restriction** | Zero-parameter actions and role-constrained non-actor parameters cannot be invoked by TEST. Remaining arguments name the declared parameter entity. | D19 |
| **state execution design gate** | M2 checks state references/types; runtime state enforcement awaits an explicit execution model. Unsupported target constructs must be rejected. | D20 |
