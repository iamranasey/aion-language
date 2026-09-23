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

- Keywords are uppercase and reserved: `SYSTEM ENTITY ACTION RULE ALLOW DENY
  REQUIRE GUARANTEE CONSTRAINT INVARIANT TEST`.
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
invariant-pred = "after" , ident , "," , ident , "." , ident , "unchanged" ;
               (* after <ACTION>, <Entity>.<field> unchanged *)

(* ---- Constraints ---- *)
constraint-decl = "CONSTRAINT" , ident , comparison ;
comparison      = ident , "." , ident , rel-op , value ;
rel-op          = "==" | "!=" | "<" | "<=" | ">" | ">=" ;
value           = integer | "true" | "false" | string ;

(* ---- Guarantees ---- *)
guarantee-decl  = "GUARANTEE" , guarantee-class , ident , guarantee-pred ;
guarantee-class = "static" | "monitor" | "proof" ;

(* ---- Tests ---- *)
test-decl   = "TEST" , ident , scenario , "EXPECT" , expectation ;
scenario    = subject , ("attempts" | "performs") , ident ,
              "(" , [ ident-list ] , ")" ;
expectation = ("ALLOWED" | "DENIED") , [ "," , "AUDIT" ] ;
```

### Guarantee predicates (v0.1 catalog)

Guarantees do not take arbitrary expressions in v0.1. They are boolean
combinations (`and`, `or`, `not`, parentheses) of a fixed set of decidable
predicates over the semantic model:

| Predicate | Meaning |
| --- | --- |
| `every ALLOW/DENY edge targets a declared ACTION` | No dangling policy edge |
| `no (subject, action) pair appears in both ALLOW and DENY` | Policy is conflict-free |
| `every REQUIRE obligation targets a declared ACTION` | No dangling obligation |
| `every declared ACTION is reachable by some ALLOW edge` | No dead actions |
| `every INVARIANT and CONSTRAINT references declared fields` | No dangling state predicate |

Restricting guarantees to a predicate catalog keeps them **decidable by
construction** — the semantic model is finite, each predicate is a total
function over it, and evaluation terminates.

---

## 3. Decision Log

Decisions are numbered and permanent. A decision may only be replaced by a new
numbered entry that references the one it supersedes.

- **D1 — Fail-closed default.** Absence of an `ALLOW` edge means denial. A
  request is permitted only if an `ALLOW` edge matches and no `DENY` edge
  matches. There is no implicit allow.
- **D2 — Conflicts are compile errors.** If the same `(subject, action)` pair
  appears in both `ALLOW` and `DENY` within a `RULE`, compilation fails. `DENY`
  is an explicit override for pairs that would otherwise be allowed by a
  broader subject (e.g., `Staff` allowed, `Staff[Finance]` denied); it is not a
  tie-breaker. Resolution rule: a `DENY` on `Entity[Role]` overrides an `ALLOW`
  on the bare `Entity` *only* when the pair differs after role expansion;
  exact-pair duplication is an error. This is checked statically.
- **D3 — No dangling references.** Policy edges, obligations, invariant fields,
  and constraint fields must name declared `ACTION`s, entities, roles, and
  fields. Undeclared names are compile errors, not warnings.
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
- **D7 — TEST blocks are executable.** A `TEST` is a conformance scenario
  evaluated against the *policy model* (subjects, actions, ALLOW/DENY/REQUIRE),
  not against generated code. Decision procedure for `subject attempts action`:
  1. If a `DENY` edge matches the pair → `DENIED`.
  2. Else if an `ALLOW` edge matches → `ALLOWED` (plus `AUDIT` if a `REQUIRE`
     obligation covers the action).
  3. Else → `DENIED` (D1). `attempts` and `performs` are syntactic synonyms;
  they exist so tests read naturally for both negative and positive cases.
- **D8 — Expressions are catalogs, not free math.** Invariants and constraints
  use fixed predicate shapes; guarantees use the predicate catalog of §2. This
  trades expressiveness for decidability and honest claims. Free-form
  expressions may be proposed later under a new decision entry.
- **D9 — Deterministic grammar.** The grammar is LL(1): a declaration's kind is
  determined by its leading keyword, and no semantic information is needed to
  parse. The parser never invokes an LLM or any non-deterministic component.
- **D10 — Versioning of this document.** Any grammar change merged without a
  decision-log entry is invalid and should be rejected in review.

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
