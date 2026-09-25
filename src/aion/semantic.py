"""Semantic model and decision procedure for AION v0.1 (M2).

This module turns a position-free ``Spec`` (``ast_nodes.py``) into a
``SemanticModel``: symbol tables for entities, roles, fields, actions and rules,
plus the policy graph (ALLOW/DENY/REQUIRE edges) needed to *decide* requests and
*evaluate* the reserved guarantee atoms.

It implements the normative semantics of ``GRAMMAR.md`` §3:

  - **D1**  fail-closed default (no matching ALLOW ⇒ DENIED).
  - **D2**  exact-pair ALLOW∩DENY at the same specificity is a conflict.
  - **D7**  the ``TEST`` decision procedure.
  - **D11** subject specificity: ``Entity[Role]`` = 2, bare ``Entity`` = 1; the
            highest-specificity matching edge wins, ALLOW or DENY alike.

Nothing here *reports* diagnostics — it only answers semantic questions
(``decide``, ``conflicts``, ``atom_*``, ``eval_pred``). ``validate.py`` drives it
and turns the answers into ``Diagnostic`` records. Keeping the two apart means
the decision procedure is unit-testable in isolation.

No LLM or non-determinism (D9): every method is a total function over the finite
semantic model, so evaluation terminates.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple

from . import ast_nodes as ast
from .diagnostics import (
    DUPLICATE_ACTION,
    DUPLICATE_ENTITY,
    DUPLICATE_FIELD,
    DUPLICATE_ROLE,
    DUPLICATE_RULE,
    Diagnostic,
)
from .lexer import GUARANTEE_ATOMS

# Decision outcomes (D7). ``CONFLICT`` is not a runtime outcome — it signals the
# exact-pair conflict of D2 that ``validate`` reports as a compile error.
ALLOWED = "ALLOWED"
DENIED = "DENIED"
CONFLICT = "CONFLICT"


@dataclass
class EntitySym:
    """A declared ``ENTITY``: its roles (D4) and field name → type map."""

    name: str
    roles: List[str] = field(default_factory=list)
    fields: Dict[str, str] = field(default_factory=dict)


@dataclass
class ActionSym:
    """A declared ``ACTION``: positional params (first is the actor, D15) and
    the optional result entity."""

    name: str
    params: List[ast.Param]
    result: Optional[str]


@dataclass
class Decision:
    """Outcome of the D7 decision procedure for one (subject, action) request."""

    outcome: str  # ALLOWED | DENIED | CONFLICT
    audit: bool = False


@dataclass
class SemanticModel:
    """Symbol tables + policy graph for one spec.

    Build with :meth:`SemanticModel.build`, which also returns the duplicate-name
    diagnostics it detected while indexing (a repeated declaration is a defect,
    but indexing continues so later checks still have a symbol to resolve
    against — the first declaration wins).
    """

    system_name: str
    entities: Dict[str, EntitySym] = field(default_factory=dict)
    actions: Dict[str, ActionSym] = field(default_factory=dict)
    rules: Dict[str, ast.RuleDecl] = field(default_factory=dict)

    # Policy edges, each tagged with the rule that declared it so diagnostics can
    # point at ``RULE <name>``.
    allow_edges: List[Tuple[str, ast.Edge]] = field(default_factory=list)
    deny_edges: List[Tuple[str, ast.Edge]] = field(default_factory=list)
    require_edges: List[Tuple[str, ast.ObligationEdge]] = field(default_factory=list)
    audited_actions: Set[str] = field(default_factory=set)

    invariants: List[ast.InvariantDecl] = field(default_factory=list)
    constraints: List[ast.ConstraintDecl] = field(default_factory=list)
    guarantees: List[ast.GuaranteeDecl] = field(default_factory=list)
    tests: List[ast.TestDecl] = field(default_factory=list)

    # --- construction ----------------------------------------------------
    @classmethod
    def build(cls, spec: ast.Spec) -> Tuple["SemanticModel", List[Diagnostic]]:
        model = cls(system_name=spec.name)
        dups: List[Diagnostic] = []

        for decl in spec.declarations:
            if isinstance(decl, ast.EntityDecl):
                model._index_entity(decl, dups)
            elif isinstance(decl, ast.ActionDecl):
                model._index_action(decl, dups)
            elif isinstance(decl, ast.RuleDecl):
                model._index_rule(decl, dups)
            elif isinstance(decl, ast.InvariantDecl):
                model.invariants.append(decl)
            elif isinstance(decl, ast.ConstraintDecl):
                model.constraints.append(decl)
            elif isinstance(decl, ast.GuaranteeDecl):
                model.guarantees.append(decl)
            elif isinstance(decl, ast.TestDecl):
                model.tests.append(decl)

        return model, dups

    def _index_entity(self, decl: ast.EntityDecl, dups: List[Diagnostic]) -> None:
        if decl.name in self.entities:
            dups.append(Diagnostic(
                DUPLICATE_ENTITY, f"ENTITY {decl.name}",
                f"entity '{decl.name}' is declared more than once",
            ))
            return  # first declaration wins
        sym = EntitySym(name=decl.name)
        for role in decl.roles or []:
            if role in sym.roles:
                dups.append(Diagnostic(
                    DUPLICATE_ROLE, f"ENTITY {decl.name}",
                    f"role '{role}' is declared twice on entity '{decl.name}'",
                ))
                continue
            sym.roles.append(role)
        for f in decl.fields or []:
            if f.name in sym.fields:
                dups.append(Diagnostic(
                    DUPLICATE_FIELD, f"ENTITY {decl.name}",
                    f"field '{f.name}' is declared twice on entity '{decl.name}'",
                ))
                continue
            sym.fields[f.name] = f.type
        self.entities[decl.name] = sym

    def _index_action(self, decl: ast.ActionDecl, dups: List[Diagnostic]) -> None:
        if decl.name in self.actions:
            dups.append(Diagnostic(
                DUPLICATE_ACTION, f"ACTION {decl.name}",
                f"action '{decl.name}' is declared more than once",
            ))
            return
        self.actions[decl.name] = ActionSym(
            name=decl.name, params=list(decl.params), result=decl.result,
        )

    def _index_rule(self, decl: ast.RuleDecl, dups: List[Diagnostic]) -> None:
        if decl.name in self.rules:
            dups.append(Diagnostic(
                DUPLICATE_RULE, f"RULE {decl.name}",
                f"rule '{decl.name}' is declared more than once",
            ))
            return
        self.rules[decl.name] = decl
        for block in decl.blocks:
            if isinstance(block, ast.AllowBlock):
                for edge in block.edges:
                    self.allow_edges.append((decl.name, edge))
            elif isinstance(block, ast.DenyBlock):
                for edge in block.edges:
                    self.deny_edges.append((decl.name, edge))
            elif isinstance(block, ast.RequireBlock):
                for ob in block.edges:
                    self.require_edges.append((decl.name, ob))
                    if ob.obligation == "AUDIT":
                        self.audited_actions.add(ob.action)

    # --- subject matching and specificity (D7, D11) ----------------------
    @staticmethod
    def _specificity(subject: ast.Subject) -> int:
        return 2 if subject.role is not None else 1

    @staticmethod
    def _matches(edge_subject: ast.Subject, request: ast.Subject) -> bool:
        """Does ``edge_subject`` apply to ``request``?

        D7: a request ``Entity[Role]`` matches an edge ``Entity[Role]`` (spec 2)
        or a bare ``Entity`` (spec 1); a request bare ``Entity`` matches only a
        bare ``Entity`` edge. Entity must always be identical (case-sensitive).
        """
        if edge_subject.entity != request.entity:
            return False
        # A bare edge (role None) matches any role of that entity; a role-qualified
        # edge matches only the identical role.
        return edge_subject.role is None or edge_subject.role == request.role

    def decide(self, request: ast.Subject, action: str) -> Decision:
        """The D7 decision procedure for ``request attempts action``."""
        matching: List[Tuple[int, str]] = []  # (specificity, kind)
        for _rule, edge in self.allow_edges:
            if edge.action == action and self._matches(edge.subject, request):
                matching.append((self._specificity(edge.subject), ALLOWED))
        for _rule, edge in self.deny_edges:
            if edge.action == action and self._matches(edge.subject, request):
                matching.append((self._specificity(edge.subject), DENIED))

        if not matching:
            return Decision(DENIED, audit=False)  # D1 fail-closed

        top = max(spec for spec, _ in matching)
        kinds = {kind for spec, kind in matching if spec == top}
        if ALLOWED in kinds and DENIED in kinds:
            # Equal-specificity ALLOW+DENY on the identical pair (D2/D11).
            return Decision(CONFLICT, audit=False)
        if DENIED in kinds:
            return Decision(DENIED, audit=False)
        return Decision(ALLOWED, audit=action in self.audited_actions)

    # --- static analyses -------------------------------------------------
    def all_possible_subjects(self) -> List[ast.Subject]:
        """Every subject a request could name: each entity bare and each
        entity[role]. Used by liveness (D11: an ALLOW shadowed for *all*
        possible subjects is not effective)."""
        subjects: List[ast.Subject] = []
        for name, sym in self.entities.items():
            subjects.append(ast.Subject(entity=name, role=None))
            for role in sym.roles:
                subjects.append(ast.Subject(entity=name, role=role))
        return subjects

    def action_is_live(self, action: str) -> bool:
        """True if some possible subject is ALLOWED to perform ``action``."""
        return any(
            self.decide(subj, action).outcome == ALLOWED
            for subj in self.all_possible_subjects()
        )

    def conflicts(self) -> List[Tuple[str, str, Optional[str], str]]:
        """Exact-pair ALLOW∩DENY within a single rule (D2).

        Returns ``(rule_name, entity, role, action)`` for every identical
        ``(subject, action)`` pair that appears in both an ALLOW and a DENY of
        the same rule. Identical ``(entity, role)`` implies identical
        specificity, so this is exactly the same-specificity conflict of D2/D11.
        """
        found: List[Tuple[str, str, Optional[str], str]] = []
        for rule_name, rule in self.rules.items():
            allows: Set[Tuple[str, Optional[str], str]] = set()
            denies: Set[Tuple[str, Optional[str], str]] = set()
            for block in rule.blocks:
                if isinstance(block, ast.AllowBlock):
                    for e in block.edges:
                        allows.add((e.subject.entity, e.subject.role, e.action))
                elif isinstance(block, ast.DenyBlock):
                    for e in block.edges:
                        denies.add((e.subject.entity, e.subject.role, e.action))
            for entity, role, action in sorted(allows & denies):
                found.append((rule_name, entity, role, action))
        return found

    # --- guarantee atoms (GRAMMAR.md §2 catalog, D14) --------------------
    def atom_no_dangling_edges(self) -> bool:
        """Every ALLOW/DENY edge targets a declared ACTION."""
        return all(
            edge.action in self.actions
            for _rule, edge in self.allow_edges + self.deny_edges
        )

    def atom_conflict_free(self) -> bool:
        """No exact-pair ALLOW∩DENY at the same specificity (D2, D11)."""
        return not self.conflicts()

    def atom_no_dangling_obligations(self) -> bool:
        """Every REQUIRE obligation targets a declared ACTION."""
        return all(ob.action in self.actions for _rule, ob in self.require_edges)

    def atom_no_dead_actions(self) -> bool:
        """Every declared ACTION is reachable by some effective ALLOW (D11)."""
        return all(self.action_is_live(name) for name in self.actions)

    def atom_no_dangling_state_refs(self) -> bool:
        """Every INVARIANT/CONSTRAINT field-ref names a declared entity+field
        (D12, D13)."""
        refs: List[ast.FieldRef] = [inv.ref for inv in self.invariants]
        for con in self.constraints:
            refs.append(con.left)
            if isinstance(con.right, ast.FieldRef):
                refs.append(con.right)
        return all(self._field_ref_declared(r) for r in refs)

    def _field_ref_declared(self, ref: ast.FieldRef) -> bool:
        sym = self.entities.get(ref.entity)
        return sym is not None and ref.field in sym.fields

    _ATOM_METHODS = {
        "NO_DANGLING_EDGES": atom_no_dangling_edges,
        "CONFLICT_FREE": atom_conflict_free,
        "NO_DANGLING_OBLIGATIONS": atom_no_dangling_obligations,
        "NO_DEAD_ACTIONS": atom_no_dead_actions,
        "NO_DANGLING_STATE_REFS": atom_no_dangling_state_refs,
    }

    def eval_atom(self, name: str) -> bool:
        """Evaluate one reserved atom. Fail-closed (D1): an atom outside the
        catalog cannot be proven true, so it is False. (The parser restricts
        atoms to ``GUARANTEE_ATOMS``, so this branch is defensive.)"""
        method = self._ATOM_METHODS.get(name)
        if method is None or name not in GUARANTEE_ATOMS:
            return False
        return method(self)

    def eval_pred(self, expr: ast.PredExpr) -> bool:
        """Fold a ``guarantee-pred`` left-to-right with no and/or precedence
        (GRAMMAR.md §2: ``pred-expr = pred-term { ("and"|"or") pred-term }``)."""
        result = self.eval_term(expr.terms[0])
        for i, op in enumerate(expr.ops):
            rhs = self.eval_term(expr.terms[i + 1])
            result = (result and rhs) if op == "and" else (result or rhs)
        return result

    def eval_term(self, term: ast.PredTerm) -> bool:
        value = self.eval_operand(term.operand)
        return (not value) if term.negated else value

    def eval_operand(self, operand) -> bool:
        if isinstance(operand, ast.PredAtom):
            return self.eval_atom(operand.name)
        if isinstance(operand, ast.PredExpr):
            return self.eval_pred(operand)
        raise TypeError(f"unexpected predicate operand: {operand!r}")
