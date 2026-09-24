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

## 1. The four neighbors, assessed without flattery

### 1.1 Rego / Open Policy Agent, and Cedar (AWS)

**What they are:** mature, production-deployed policy languages purpose-built
for authorization decisions. Rego/OPA is widely used for admission control,
API authorization, and CI/CD gating. Cedar backs Amazon Verified
Permissions in production.

**Overlap with AION:** total, for the only example that currently exists.
`OrderService`'s `ALLOW`/`DENY` edges, role-scoped subjects
(`Staff[Finance]`), and `REQUIRE ... AUDIT` obligations are structurally an
authorization policy — the exact domain Rego and Cedar already solve, with
years of tooling, IDE support, and community behind them.

**Honest assessment:** for authorization policy alone, today, a team is
almost certainly better served writing Rego or Cedar directly. AION does
not currently out-compete them on their own ground, and the docs should not
imply otherwise. `MILESTONES.md`'s own M4 recommendation — targeting
OPA/Rego — makes the overlap explicit rather than coincidental, which
raises the stakes on answering this section, not lowers them.

**The actual bet, stated honestly:** AION is not trying to be a better
authorization DSL. It's trying to be a language where authorization is *one
slice* of a larger system-intent model — the same `ENTITY`/`ACTION` model
that declares `Order.total` and `Payment.amount` is meant to eventually
carry state invariants, business-rule constraints, and (per open question 7)
data and deployment shape, all under the same guarantee discipline. The
`OrderService` example only shows the authz slice because that's the only
slice with worked-out semantics so far (D1–D8 are almost entirely about
policy). This is a **falsifiable bet, currently unproven**: if the
non-authz constructs (`INVARIANT`, `CONSTRAINT`, and whatever eventually
answers open question 7) never get the same rigor as the policy semantics,
AION has no real claim over Rego/Cedar and should say so rather than
pretend otherwise. This is the single most important thing for the project
to prove or disprove early — see the M4 proposal in §3.

### 1.2 TLA+ / Alloy / Dafny

**What they are:** rigorous formal-specification and verification tools,
academically mature, with real proof-class guarantees available.

**Overlap with AION:** the `static` → `monitor` → `proof` guarantee-class
ladder in `GRAMMAR.md` §4 is explicitly reaching toward the same territory
these tools already occupy at the `proof` tier.

**Honest track record:** decades of maturity, still niche adoption. The
well-documented reason isn't that formal methods don't work — it's that (a)
the notation and mental model impose a steep learning curve most engineering
teams don't invest in, and (b) the spec is written and maintained *separately*
from the implementation, so the two drift apart over time with nothing
forcing them back into alignment. TLA+ can prove your spec correct; it
cannot prove your code still matches the spec six months later.

**The bet:** AION's traceability requirement (M4: every generated artifact
carries a source → IR → target mapping) is aimed specifically at failure
mode (b) — because the implementation is *generated from* the spec rather
than hand-maintained alongside it, the sync-rot problem that has capped
formal-methods adoption for decades doesn't have the same opportunity to
occur. This is a genuinely different approach to the adoption barrier, not
just a smaller/friendlier TLA+.

**Risk to flag honestly:** this bet only pays off if code generation (M4+)
produces output good enough to actually ship, not toy artifacts nobody
trusts. If generated code quality never clears that bar, the traceability
guarantee becomes moot — nobody adopts output they don't trust regardless
of how well-traced it is.

### 1.3 Gherkin / BDD

**What it is:** natural-language-adjacent scenario syntax
(`Given/When/Then`) backing hand-written step-definition glue code.

**Overlap:** AION's `TEST` blocks read in a similarly natural style
(`Staff[Support] attempts refund(Payment) EXPECT DENIED`).

**Honest limit of Gherkin:** the language itself doesn't know what
"succeeds" or "fails" means — a human wrote untyped step-definition code
that decides that, and Gherkin has no way to check that the glue code
matches the scenario's intent.

**AION's actual difference — and this one is already true, not
aspirational:** a `TEST` block's `EXPECT` is evaluated by the D7 decision
procedure over the declared policy model, not by hand-written glue code. If
this is stated anywhere, it should be stated with confidence — of the four
comparisons in this document, this is the only one where AION already does
something the neighbor structurally cannot, today, without waiting on M3/M4.

### 1.4 The AI-generation angle — the least developed, most novel bet

None of the above were designed for a world where an AI model is expected
to write or maintain the implementation. This is the gap that's actually
unoccupied, and it deserves to be the lead thesis rather than a closing
footnote:

Today, if you hand an AI model a natural-language spec or a ticket and ask
it to implement a system, there is no mechanical way to check whether the
implementation honored the intent — you're back to code review by eyeball,
at exactly the moment AI-generated code volume is making eyeball review the
bottleneck.

**The differentiation claim AION can make that Rego, Cedar, TLA+, Alloy,
Dafny, and Gherkin cannot:** AION is not a better way for a human to write
policy or specs. It is a substrate an AI model can implement *against*,
where "did the AI get it right" is a **decidable question** — the same
`TEST` suite and guarantee predicates that validate the AION source are
re-run against whatever the AI generates, and a wrong implementation fails
mechanically instead of passing a plausible-looking review. `MILESTONES.md`
M5 already gates AI tooling behind exactly this ("every AI-generated
proposal ... passes deterministic validation before being presented as a
result") — the thesis has quietly already been designed into the milestone
plan. It just hasn't been stated as the project's central bet anywhere a
reader would find it.

**Honest status:** unproven, gated behind M3 and M4. The correct move now
is to state this as the thesis explicitly, and treat M4/M5 as the
milestones that either validate or falsify it — not to claim it as already
demonstrated.

---

## 2. What this means for positioning (proposed, not adopted)

If accepted, the lead differentiation statement for `README.md` /
`PHILOSOPHY.md` would read something like:

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
