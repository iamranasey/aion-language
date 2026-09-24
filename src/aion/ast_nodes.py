"""AST node types for AION v0.1 (GRAMMAR.md §2).

The tree is a structural mirror of the EBNF, deliberately free of source
positions so that `parse -> print -> re-parse` equality (the M1 round-trip exit
criterion) is a plain structural comparison. The shapes are language-agnostic so
that M3 IR lowering is a mapping, not a redesign.

M1 is syntactic only: nothing here performs or records semantic validation
(dangling references, conflicts, `proof` rejection, TEST arity). Those are M2.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Union


# --- Entities ---
@dataclass
class Field:
    name: str
    type: str  # "int" | "bool" | "string"


@dataclass
class EntityDecl:
    name: str
    roles: Union[List[str], None] = None
    fields: Union[List[Field], None] = None


# --- Actions ---
@dataclass
class Param:
    entity: str
    role: Union[str, None] = None


@dataclass
class ActionDecl:
    name: str
    params: List[Param]
    result: Union[str, None] = None


# --- Rules and policy ---
@dataclass
class Subject:
    entity: str
    role: Union[str, None] = None


@dataclass
class Edge:
    subject: Subject
    action: str


@dataclass
class ObligationEdge:
    action: str
    obligation: str  # "AUDIT" is the only v0.1 obligation (D6)


@dataclass
class AllowBlock:
    edges: List[Edge]


@dataclass
class DenyBlock:
    edges: List[Edge]


@dataclass
class RequireBlock:
    edges: List[ObligationEdge]


PolicyBlock = Union[AllowBlock, DenyBlock, RequireBlock]


@dataclass
class RuleDecl:
    name: str
    blocks: List[PolicyBlock]


# --- Invariants and constraints ---
@dataclass
class FieldRef:
    entity: str
    field: str


@dataclass
class InvariantDecl:
    name: str
    action: str
    ref: FieldRef


@dataclass
class Literal:
    value: Union[int, bool, str]


@dataclass
class ConstraintDecl:
    name: str
    left: FieldRef
    op: str  # "==" | "!=" | "<" | "<=" | ">" | ">="
    right: Union[FieldRef, Literal]


# --- Guarantees ---
@dataclass
class PredAtom:
    name: str


@dataclass
class PredExpr:
    terms: List["PredTerm"]
    ops: List[str]  # "and" | "or"; len(ops) == len(terms) - 1


@dataclass
class PredTerm:
    negated: bool
    operand: Union[PredAtom, PredExpr]  # a PredExpr operand was parenthesized


@dataclass
class GuaranteeDecl:
    cls: str  # "static" | "monitor" | "proof"
    name: str
    pred: PredExpr


# --- Tests ---
@dataclass
class Scenario:
    subject: Subject
    verb: str  # "attempts" | "performs"
    action: str
    args: List[str]


@dataclass
class Expectation:
    result: str  # "ALLOWED" | "DENIED"
    audit: bool


@dataclass
class TestDecl:
    name: str
    scenario: Scenario
    expectation: Expectation


# --- Program ---
Declaration = Union[
    EntityDecl, ActionDecl, RuleDecl, InvariantDecl,
    ConstraintDecl, GuaranteeDecl, TestDecl,
]


@dataclass
class Spec:
    name: str
    declarations: List[Declaration]
