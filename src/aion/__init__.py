"""AION v0.1 front end (M1 — parser and AST).

Public surface:
    parse_text(text) -> Spec
    parse_file(path) -> Spec
    pretty_print(spec) -> str
    AionError / AionLexError / AionSyntaxError

Host language: Python 3 (see src/README.md). M1 is syntactic only; semantic
validation is M2 and is deliberately not present here.
"""

from __future__ import annotations

from .ast_nodes import Spec
from .errors import AionError, AionLexError, AionSyntaxError
from .lexer import Lexer, Token
from .parser import Parser, parse_file, parse_text
from .printer import pretty_print

__all__ = [
    "Spec",
    "AionError",
    "AionLexError",
    "AionSyntaxError",
    "Lexer",
    "Token",
    "Parser",
    "parse_text",
    "parse_file",
    "pretty_print",
]
