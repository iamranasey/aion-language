# AION v0.1 — Grammar and Decision Log

This document is the working grammar for AION v0.1 and the decision log that
records *why* the grammar is shaped this way. Every design decision here is
binding for the v0.1 parser unless superseded by a later logged decision.

Status per `PHILOSOPHY.md`: **Specified**, not yet **Implemented**.

---

## 1. Lexical Rules

```ebnf
ident      = letter , { letter | digit | "_" } ;
letter     = "a".."z" | "A".."Z" ;
digit      = "0".."9" ;
integer    = [ "-" ] , digit , { digit } ;
string     = '"' , { any-character-except-'"' } , '"' ;
comment    = "#" , { any-character-except-newline } , newline ;
```

- Declaration keywords are uppercase and reserved: `SYSTEM ENTITY ACTION RULE
  ALLOW DENY REQUIRE GUARANTEE CONSTRAINT INVARIANT TEST`.
- Context keywords are reserved where they appear: `roles fields int bool
  string after unchanged and or not attempts performs EXPECT ALLOWED DENIED
  AUDIT static monitor proof`. `ident`s are case-sensitive, so a reserved word
  and an identifier that differ only in case are distinct tokens; a reserved
  word may not be reused as a declared name.
- Guarantee predicate atoms are uppercase and reserved (see the catalog in §2):
  `NO_DANGLING_EDGES CONFLICT_FREE NO_DANGLING_OBLIGATIONS NO_DEAD_ACTIONS
  NO_DANGLING_STATE_REFS`. They are single tokens; the punctuation and the word
  `and` that appeared inside the old English predicate phrases are gone, so an
  atom can never be confused with a boolean operator or a grouping parenthesis.
- Whitespace and newlines are insignificant. Declarations are recognized by
  their leading keyword (the grammar is LL(1)); no semicolons or braces.
- `#` starts a comment to end of line.

---

## 2. Syntax (EBNF)

```ebnf
(* ---- Program ---- *)
spec        = "SYSTEM" , ident , { declaration } ;
declaration = entity-decl | action-decl | rule-decl
            | invariant-decl | constraint-decl
            | guarantee-decl | test-decl ;

(* ---- Entities ---- *)
entity-decl  = "ENTITY" , ident ,
               [ "roles"  , ":" , "[" , ident-list , "]" ] ,
               [ "fields" , ":" , "[" , field-list , "]" ] ;
ident-list   = ident , { "," , ident } ;
field-list   = field , { "," , field } ;
field        = ident , ":" , primitive-type ;
primitive-type = "int" | "bool" | "string" ;

(* ---- Actions ---- *)
action-decl  = "ACTION" , ident , "(" , [ param-list ] , ")" ,
               [ "->" , ident ] ;        (* "->" ident = result entity *)
param-list   = param , { "," , param } ;
param        = ident , [ "[" , ident , "]" ] ;
                                          (* Entity, optionally role-constrained:
                                             Entity[Role] *)

(* ---- Rules and policy ---- *)
rule-decl     = "RULE" , ident , { policy-block } ;
policy-block  = allow-block | deny-block | require-block ;
allow-block   = "ALLOW"   , edge , { edge } ;
deny-block    = "DENY"    , edge , { edge } ;
require-block = "REQUIRE" , obligation-edge , { obligation-edge } ;
edge          = subject , "->" , ident ;  (* ident must name an ACTION *)
obligation-edge = ident , "->" , obligation ;
subject       = ident , [ "[" , ident , "]" ] ;  (* Entity or Entity[Role] *)
obligation    = "AUDIT" ;

(* ---- Invariants ---- *)
invariant-decl = "INVARIANT" , ident , invariant-pred ;
invariant-pred = "after" , ident , "," , field-ref , "unchanged" ;
               (* after <ACTION>, <Entity>.<field> unchanged *)

(* ---- Constraints ---- *)
constraint-decl = "CONSTRAINT" , ident , comparison ;
comparison      = field-ref , rel-op , ( field-ref | value ) ;
field-ref       = ident , "." , ident ;  (* <Entity>.<field>; both must be
                                            declared, exact case — see D12/D13 *)
rel-op          = "==" | "!=" | "<" | "<=" | ">" | ">=" ;
value           = integer | "true" | "false" | string ;

(* ---- Guarantees ---- *)
guarantee-decl  = "GUARANTEE" , guarantee-class , ident , guarantee-pred ;
guarantee-class = "static" | "monitor" | "proof" ;
guarantee-pred  = pred-expr ;
pred-expr       = pred-term , { ( "and" | "or" ) , pred-term } ;
pred-term       = [ "not" ] , ( pred-atom | "(" , pred-expr , ")" ) ;
pred-atom       = "NO_DANGLING_EDGES" | "CONFLICT_FREE"
                | "NO_DANGLING_OBLIGATIONS" | "NO_DEAD_ACTIONS"
                | "NO_DANGLING_STATE_REFS" ;

(* ---- Tests ---- *)
test-decl   = "TEST" , ident , scenario , "EXPECT" , expectation ;
scenario    = subject , ("attempts" | "performs") , ident ,
              "(" , [ ident-list ] , ")" ;
expectation = ("ALLOWED" | "DENIED") , [ "," , "AUDIT" ] ;
```

### Guarantee predicates (v0.1 catalog)

Guarantees do not take arbitrary expressions in v0.1. A `guarantee-pred` is a
boolean combination (`and`, `or`, `not`, parentheses) of a fixed set of reserved
predicate **atoms** over the semantic model. Each atom is a single uppercase
token, so the parser never has to distinguish predicate prose from operators:

| Atom | Meaning |
| --- | --- |
| `NO_DANGLING_EDGES` | Every `ALLOW`/`DENY` edge targets a declared `ACTION` |
| `CONFLICT_FREE` | No `(subject, action)` pair appears in both `ALLOW` and `DENY` at the same specificity (D2, D11) |
| `NO_DANGLING_OBLIGATIONS` | Every `REQUIRE` obligation targets a declared `ACTION` |
| `NO_DEAD_ACTIONS` | Every declared `ACTION` is reachable by some effective `ALLOW` (D11) |
| `NO_DANGLING_STATE_REFS` | Every `INVARIANT` and `CONSTRAINT` field-ref names a declared entity and field (D12, D13) |

Example: `GUARANTEE static well_formed_policy NO_DANGLING_EDGES and CONFLICT_FREE`.

Restricting guarantees to a predicate catalog keeps them **decidable by
construction** — the semantic model is finite, each atom is a total function
over it, and evaluation terminates.

---

## 3. Decision Log

Decisions are numbered and permanent. A decision may only be replaced by a new
numbered entry that references the one it supersedes.

- **D1 — Fail-closed default.** Absence of an `ALLOW` edge means denial. A
  request is permitted only if an `ALLOW` edge matches and no `DENY` edge
  matches. There is no implicit allow.
- **D2 — Conflicts are compile errors (superseded in part by D11).** A conflict
  is an *exact* `(subject, action)` pair that appears in both `ALLOW` and `DENY`
  within a `RULE` at the *same specificity* (D11); compilation fails on such a
  pair. A `DENY` whose subject differs from the `ALLOW` subject — e.g. a bare
  `Entity` deny against a role-qualified `Entity[Role]` allow, or vice versa —
  is **not** a conflict; it is resolved deterministically by the specificity
  ordering in D11. This entry replaces the earlier "DENY overrides ALLOW only
  when the pair differs after role expansion" wording, which left the
  broad-DENY / narrow-ALLOW direction undefined.
- **D3 — No dangling references.** Policy edges, obligations, invariant
  field-refs, and constraint field-refs must name declared `ACTION`s, entities,
  roles, and fields. Undeclared names are compile errors, not warnings.
- **D4 — Roles and fields are declared, not inferred.** `roles:` and `fields:`
  are optional entity attributes. Referencing an undeclared role or field is a
  compile error (D3).
- **D5 — GUARANTEE has three classes.** `static` (checked at compile time over
  the semantic model; failure is a compile error), `monitor` (checked at
  runtime against execution traces; the compiler must emit instrumentation),
  and `proof` (requires a verification backend; **unsupported in v0.1** — parsed
  for forward compatibility, but validation must reject it from the stable
  core with an explicit "unsupported" diagnostic). See §4.
- **D6 — REQUIRE attaches obligations to actions.** `REQUIRE <action> -> AUDIT`
  means every permitted execution of `<action>` must produce an audit record.
  Enforcement path: static check that the obligation is wired through the IR,
  and target-level check that generated code emits the audit event. `AUDIT` is
  the only obligation in v0.1.
- **D7 — TEST blocks are executable (decision procedure updated by D11).** A
  `TEST` is a conformance scenario evaluated against the *policy model*
  (subjects, actions, ALLOW/DENY/REQUIRE), not against generated code. Decision
  procedure for `subject attempts action`:
  1. Gather every `ALLOW`/`DENY` edge whose subject *matches* the request
     subject and whose action is `action`. A request `Entity[Role]` matches an
     edge subject `Entity[Role]` (specificity 2) or bare `Entity`
     (specificity 1); a request bare `Entity` matches only bare `Entity`.
  2. If no edge matches → `DENIED` (D1, fail-closed).
  3. Otherwise pick the matching edge(s) of **highest specificity** (D11). If
     that set contains both an `ALLOW` and a `DENY`, it is an exact-pair
     conflict → compile error (D2), not a runtime outcome.
  4. If the highest-specificity edge is `DENY` → `DENIED`; if `ALLOW` →
     `ALLOWED` (plus `AUDIT` if a `REQUIRE` obligation covers the action).
  `attempts` and `performs` are syntactic synonyms; they exist so tests read
  naturally for both negative and positive cases.
- **D8 — Expressions are catalogs, not free math.** Invariants and constraints
  use fixed predicate shapes; guarantees use the predicate catalog of §2. This
  trades expressiveness for decidability and honest claims. Free-form
  expressions may be proposed later under a new decision entry.
- **D9 — Deterministic grammar.** The grammar is LL(1): a declaration's kind is
  determined by its leading keyword, and no semantic information is needed to
  parse. The parser never invokes an LLM or any non-deterministic component.
- **D10 — Versioning of this document.** Any grammar change merged without a
  decision-log entry is invalid and should be rejected in review.
- **D11 — Subject specificity resolves ALLOW vs DENY.** A role-qualified
  subject `Entity[Role]` has specificity 2; a bare `Entity` has specificity 1.
  When both an `ALLOW` and a `DENY` match a request, the edge with the *higher
  specificity* wins, regardless of whether it is `ALLOW` or `DENY`. Thus
  `ALLOW User[Admin] -> archive` beats `DENY User -> archive` for an Admin,
  while the same `DENY User -> archive` still denies every non-Admin `User`.
  Equal-specificity `ALLOW`+`DENY` on the identical pair is the exact-pair
  conflict of D2 (compile error). An `ALLOW` edge that is shadowed for *all*
  possible request subjects by a higher-specificity `DENY` is **not** effective
  and does not satisfy `NO_DEAD_ACTIONS`. This removes the D2/D7 ambiguity for
  the broad-DENY / narrow-ALLOW direction the v0.1 examples rely on.
- **D12 — Field references are case-sensitive and use the declared name.** A
  `field-ref` is `<Entity>.<field>` where `<Entity>` is the exact declared
  entity identifier and `<field>` is a field declared on it. There is no
  implicit lower-casing, pluralization, or aliasing: `payment.amount` does not
  refer to `ENTITY Payment`, and is a dangling reference (D3). Invariants and
  constraints use the same `field-ref` shape and the same casing rule.
- **D13 — Constraint operands are entity fields, not action results.** Both
  sides of a `comparison` are `field-ref`s (or a `field-ref` and a literal
  `value`). An `ACTION` name is never a valid operand. If a value produced by an
  action must be constrained, model it as a **result entity**: give the action a
  `-> ResultEntity` return and declare the carried fields on that entity, then
  constrain `ResultEntity.field`. (This is why the normative `refund` example
  declares a `Refund` entity rather than writing `refund.amount`.)
- **D14 — Guarantee predicates are reserved atoms.** A `guarantee-pred` is a
  boolean combination of the reserved atoms cataloged in §2
  (`NO_DANGLING_EDGES`, `CONFLICT_FREE`, `NO_DANGLING_OBLIGATIONS`,
  `NO_DEAD_ACTIONS`, `NO_DANGLING_STATE_REFS`), not free English prose. This
  supersedes the earlier prose-phrase catalog, whose phrases embedded the
  operator token `and`, parentheses, and commas and were therefore not
  unambiguously tokenizable. Adding a new checkable property requires adding a
  new reserved atom under a further decision entry.

---

## 4. Guarantee Semantics

A guarantee is a triple **(class, name, predicate)**. The class determines what
"keeping the guarantee" means and what evidence exists:

| Class | Obligation | Evidence | Failure mode |
| --- | --- | --- | --- |
| `static` | Predicate must evaluate to true over the compile-time semantic model | Compile-time evaluation trace | Compile error |
| `monitor` | Predicate must hold over every execution trace | Runtime instrumentation emitted by the compiler; violations reported at runtime | Runtime violation report (generation must refuse to silently drop monitors) |
| `proof` | Predicate must hold over all reachable states | A proof from a verification backend | **v0.1: unsupported — parse-only, rejected from stable core (D5)** |

Strength ordering: `proof` > `static` > `monitor`. Documentation must never
present a stronger claim than the class supports — this operationalizes the
"Verified ≠ Proven" rule from `PHILOSOPHY.md`.

### Why the original `GUARANTEE unauthorized_access == 0` was invalid

1. **Undeclared variable.** `unauthorized_access` is never declared, so the
   expression has no defined meaning in the semantic model (violates D3).
2. **Class confusion.** "Zero unauthorized accesses" is a property of
   *executions*, not of the specification text. Under D5 it could only ever be
   a `monitor` or `proof` guarantee — yet the language offered no way to say
   which, making the claim un-falsifiable.

The replacement example in `SPEC.md` uses only `static` guarantees drawn from
the decidable catalog, so every guarantee in the example can actually be
checked by the v0.1 toolchain.

---

## 5. The Normative Example

See `SPEC.md` §4 (`OrderService`). It is the first conformance target for the
parser: the milestone M1 parser must accept it, and the milestone M2 test
runner must pass both of its `TEST` blocks.
