"""AION v0.1 toolchain: front end (M1) + semantic validator (M2).

Public surface:
    parse_text(text) -> Spec
    parse_file(path) -> Spec
    pretty_print(spec) -> str
    validate(spec) -> list[Diagnostic]
    validate_or_raise(spec) -> None
    SemanticModel.build(spec) -> (SemanticModel, list[Diagnostic])
    Diagnostic / AionSemanticError
    AionError / AionLexError / AionSyntaxError

Host language: Python 3 (see src/README.md). M1 is the syntactic front end
(lexer, parser, position-free AST, round-trip pretty-printer). M2 adds the
semantic model and static validation: symbol tables, dangling-reference
detection (D3), policy-conflict detection and role-override resolution
(D2/D11), the five static guarantee atoms (D5/D14), and the D7 ``TEST``
interpreter. The parse/validate path is deterministic — no LLM (D9).
"""

from __future__ import annotations

from .ast_nodes import Spec
from .diagnostics import AionSemanticError, Diagnostic
from .errors import AionError, AionLexError, AionSyntaxError
from .lexer import Lexer, Token
from .parser import Parser, parse_file, parse_text
from .printer import pretty_print
from .semantic import ALLOWED, CONFLICT, DENIED, Decision, SemanticModel
from .validate import validate, validate_or_raise

__all__ = [
    "Spec",
    "AionError",
    "AionLexError",
    "AionSyntaxError",
    "AionSemanticError",
    "Diagnostic",
    "Lexer",
    "Token",
    "Parser",
    "parse_text",
    "parse_file",
    "pretty_print",
    "SemanticModel",
    "Decision",
    "ALLOWED",
    "DENIED",
    "CONFLICT",
    "validate",
    "validate_or_raise",
]
