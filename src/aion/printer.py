"""AST pretty-printer for AION v0.1.

Emits canonical source that re-parses to a structurally equal AST, satisfying
the M1 round-trip exit criterion (`parse -> print -> re-parse` is stable for
every conformance spec). Formatting is deterministic; it need not reproduce the
original whitespace, only the original structure.
"""

from __future__ import annotations

from typing import List

from . import ast_nodes as ast


def pretty_print(spec: ast.Spec) -> str:
    parts: List[str] = [f"SYSTEM {spec.name}"]
    for decl in spec.declarations:
        parts.append(_print_declaration(decl))
    return "\n\n".join(parts) + "\n"


def _print_declaration(decl: ast.Declaration) -> str:
    if isinstance(decl, ast.EntityDecl):
        return _print_entity(decl)
    if isinstance(decl, ast.ActionDecl):
        return _print_action(decl)
    if isinstance(decl, ast.RuleDecl):
        return _print_rule(decl)
    if isinstance(decl, ast.InvariantDecl):
        return _print_invariant(decl)
    if isinstance(decl, ast.ConstraintDecl):
        return _print_constraint(decl)
    if isinstance(decl, ast.GuaranteeDecl):
        return _print_guarantee(decl)
    if isinstance(decl, ast.TestDecl):
        return _print_test(decl)
    raise TypeError(f"unknown declaration node: {decl!r}")


def _print_entity(decl: ast.EntityDecl) -> str:
    lines = [f"ENTITY {decl.name}"]
    if decl.roles is not None:
        lines.append(f"    roles: [{', '.join(decl.roles)}]")
    if decl.fields is not None:
        rendered = ", ".join(f"{f.name}: {f.type}" for f in decl.fields)
        lines.append(f"    fields: [{rendered}]")
    return "\n".join(lines)


def _print_action(decl: ast.ActionDecl) -> str:
    params = ", ".join(_print_param(p) for p in decl.params)
    head = f"ACTION {decl.name}({params})"
    if decl.result is not None:
        head += f" -> {decl.result}"
    return head


def _print_param(param: ast.Param) -> str:
    return f"{param.entity}[{param.role}]" if param.role else param.entity


def _print_subject(subject: ast.Subject) -> str:
    return f"{subject.entity}[{subject.role}]" if subject.role else subject.entity


def _print_rule(decl: ast.RuleDecl) -> str:
    lines = [f"RULE {decl.name}"]
    for block in decl.blocks:
        if isinstance(block, ast.AllowBlock):
            lines.append("ALLOW")
            lines.extend(f"    {_print_subject(e.subject)} -> {e.action}" for e in block.edges)
        elif isinstance(block, ast.DenyBlock):
            lines.append("DENY")
            lines.extend(f"    {_print_subject(e.subject)} -> {e.action}" for e in block.edges)
        elif isinstance(block, ast.RequireBlock):
            lines.append("REQUIRE")
            lines.extend(f"    {e.action} -> {e.obligation}" for e in block.edges)
        else:
            raise TypeError(f"unknown policy block: {block!r}")
    return "\n".join(lines)


def _print_invariant(decl: ast.InvariantDecl) -> str:
    return (
        f"INVARIANT {decl.name}\n"
        f"    after {decl.action}, {_print_field_ref(decl.ref)} unchanged"
    )


def _print_field_ref(ref: ast.FieldRef) -> str:
    return f"{ref.entity}.{ref.field}"


def _print_constraint(decl: ast.ConstraintDecl) -> str:
    return (
        f"CONSTRAINT {decl.name}\n"
        f"    {_print_field_ref(decl.left)} {decl.op} {_print_operand(decl.right)}"
    )


def _print_operand(operand) -> str:
    if isinstance(operand, ast.FieldRef):
        return _print_field_ref(operand)
    if isinstance(operand, ast.Literal):
        return _print_literal(operand)
    raise TypeError(f"unknown constraint operand: {operand!r}")


def _print_literal(literal: ast.Literal) -> str:
    value = literal.value
    if isinstance(value, bool):  # must precede int: bool is a subclass of int
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, str):
        return f'"{value}"'
    raise TypeError(f"unknown literal value: {value!r}")


def _print_guarantee(decl: ast.GuaranteeDecl) -> str:
    return (
        f"GUARANTEE {decl.cls} {decl.name}\n"
        f"    {_print_pred_expr(decl.pred)}"
    )


def _print_pred_expr(expr: ast.PredExpr) -> str:
    out = _print_pred_term(expr.terms[0])
    for op, term in zip(expr.ops, expr.terms[1:]):
        out += f" {op} {_print_pred_term(term)}"
    return out


def _print_pred_term(term: ast.PredTerm) -> str:
    prefix = "not " if term.negated else ""
    if isinstance(term.operand, ast.PredAtom):
        return f"{prefix}{term.operand.name}"
    if isinstance(term.operand, ast.PredExpr):
        return f"{prefix}({_print_pred_expr(term.operand)})"
    raise TypeError(f"unknown predicate operand: {term.operand!r}")


def _print_test(decl: ast.TestDecl) -> str:
    scenario = decl.scenario
    args = ", ".join(scenario.args)
    expectation = f"EXPECT {scenario_expectation(decl.expectation)}"
    return (
        f"TEST {decl.name}\n"
        f"    {_print_subject(scenario.subject)} {scenario.verb} "
        f"{scenario.action}({args})\n"
        f"    {expectation}"
    )


def scenario_expectation(expectation: ast.Expectation) -> str:
    return f"{expectation.result}, AUDIT" if expectation.audit else expectation.result
