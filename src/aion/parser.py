"""Hand-written deterministic recursive-descent parser for AION v0.1.

Implements GRAMMAR.md §2 exactly. The grammar is LL(1) (D9): every declaration
is dispatched on its leading keyword, and no semantic information is consulted.
This module is *syntactic only* — it does not check dangling references (D3),
policy conflicts (D2/D11), `proof`-class support (D5), or TEST arity (D15).
Those are M2 (semantic model and static validation) and are intentionally
absent here rather than stubbed (guide §3.4, §8: no milestone skipping, no
confident scaffolding).

The parser accepts exactly what the grammar defines and no more: a construct
outside GRAMMAR.md §2 is a syntax error, not a convenience (guide §9.2).
"""

from __future__ import annotations

from typing import List, Optional

from . import ast_nodes as ast
from .errors import AionSyntaxError
from .lexer import (
    EOF, IDENT, INTEGER, KEYWORD, STRING, SYMBOL,
    GUARANTEE_ATOMS, Token, Lexer,
)

DECLARATION_KEYWORDS = {
    "ENTITY", "ACTION", "RULE", "INVARIANT",
    "CONSTRAINT", "GUARANTEE", "TEST",
}
REL_OPS = {"==", "!=", "<", "<=", ">", ">="}
GUARANTEE_CLASSES = {"static", "monitor", "proof"}
PRIMITIVE_TYPES = {"int", "bool", "string"}
TEST_VERBS = {"attempts", "performs"}
EXPECT_RESULTS = {"ALLOWED", "DENIED"}


class Parser:
    def __init__(self, tokens: List[Token]) -> None:
        self._tokens = tokens
        self._i = 0

    # --- token cursor helpers -----------------------------------------
    def _peek(self) -> Token:
        return self._tokens[self._i]

    def _advance(self) -> Token:
        tok = self._tokens[self._i]
        if tok.kind != EOF:
            self._i += 1
        return tok

    def _at_keyword(self, *keywords: str) -> bool:
        tok = self._peek()
        return tok.kind == KEYWORD and str(tok.value) in keywords

    def _at_symbol(self, symbol: str) -> bool:
        tok = self._peek()
        return tok.kind == SYMBOL and tok.value == symbol

    def _error(self, message: str, token: Optional[Token] = None) -> "AionSyntaxError":
        tok = token or self._peek()
        return AionSyntaxError(message, tok.line, tok.column)

    def _expect_keyword(self, keyword: str) -> Token:
        tok = self._peek()
        if tok.kind == KEYWORD and tok.value == keyword:
            return self._advance()
        raise self._error(f"expected '{keyword}' but found {tok.describe()}", tok)

    def _expect_symbol(self, symbol: str) -> Token:
        tok = self._peek()
        if tok.kind == SYMBOL and tok.value == symbol:
            return self._advance()
        raise self._error(f"expected '{symbol}' but found {tok.describe()}", tok)

    def _expect_ident(self) -> str:
        tok = self._peek()
        if tok.kind == IDENT:
            self._advance()
            return str(tok.value)
        raise self._error(f"expected an identifier but found {tok.describe()}", tok)

    # --- productions ---------------------------------------------------
    def parse_spec(self) -> ast.Spec:
        self._expect_keyword("SYSTEM")
        name = self._expect_ident()
        declarations: List[ast.Declaration] = []
        while self._peek().kind != EOF:
            tok = self._peek()
            if tok.kind == KEYWORD and str(tok.value) in DECLARATION_KEYWORDS:
                declarations.append(self._parse_declaration(str(tok.value)))
            else:
                raise self._error(
                    "expected a declaration (ENTITY, ACTION, RULE, INVARIANT, "
                    f"CONSTRAINT, GUARANTEE, or TEST) but found {tok.describe()}",
                    tok,
                )
        return ast.Spec(name=name, declarations=declarations)

    def _parse_declaration(self, keyword: str) -> ast.Declaration:
        if keyword == "ENTITY":
            return self._parse_entity_decl()
        if keyword == "ACTION":
            return self._parse_action_decl()
        if keyword == "RULE":
            return self._parse_rule_decl()
        if keyword == "INVARIANT":
            return self._parse_invariant_decl()
        if keyword == "CONSTRAINT":
            return self._parse_constraint_decl()
        if keyword == "GUARANTEE":
            return self._parse_guarantee_decl()
        return self._parse_test_decl()

    # ENTITY ident [ "roles" ":" "[" ident-list "]" ] [ "fields" ":" "[" field-list "]" ]
    def _parse_entity_decl(self) -> ast.EntityDecl:
        self._expect_keyword("ENTITY")
        name = self._expect_ident()
        roles: Optional[List[str]] = None
        fields: Optional[List[ast.Field]] = None
        if self._at_keyword("roles"):
            self._advance()
            self._expect_symbol(":")
            self._expect_symbol("[")
            roles = self._parse_ident_list()
            self._expect_symbol("]")
        if self._at_keyword("fields"):
            self._advance()
            self._expect_symbol(":")
            self._expect_symbol("[")
            fields = self._parse_field_list()
            self._expect_symbol("]")
        return ast.EntityDecl(name=name, roles=roles, fields=fields)

    def _parse_ident_list(self) -> List[str]:
        names = [self._expect_ident()]
        while self._at_symbol(","):
            self._advance()
            names.append(self._expect_ident())
        return names

    def _parse_field_list(self) -> List[ast.Field]:
        fields = [self._parse_field()]
        while self._at_symbol(","):
            self._advance()
            fields.append(self._parse_field())
        return fields

    def _parse_field(self) -> ast.Field:
        name = self._expect_ident()
        self._expect_symbol(":")
        tok = self._peek()
        if tok.kind == KEYWORD and str(tok.value) in PRIMITIVE_TYPES:
            self._advance()
            return ast.Field(name=name, type=str(tok.value))
        raise self._error(
            f"expected a primitive type (int, bool, or string) but found {tok.describe()}",
            tok,
        )

    # ACTION ident "(" [ param-list ] ")" [ "->" ident ]
    def _parse_action_decl(self) -> ast.ActionDecl:
        self._expect_keyword("ACTION")
        name = self._expect_ident()
        self._expect_symbol("(")
        params: List[ast.Param] = []
        if not self._at_symbol(")"):
            params = self._parse_param_list()
        self._expect_symbol(")")
        result: Optional[str] = None
        if self._at_symbol("->"):
            self._advance()
            result = self._expect_ident()
        return ast.ActionDecl(name=name, params=params, result=result)

    def _parse_param_list(self) -> List[ast.Param]:
        params = [self._parse_param()]
        while self._at_symbol(","):
            self._advance()
            params.append(self._parse_param())
        return params

    def _parse_param(self) -> ast.Param:
        entity = self._expect_ident()
        role: Optional[str] = None
        if self._at_symbol("["):
            self._advance()
            role = self._expect_ident()
            self._expect_symbol("]")
        return ast.Param(entity=entity, role=role)

    # RULE ident { policy-block }
    def _parse_rule_decl(self) -> ast.RuleDecl:
        self._expect_keyword("RULE")
        name = self._expect_ident()
        blocks: List[ast.PolicyBlock] = []
        while self._at_keyword("ALLOW", "DENY", "REQUIRE"):
            blocks.append(self._parse_policy_block())
        return ast.RuleDecl(name=name, blocks=blocks)

    def _parse_policy_block(self) -> ast.PolicyBlock:
        tok = self._advance()  # ALLOW | DENY | REQUIRE
        keyword = str(tok.value)
        if keyword in ("ALLOW", "DENY"):
            edges = [self._parse_edge()]
            while self._peek().kind == IDENT:
                edges.append(self._parse_edge())
            return ast.AllowBlock(edges) if keyword == "ALLOW" else ast.DenyBlock(edges)
        # REQUIRE
        obligation_edges = [self._parse_obligation_edge()]
        while self._peek().kind == IDENT:
            obligation_edges.append(self._parse_obligation_edge())
        return ast.RequireBlock(obligation_edges)

    def _parse_edge(self) -> ast.Edge:
        subject = self._parse_subject()
        self._expect_symbol("->")
        action = self._expect_ident()
        return ast.Edge(subject=subject, action=action)

    def _parse_subject(self) -> ast.Subject:
        entity = self._expect_ident()
        role: Optional[str] = None
        if self._at_symbol("["):
            self._advance()
            role = self._expect_ident()
            self._expect_symbol("]")
        return ast.Subject(entity=entity, role=role)

    def _parse_obligation_edge(self) -> ast.ObligationEdge:
        action = self._expect_ident()
        self._expect_symbol("->")
        self._expect_keyword("AUDIT")
        return ast.ObligationEdge(action=action, obligation="AUDIT")

    # INVARIANT ident "after" ident "," field-ref "unchanged"
    def _parse_invariant_decl(self) -> ast.InvariantDecl:
        self._expect_keyword("INVARIANT")
        name = self._expect_ident()
        self._expect_keyword("after")
        action = self._expect_ident()
        self._expect_symbol(",")
        ref = self._parse_field_ref()
        self._expect_keyword("unchanged")
        return ast.InvariantDecl(name=name, action=action, ref=ref)

    def _parse_field_ref(self) -> ast.FieldRef:
        entity = self._expect_ident()
        self._expect_symbol(".")
        field = self._expect_ident()
        return ast.FieldRef(entity=entity, field=field)

    # CONSTRAINT ident comparison
    def _parse_constraint_decl(self) -> ast.ConstraintDecl:
        self._expect_keyword("CONSTRAINT")
        name = self._expect_ident()
        left = self._parse_field_ref()
        op = self._parse_rel_op()
        right = self._parse_field_ref_or_value()
        return ast.ConstraintDecl(name=name, left=left, op=op, right=right)

    def _parse_rel_op(self) -> str:
        tok = self._peek()
        if tok.kind == SYMBOL and str(tok.value) in REL_OPS:
            self._advance()
            return str(tok.value)
        raise self._error(
            "expected a relational operator (==, !=, <, <=, >, or >=) "
            f"but found {tok.describe()}",
            tok,
        )

    def _parse_field_ref_or_value(self) -> "ast.FieldRef | ast.Literal":
        tok = self._peek()
        if tok.kind == IDENT:
            return self._parse_field_ref()
        if tok.kind == INTEGER:
            self._advance()
            return ast.Literal(int(tok.value))
        if tok.kind == STRING:
            self._advance()
            return ast.Literal(str(tok.value))
        if tok.kind == KEYWORD and tok.value in ("true", "false"):
            self._advance()
            return ast.Literal(tok.value == "true")
        raise self._error(
            "expected a field reference or a literal value "
            f"(integer, string, true, or false) but found {tok.describe()}",
            tok,
        )

    # GUARANTEE class ident guarantee-pred
    def _parse_guarantee_decl(self) -> ast.GuaranteeDecl:
        self._expect_keyword("GUARANTEE")
        tok = self._peek()
        if tok.kind == KEYWORD and str(tok.value) in GUARANTEE_CLASSES:
            self._advance()
            cls = str(tok.value)
        else:
            raise self._error(
                "expected a guarantee class (static, monitor, or proof) "
                f"but found {tok.describe()}",
                tok,
            )
        name = self._expect_ident()
        pred = self._parse_pred_expr()
        return ast.GuaranteeDecl(cls=cls, name=name, pred=pred)

    def _parse_pred_expr(self) -> ast.PredExpr:
        terms = [self._parse_pred_term()]
        ops: List[str] = []
        while self._at_keyword("and", "or"):
            ops.append(str(self._advance().value))
            terms.append(self._parse_pred_term())
        return ast.PredExpr(terms=terms, ops=ops)

    def _parse_pred_term(self) -> ast.PredTerm:
        negated = False
        if self._at_keyword("not"):
            self._advance()
            negated = True
        if self._at_symbol("("):
            self._advance()
            inner = self._parse_pred_expr()
            self._expect_symbol(")")
            return ast.PredTerm(negated=negated, operand=inner)
        tok = self._peek()
        if tok.kind == KEYWORD and str(tok.value) in GUARANTEE_ATOMS:
            self._advance()
            return ast.PredTerm(negated=negated, operand=ast.PredAtom(str(tok.value)))
        raise self._error(
            "expected a guarantee predicate atom "
            "(NO_DANGLING_EDGES, CONFLICT_FREE, NO_DANGLING_OBLIGATIONS, "
            f"NO_DEAD_ACTIONS, or NO_DANGLING_STATE_REFS) or '(' but found {tok.describe()}",
            tok,
        )

    # TEST ident scenario "EXPECT" expectation
    def _parse_test_decl(self) -> ast.TestDecl:
        self._expect_keyword("TEST")
        name = self._expect_ident()
        scenario = self._parse_scenario()
        self._expect_keyword("EXPECT")
        expectation = self._parse_expectation()
        return ast.TestDecl(name=name, scenario=scenario, expectation=expectation)

    def _parse_scenario(self) -> ast.Scenario:
        subject = self._parse_subject()
        tok = self._peek()
        if tok.kind == KEYWORD and str(tok.value) in TEST_VERBS:
            self._advance()
            verb = str(tok.value)
        else:
            raise self._error(
                f"expected 'attempts' or 'performs' but found {tok.describe()}", tok
            )
        action = self._expect_ident()
        self._expect_symbol("(")
        args: List[str] = []
        if not self._at_symbol(")"):
            args = self._parse_ident_list()
        self._expect_symbol(")")
        return ast.Scenario(subject=subject, verb=verb, action=action, args=args)

    def _parse_expectation(self) -> ast.Expectation:
        tok = self._peek()
        if tok.kind == KEYWORD and str(tok.value) in EXPECT_RESULTS:
            self._advance()
            result = str(tok.value)
        else:
            raise self._error(
                f"expected 'ALLOWED' or 'DENIED' but found {tok.describe()}", tok
            )
        audit = False
        if self._at_symbol(","):
            self._advance()
            self._expect_keyword("AUDIT")
            audit = True
        return ast.Expectation(result=result, audit=audit)


def parse_text(text: str) -> ast.Spec:
    """Lex and parse AION source text into a Spec AST."""
    tokens = Lexer(text).tokenize()
    return Parser(tokens).parse_spec()


def parse_file(path: str) -> ast.Spec:
    """Read and parse an AION source file into a Spec AST."""
    with open(path, "r", encoding="utf-8") as handle:
        return parse_text(handle.read())
