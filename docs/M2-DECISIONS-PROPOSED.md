# M2 semantic decisions — adoption record

Status: **ADOPTED by maintainer instruction on 2026-10-01.**
A–D are recorded as GRAMMAR D16–D19. E's design gate and scope boundary are
recorded as D20; no concrete runtime state model is adopted. The filename is
retained for existing links. The original options and recommendations below
are historical rationale; GRAMMAR is authoritative. M2 checks are implemented and locally tested on the PR branch.

## A. Denial and specificity (clarification of D1/D11)

Question: does D1's "no DENY edge matches" override D11's explicit example?
Options: unconditional deny precedence; or D11 specificity precedence.
Recommendation: explicitly mark D1's unconditional-deny sentence superseded by
D11. A matching higher-specificity ALLOW wins over a bare DENY; equal-specificity
ALLOW/DENY conflicts are compile errors. Absence of an effective ALLOW denies.
Acceptance witnesses: bare deny plus role allow; bare allow plus role deny;
no matching edge; identical conflicting edges. Preserve the existing role-override example.

## B. Composition across RULE blocks

Question: D2 names conflicts within a RULE, while D7 gathers all matching edges.
Options: globally composed rules; independent named policies requiring explicit
selection; or ordered rules. Selection/order would need additional language design.
Recommendation: treat RULE names as organizational groups. Merge all policy edges
for validation and evaluation. An identical ALLOW/DENY pair anywhere in the model
is invalid, even if no TEST exercises it. Duplicate same-effect edges are idempotent;
duplicate REQUIRE edges require one audit obligation, not repeated audit events.
Acceptance witnesses: split a policy over two RULEs without changing outcomes;
cross-RULE conflicting pair rejects; reordering declarations preserves outcomes.

## C. Names and duplicate declarations

Question: what names may collide and what happens to duplicate declarations?
Options: one global namespace; separate namespaces by declaration category.
Recommendation: separate namespaces for entities, actions, rules, invariants,
constraints, guarantees, and tests; unique names within each. Roles and fields
are unique within their entity, in separate namespaces. Duplicate declarations
are errors, never implicit replacement. Resolve forward references after collecting
declarations. Role references require an existing role on the referenced entity.
Acceptance witnesses: duplicate entity rejects; field name shared by different
entities succeeds; forward action reference resolves; unknown role rejects.

## D. Comparison types and TEST bindings

Question: which primitive comparisons are well-typed, and how do zero-parameter
actions and role-constrained arguments behave in TESTs?
Options: implicit coercions or strict types; implicit actors or explicit arity.
Recommendation: no coercions. Equality/inequality require matching primitive
types; ordering requires two ints. Preserve zero-parameter ACTION syntax, but
reject TEST invocation of such an action under D15's subject-plus-args rule.
Retain D15's policy-driven subject authorization. For remaining arguments, require
the declared entity; reject role-constrained non-actor TEST parameters until the
language specifies how the bare argument identifier supplies a role. Do not infer it.
Acceptance witnesses: bool/int comparison rejects; int/int ordering succeeds;
zero-parameter declaration parses but TEST invocation rejects; actor type mismatch
alone does not decide authorization. The adopted role-argument restriction narrows semantic acceptance without
changing parsing (D19).

## E. State and monitor semantics (design gate for M4)

Question: which concrete instances and states do entity-level field references denote?
Options: bind fields through an explicit execution context; or introduce instance
variables and quantifiers. Recommendation: design a bounded execution-context
contract first, including actor/arguments/result, instance identity, before/after
snapshots, comparison timing, failed actions, and audit delivery failure behavior.
Under D20, M2 claims only structural/type validation for state constructs,
not enforcement of their values or preservation during execution. A target must
reject unsupported invariants, constraints, monitors, and proof requirements rather
than silently discard them. The existing M4 non-policy demonstration proposal stays
proposed; no new target capability is claimed here.

## Approval and implementation sequence

A–D are recorded in D16–D19 and the state-design gate in D20. SPEC, GLOSSARY,
and conformance expectations are synchronized with the M2 implementation. Symbol
tables, reference/type diagnostics, global conflicts, predicates, and TEST evaluation
are implemented. Published regression vectors live in tests/fixtures/m2-conformance.json;
additional decision coverage lives in tests/test_m2_decisions.py. E needs a separate design review before a state-aware target is implemented.
