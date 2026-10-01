# AION — Prior Art and Differentiation Thesis

**Status:** partially adopted (2026-09-24, by maintainer decision).

- **§2 (positioning) is ADOPTED** — its differentiation statement is merged
  into [`README.md`](README.md) and [`PHILOSOPHY.md`](PHILOSOPHY.md).
- **§1 (neighbor assessments) and §4 (open limitations) are informative**
  context and stand as written; they make no binding claim on their own.
- **§3 (the M4 reframe and its candidate exit criterion) is still PROPOSED.**
  It changes milestone scope, so per AI Contributor Guide §5–§6 it requires a
  `GRAMMAR.md` decision-log entry and explicit maintainer adoption before it
  is binding. It is **not** adopted here, and `MILESTONES.md` is unchanged by
  this document.

**Why this document exists:** every other document in this repository
answers "what is AION and how is it built." None answers "given that
mature, funded, production-deployed alternatives already occupy adjacent
territory, why does this project's specific bet succeed where enough of
them have struggled to reach mass adoption." That question was raised
against the README and never closed by the grammar/milestone rewrite,
because it isn't a grammar problem. This document is the first attempt to
close it — honestly, including the ways the bet could fail.

---

## 1. Informative comparisons and limits

These comparisons describe overlapping design goals. They do not establish
novelty, exclusive capability, patentability, or superiority.

### 1.1 Rego / OPA and Cedar

AION's policy examples overlap with established authorization tools. Its
current six seed examples exercise parsing and model validation, not a production authorization service.
AION's D11 specificity semantics differ from Cedar's forbid-overrides-permit
rule, so a future translation needs explicit semantic preservation rather
than direct keyword substitution. See [Cedar authorization semantics](https://docs.cedarpolicy.com/auth/authorization.html).
The first target remains a bounded experiment; no production advantage is
claimed. State constraints and invariants require an execution model before
an end-to-end enforcement comparison is meaningful.

### 1.2 TLA+, Alloy, and Dafny

These tools address related specification, analysis, and verification problems
with different execution models and proof obligations. A source-to-target
traceability report records provenance; it does not prove that translation
preserves semantics or eliminate implementation defects. AION has no proof
backend. Claims about comparative usability, adoption, or assurance need
explicit tasks and measured evidence, not broad assertions about formal methods.

### 1.3 Gherkin / BDD

AION specifies TEST outcomes through D7/D11 over its policy model. That evaluator
is implemented and covered by M2 conformance tests. This differs in design from scenarios
connected to implementation-specific step definitions, but it is not yet a
measured usability or correctness advantage.

### 1.4 Checking generated implementations

AION's research hypothesis is that a bounded intent model, executable reference
semantics, and traceable generation can make selected implementation behaviors
easier to check. Evaluation over a finite declared policy model is decidable;
that fact does not make arbitrary program correctness decidable. Passing a
finite scenario suite establishes only those observed outcomes. Broader claims
require a stated input domain, supported constructs, environmental assumptions,
and an appropriate exhaustive check or proof.

No unoccupied market or unique AI-verification capability is asserted. The
experiment and baseline measurements are described in [CONFORMANCE.md](docs/CONFORMANCE.md).

---

## 2. Adopted positioning

The adopted differentiation statement in `README.md` and `PHILOSOPHY.md` is:

> AION's bet is not that humans should specify systems in a new syntax
> instead of Rego, Cedar, or TLA+ — for policy alone, those are mature and
> often the better choice today. AION's bet is that as AI models take on
> more implementation work, there needs to be a substrate where an AI's
> output can be mechanically checked against declared intent rather than
> trusted on review — and that substrate needs decidable guarantees, fail-
> closed policy semantics, and generation traceability as load-bearing
> features, not add-ons. Whether that substrate needs to be a new language
> at all, versus a discipline layered on existing tools, is an open
> question this project treats as falsifiable rather than assumed.

That last sentence matters: it keeps the project honest about the
possibility that the differentiated value could eventually be delivered as
tooling *around* Rego/TLA+ rather than a wholly new language — which is a
more defensible position than asserting novelty the project hasn't yet
earned.

---

## 3. Proposed M4 reframe (requires maintainer decision)

Current `MILESTONES.md` M4 exit criteria are correct engineering choices
and should not be weakened. The proposal here is about **stated purpose**,
plus one candidate new criterion:

**Reframe the goal statement.** Current: "prove the pipeline end-to-end on
a narrow target." Proposed replacement: "prove that the source → IR →
target traceability and guarantee-preservation pipeline holds under a real
target — not to prove AION can competently emit Rego." The target
(OPA/Rego or a Python policy module) remains the right pragmatic choice for
cost reasons; the doc should say explicitly that the target is chosen for
its cheapness to implement against, not as a claim that AION improves on
Rego/Cedar for authorization specifically.

**Candidate new exit criterion (PROPOSED, requires a decision-log entry if
adopted):** M4's generated artifact must exercise at least one non-`ALLOW`/
`DENY` construct — an `INVARIANT` or `CONSTRAINT` — end to end, not only
policy edges. Rationale: without this, M4 only ever proves "AION compiles
RBAC policy to Rego," which does nothing to support the §1.1 differentiation
bet and everything to reinforce the "why not just write Rego" objection.
This is deliberately framed as a candidate, not a mandate — a human
maintainer should weigh it against M4's existing scope discipline before
it's added.

**Do not add:** a second code-generation target at M4. `MILESTONES.md`
already correctly warns against breadth-before-depth here (M4 note on one
target chosen and recorded). This proposal doesn't reopen that — it asks
for depth within the existing target, not a second target.

---

## 4. What this document does not resolve

- It does not prove the AI-generation thesis (§1.4) — that requires M3
  and M4 to actually exist.
- It does not resolve open design question 7 (data/deployment/infra
  modeling), which the §1.1 bet ultimately depends on.
- It does not address developer-experience, tooling, or community factors
  that determine real-world adoption independent of language design —
  those are real and unaddressed, and no positioning document changes them.

This document's only job is to make sure the project's differentiation
claim is falsifiable and stated, instead of assumed and silent.
