"""Static validator for AION v0.1 (M2).

``validate(spec)`` walks the semantic model in a fixed, deterministic order and
*collects* every applicable ``Diagnostic`` rather than failing on the first one
(``examples/README.md``: a negative spec "should report each applicable
diagnostic rather than silently accepting the specification"). The order is:

  1. duplicate declarations (found while indexing),
  2. ``ACTION`` parameter / result entity references (D3, D4),
  3. ``ALLOW`` / ``DENY`` edge subject + action references (D3, D4),
  4. ``REQUIRE`` obligation action references (D3),
  5. ``INVARIANT`` / ``CONSTRAINT`` state references (D3, D12, D13),
  6. exact-pair policy conflicts (D2, D11),
  7. ``GUARANTEE`` class + predicate evaluation (D5, D14),
  8. ``TEST`` scenarios via the D7/D15 decision procedure.

Each step resolves names against the symbol tables; an unresolved name is a
compile error, never a warning (D3). When a construct's *own* references dangle,
later checks that depend on them are skipped so a single root defect is not
reported several times over (e.g. a ``TEST`` whose action is undeclared reports
the dangling action once and is not also failed for arity or outcome).

No LLM or non-determinism (D9): this is a total function over the finite model.
"""

from __future__ import annotations

from typing import List, Optional

from . import ast_nodes as ast
from . import semantic
from .diagnostics import (
    CONFLICT,
    DANGLING_ACTION,
    DANGLING_ENTITY,
    DANGLING_FIELD,
    DANGLING_ROLE,
    GUARANTEE_FAILED,
    TEST_ARG_MISMATCH,
    TEST_ARITY,
    TEST_FAILED,
    UNSUPPORTED_PROOF,
    Diagnostic,
)


def validate(spec: ast.Spec) -> List[Diagnostic]:
    """Return every semantic defect in ``spec`` (empty list ⇒ spec is valid)."""
    model, diagnostics = semantic.SemanticModel.build(spec)

    _check_actions(model, diagnostics)
    _check_policy_edges(model, diagnostics)
    _check_obligations(model, diagnostics)
    _check_state_refs(model, diagnostics)
    _check_conflicts(model, diagnostics)
    _check_guarantees(model, diagnostics)
    _check_tests(model, diagnostics)

    return diagnostics


def validate_or_raise(spec: ast.Spec) -> None:
    """Convenience wrapper: raise ``AionSemanticError`` if ``spec`` is invalid."""
    from .diagnostics import AionSemanticError

    diagnostics = validate(spec)
    if diagnostics:
        raise AionSemanticError(diagnostics)


# --- individual checks ---------------------------------------------------
def _check_actions(model: semantic.SemanticModel, out: List[Diagnostic]) -> None:
    """Action parameter entities/roles and the result entity must be declared."""
    for name, sym in model.actions.items():
        where = f"ACTION {name}"
        for param in sym.params:
            _check_subject_entity_role(model, param.entity, param.role, where, out)
        if sym.result is not None and sym.result not in model.entities:
            out.append(Diagnostic(
                DANGLING_ENTITY, where,
                f"result entity '{sym.result}' is not declared",
            ))


def _check_policy_edges(model: semantic.SemanticModel, out: List[Diagnostic]) -> None:
    """ALLOW/DENY edge subjects and target actions must be declared (D3, D4)."""
    for rule_name, edge in model.allow_edges + model.deny_edges:
        where = f"RULE {rule_name}"
        _check_subject_entity_role(
            model, edge.subject.entity, edge.subject.role, where, out,
        )
        if edge.action not in model.actions:
            out.append(Diagnostic(
                DANGLING_ACTION, where,
                f"policy edge targets undeclared action '{edge.action}'",
            ))


def _check_obligations(model: semantic.SemanticModel, out: List[Diagnostic]) -> None:
    """REQUIRE obligations must target declared actions (D3, D6)."""
    for rule_name, ob in model.require_edges:
        if ob.action not in model.actions:
            out.append(Diagnostic(
                DANGLING_ACTION, f"RULE {rule_name}",
                f"obligation targets undeclared action '{ob.action}'",
            ))


def _check_state_refs(model: semantic.SemanticModel, out: List[Diagnostic]) -> None:
    """INVARIANT/CONSTRAINT field-refs and invariant actions must resolve
    (D3, D12, D13)."""
    for inv in model.invariants:
        where = f"INVARIANT {inv.name}"
        if inv.action not in model.actions:
            out.append(Diagnostic(
                DANGLING_ACTION, where,
                f"invariant references undeclared action '{inv.action}'",
            ))
        _check_field_ref(model, inv.ref, where, out)

    for con in model.constraints:
        where = f"CONSTRAINT {con.name}"
        _check_field_ref(model, con.left, where, out)
        if isinstance(con.right, ast.FieldRef):
            _check_field_ref(model, con.right, where, out)


def _check_conflicts(model: semantic.SemanticModel, out: List[Diagnostic]) -> None:
    """Exact-pair ALLOW∩DENY at the same specificity is a compile error (D2)."""
    for rule_name, entity, role, action in model.conflicts():
        subject = f"{entity}[{role}]" if role else entity
        out.append(Diagnostic(
            CONFLICT, f"RULE {rule_name}",
            f"'{subject} -> {action}' appears in both ALLOW and DENY "
            f"at the same specificity (exact-pair conflict)",
        ))


def _check_guarantees(model: semantic.SemanticModel, out: List[Diagnostic]) -> None:
    """D5: reject ``proof`` from the stable core; evaluate ``static`` predicates;
    ``monitor`` is accepted but not statically checked (it is a runtime
    obligation discharged by generated instrumentation)."""
    for g in model.guarantees:
        where = f"GUARANTEE {g.name}"
        if g.cls == "proof":
            out.append(Diagnostic(
                UNSUPPORTED_PROOF, where,
                "'proof'-class guarantees require a verification backend and are "
                "unsupported in v0.1 (D5); parsed for forward compatibility only",
            ))
            continue
        if g.cls == "static":
            if not model.eval_pred(g.pred):
                out.append(Diagnostic(
                    GUARANTEE_FAILED, where,
                    "static guarantee predicate evaluates to false over the "
                    "semantic model",
                ))
        # 'monitor': no static evaluation; nothing to report at compile time.


def _check_tests(model: semantic.SemanticModel, out: List[Diagnostic]) -> None:
    """D7/D15: resolve the scenario, check arity + argument binding, then run
    the decision procedure and compare to the stated expectation."""
    for test in model.tests:
        _check_one_test(model, test, out)


def _check_one_test(
    model: semantic.SemanticModel, test: ast.TestDecl, out: List[Diagnostic],
) -> None:
    where = f"TEST {test.name}"
    scen = test.scenario

    # 1. Subject must name a declared entity/role (D15). It need NOT be
    #    authorized — an unauthorized subject is how a DENIED test is written.
    subject_broken = _check_subject_entity_role(
        model, scen.subject.entity, scen.subject.role, where, out,
    )
    if subject_broken:
        return

    # 2. Action must be declared.
    action = model.actions.get(scen.action)
    if action is None:
        out.append(Diagnostic(
            DANGLING_ACTION, where,
            f"scenario performs undeclared action '{scen.action}'",
        ))
        return

    # 3. Arity: one subject (the actor) plus the argument list must equal the
    #    action's parameter count (D15).
    expected_args = len(action.params) - 1
    if len(scen.args) != expected_args:
        out.append(Diagnostic(
            TEST_ARITY, where,
            f"action '{action.name}' takes {len(action.params)} parameter(s) "
            f"(1 actor + {expected_args} argument(s)) but the scenario supplies "
            f"{len(scen.args)} argument(s)",
        ))
        return

    # 4. Each argument binds positionally to the parameters *after* the actor
    #    and must name a compatible declared entity (D15).
    arg_broken = False
    for i, arg in enumerate(scen.args):
        param = action.params[i + 1]
        if arg not in model.entities:
            out.append(Diagnostic(
                DANGLING_ENTITY, where,
                f"argument '{arg}' is not a declared entity",
            ))
            arg_broken = True
        elif arg != param.entity:
            out.append(Diagnostic(
                TEST_ARG_MISMATCH, where,
                f"argument '{arg}' does not match parameter {i + 1} of "
                f"'{action.name}' (expected entity '{param.entity}')",
            ))
            arg_broken = True
    if arg_broken:
        return

    # 5. Decision procedure (D7). A CONFLICT outcome is already reported by
    #    _check_conflicts as a compile error, so the test is skipped rather than
    #    double-reported as a failure.
    decision = model.decide(scen.subject, scen.action)
    if decision.outcome == semantic.CONFLICT:
        return

    exp = test.expectation
    if decision.outcome != exp.result or decision.audit != exp.audit:
        got = decision.outcome + (", AUDIT" if decision.audit else "")
        want = exp.result + (", AUDIT" if exp.audit else "")
        out.append(Diagnostic(
            TEST_FAILED, where,
            f"expected {want} but the decision procedure yields {got}",
        ))


# --- shared helpers ------------------------------------------------------
def _check_subject_entity_role(
    model: semantic.SemanticModel,
    entity: str,
    role: Optional[str],
    where: str,
    out: List[Diagnostic],
) -> bool:
    """Report a dangling entity and/or role for a subject reference.

    Returns True if anything was reported (the caller can then skip dependent
    checks). The entity is checked first; the role is only checked when the
    entity exists, so a bad entity is not also reported as a bad role.
    """
    broken = False
    sym = model.entities.get(entity)
    if sym is None:
        out.append(Diagnostic(
            DANGLING_ENTITY, where,
            f"references undeclared entity '{entity}'",
        ))
        return True
    if role is not None and role not in sym.roles:
        out.append(Diagnostic(
            DANGLING_ROLE, where,
            f"role '{role}' is not declared on entity '{entity}'",
        ))
        broken = True
    return broken


def _check_field_ref(
    model: semantic.SemanticModel,
    ref: ast.FieldRef,
    where: str,
    out: List[Diagnostic],
) -> None:
    """Report a dangling entity or field for a ``<Entity>.<field>`` reference
    (case-sensitive, D12)."""
    sym = model.entities.get(ref.entity)
    if sym is None:
        out.append(Diagnostic(
            DANGLING_ENTITY, where,
            f"field-ref names undeclared entity '{ref.entity}' "
            f"(entity names are case-sensitive, D12)",
        ))
        return
    if ref.field not in sym.fields:
        out.append(Diagnostic(
            DANGLING_FIELD, where,
            f"entity '{ref.entity}' has no declared field '{ref.field}'",
        ))
