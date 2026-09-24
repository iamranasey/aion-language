"""Error types for the AION v0.1 front end.

Every diagnostic carries a 1-based line and column so the M1 exit criterion
"error messages carry line and column and identify the expected construct" is
met at the point the error is raised.
"""

from __future__ import annotations


class AionError(Exception):
    """Base class for front-end diagnostics."""

    def __init__(self, message: str, line: int, column: int) -> None:
        self.message = message
        self.line = line
        self.column = column
        super().__init__(f"{line}:{column}: {message}")


class AionLexError(AionError):
    """Raised when the source cannot be tokenized."""


class AionSyntaxError(AionError):
    """Raised when the token stream does not match the GRAMMAR.md §2 EBNF."""
