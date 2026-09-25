# AION Development Philosophy (Extended Companion)

**Scope of this document.** This is an extended, narrative companion to the
canonical [`PHILOSOPHY.md`](../PHILOSOPHY.md) at the repository root. Where the
two overlap, root `PHILOSOPHY.md` and the [`GRAMMAR.md`](../GRAMMAR.md) decision
log are **authoritative**; this file must not contradict them. If it ever does,
that is a defect to fix here, not a license to reinterpret the core docs. Per the
source-of-truth hierarchy in [`AI-CONTRIBUTOR-GUIDE.md`](../AI-CONTRIBUTOR-GUIDE.md),
decisions in `GRAMMAR.md` §3 win over prose anywhere.

AION is an experimental language project, so its development philosophy must be
ambitious in direction and disciplined in claims. The project grows from simple,
testable foundations before attempting broad automation or production-grade
generation, and it never presents a future capability as a present one.

## Core Principle: Decompose Complexity

AION should help humans and machines break complex systems into simpler,
explicit structures — decomposed, named, constrained, tested, and recomposed.

A useful AION specification should make a system easier to inspect, reason
about, validate, explain, and implement, not merely shorter to write. If AION
only makes a system shorter but not clearer, it has missed its purpose.

This means AION prefers:

- explicit entities over hidden assumptions;
- explicit actions over vague behavior;
- explicit rules over scattered logic;
- explicit constraints over informal expectations;
- explicit invariants over accidental stability;
- explicit guarantees over untested claims;
- explicit tests over undocumented confidence;
- explicit semantics over interpretation by convention alone.

The goal is not to remove complexity from the real world. The goal is to
represent complex systems in forms that expose their structure.

## Foundations

AION rests on **three** foundations, chosen because each offers a *method* of
reasoning rather than a metaphor. A foundation earns its place only by showing up
in a concrete design decision recorded in [`GRAMMAR.md`](../GRAMMAR.md) §3;
borrowing a discipline's vocabulary without a corresponding decision is not
allowed.

| Foundation | Method of reasoning | Where it appears in AION |
| --- | --- | --- |
| **Mathematics** | Abstraction, relation, constraint, structure, composition | Type discipline, declared entities/fields, invariants, constraints, the guarantee-predicate catalog |
| **Logic** | Consistency, implication, contradiction, consequence | Semantic validation, policy-conflict detection (D2/D11), the status vocabulary |
| **Computer science & formal methods** | Grammars, parsers, ASTs, semantic models, IRs, checkable specifications | The deterministic toolchain, the LL(1) grammar (D9), the milestone exit criteria in [`MILESTONES.md`](../MILESTONES.md) |

### Mathematics

Mathematics teaches how to reduce complexity into precise relationships. It
supports AION's questions about a system: What are the core objects? What
relations hold between them? Which states are allowed, and which are impossible?
Which transformations preserve the rules? Which guarantees can actually be
checked? For AION, mathematics is disciplined simplification — identifying the
smaller structures and relations that define a system — not calculation for its
own sake.

### Logic

Logic defines valid reasoning, implication, contradiction, and consistency, and
formal methods turn requirements into properties a tool can check. AION uses
these carefully and modestly: it does **not** claim formal verification until a
real verification backend exists, but it designs the language so validation and
proof-oriented reasoning remain possible later. The `proof` guarantee class is
parsed but **unsupported in v0.1** (D5); validators must reject it from the
stable core.

### Computer Science & Formal Methods

Computer science provides the practical foundations for grammars, parsers, type
systems, compilers, automata, and programming-language theory. The lexer, parser,
AST, semantic model, and intermediate representation must be **deterministic and
testable**. Per **D9** and the M5 gate, no language model, embedding, or other
non-deterministic component may sit in the parse or validate path — ever, and
regardless of how it is framed.

## Inspirations, Not Foundations

Physics, systems theory, information theory, control theory and cybernetics,
cognitive science, linguistics, and biology each offer appealing lenses —
system boundaries and causality, feedback and stability, signal versus noise,
modularity and adaptation, readability and learnability. They may *inform*
future work.

They are **not** design inputs. An inspiration becomes a foundation only when a
`GRAMMAR.md` decision-log entry demonstrates its relevance to a concrete language
choice. Until then, AION does not reason from physical or biological metaphor,
and this document does not claim otherwise. **Breadth is not a foundation.**

## Status Vocabulary and Honest Claims

AION documentation and tooling distinguish five levels of confidence, and they
are not interchangeable:

- **Specified** — described in project documentation.
- **Implemented** — working code exists in the repository.
- **Tested** — automated or documented tests exercise the behavior.
- **Verified** — a defined checking mechanism confirms the implementation
  satisfies explicit properties within a stated scope.
- **Proven** — a formal proof exists under clearly stated assumptions.

Applied to the current repository: the **language constructs and grammar are
Specified**; the **M1 front end** (lexer, parser, AST, pretty-printer) and the
**M2 semantic validator** (symbol tables, dangling-reference and conflict
detection, static guarantee checks, and the `TEST` interpreter, under
[`src/`](../src/)) are **Implemented** and — because [`tests/test_m1.py`](../tests/test_m1.py)
and [`tests/test_m2.py`](../tests/test_m2.py) pass — **Tested**; **nothing is yet
Verified or Proven** (the M2 validator checks *specs*, not the toolchain
implementation against formal properties, and no proof backend exists in
v0.1–M4). Claims must never be stated a level above what they have earned.

## Verification Before Trust

AION does not ask users to trust generated systems blindly — including systems
generated by an AI model. Trust comes from parsing, validation, testing,
verification mechanisms, reviewable output, and evidence. Claim strength is
bounded by guarantee class: `static` > `monitor`, and any `proof` claim requires
an actual proof. Ambition is documented as direction, never presented as
completed capability.

## Fail Closed

**D1** — absence of an `ALLOW` means denial — is a security principle about the
language, and it is also the instinct AION applies to its own process. When it is
uncertain whether something is permitted by the current spec, grammar, or
milestone scope, the project treats it as *not allowed* and asks, rather than
treating silence as permission to proceed. Design decisions are recorded in
[`GRAMMAR.md`](../GRAMMAR.md) before they are treated as stable; experimental
features stay clearly marked until they are not.

## Differentiation

AION's positioning relative to Rego/Cedar, TLA+/Alloy/Dafny, and Gherkin — and
the falsifiable bet that its value is a substrate an AI can implement *against*
where "did the AI get it right" is a decidable question — is stated in
[`PRIOR-ART.md`](../PRIOR-ART.md) §2 (adopted) and summarized in root
[`PHILOSOPHY.md`](../PHILOSOPHY.md) and [`README.md`](../README.md). That thesis
is itself **Specified**: direction, not demonstrated capability. The milestones
that would validate or refute it are M4 (generation traceability) and M5 (AI
tooling gated behind deterministic validation).

## Development Principles

- Start with small, rigorous models before broad generation.
- Break complex systems into explicit entities, actions, rules, constraints,
  guarantees, invariants, and tests.
- Prefer deterministic compiler foundations over opaque generation.
- Use mathematics to clarify structure and relationships.
- Use logic and formal methods to support validation without overclaiming
  verification.
- Keep security and validation concepts visible in the language core.
- Treat AI assistance as a toolchain layer above the IR, never a substitute for
  precise semantics and never part of parsing or validation.
- Make generation traceable from AION source to target output.
- Document design decisions in the decision log before treating them as stable.
- Keep experimental features clearly marked until they are stable.
- Update the model when evidence contradicts an assumption, rather than
  protecting the assumption.

## Practical Meaning for AION v0.1

For the current stage, this philosophy translates into concrete discipline, and
the milestone plan in [`MILESTONES.md`](../MILESTONES.md) tracks progress against
it:

- **M0 — met:** a small grammar and decision log (D1–D15) before any syntax
  expansion; concrete example specs.
- **M1 — Implemented + Tested:** a deterministic hand-written lexer and
  recursive-descent parser, an AST, and a pretty-printer with a stable
  `parse → print → re-parse` round-trip over the conformance suite.
- **M2 — Implemented + Tested:** an explicit semantic model and static validator
  — the first component that can say "no" (dangling references, policy conflicts
  and role-override resolution, `proof` rejection, static guarantee evaluation,
  `TEST` arity and the D7 decision procedure). The four positive conformance
  specs validate clean with every `TEST` meeting its expectation; the two
  negative specs produce exactly their intended diagnostics.
- **M3–M5 — ahead:** a documented IR with round-trip preservation, then a narrow
  first code-generation target with traceability, then AI-assisted tooling layered
  strictly above the IR.

AION should first prove that a small intent-level specification can become a
validated, working implementation in one narrow domain. Once that is real, the
project can expand into larger domains with stronger evidence and better design
feedback — modest in claims, ambitious in direction.
