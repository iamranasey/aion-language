"""AION v0.1 front end and semantic validator (M1/M2).

Public surface:
    parse_text(text) -> Spec
    parse_file(path) -> Spec
    pretty_print(spec) -> str
    AionError / AionLexError / AionSyntaxError

Host language: Python 3 (see src/README.md). M1 is syntactic only; semantic
validation is provided separately by the M2 validate API.
"""

from __future__ import annotations

from .ast_nodes import Spec
from .errors import AionError, AionLexError, AionSyntaxError
from .lexer import Lexer, Token
from .parser import Parser, parse_file, parse_text, parse_with_locations
from .source_map import ParsedSource, SourceSpan
from .printer import pretty_print
from .semantic import SemanticModel, Decision
from .diagnostics import Diagnostic, AionSemanticError
from .validate import validate, validate_or_raise, build_validated_model

__all__ = [
    "Spec",
    "SemanticModel", "Decision", "Diagnostic", "AionSemanticError",
    "validate", "validate_or_raise",
    "build_validated_model",
    "AionError",
    "AionLexError",
    "AionSyntaxError",
    "Lexer",
    "Token",
    "Parser",
    "parse_text",
    "parse_file",
    "pretty_print",
    "parse_with_locations",
    "ParsedSource",
    "SourceSpan",
]
