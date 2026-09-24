"""Hand-written lexer for AION v0.1 (GRAMMAR.md §1).

Deterministic and dependency-free: no LLM or other non-deterministic component
anywhere in this module (D9, M1 exit criterion). Every token records the 1-based
line and column where it begins.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Union

from .errors import AionLexError

# Declaration keywords (uppercase, reserved).
DECL_KEYWORDS = frozenset({
    "SYSTEM", "ENTITY", "ACTION", "RULE", "ALLOW", "DENY", "REQUIRE",
    "GUARANTEE", "CONSTRAINT", "INVARIANT", "TEST",
})

# Context keywords (reserved where they appear).
CONTEXT_KEYWORDS = frozenset({
    "roles", "fields", "int", "bool", "string", "after", "unchanged",
    "and", "or", "not", "attempts", "performs", "EXPECT", "ALLOWED",
    "DENIED", "AUDIT", "static", "monitor", "proof",
})

# Guarantee predicate atoms (uppercase, reserved; GRAMMAR.md §2 catalog).
GUARANTEE_ATOMS = frozenset({
    "NO_DANGLING_EDGES", "CONFLICT_FREE", "NO_DANGLING_OBLIGATIONS",
    "NO_DEAD_ACTIONS", "NO_DANGLING_STATE_REFS",
})

# Boolean literal keywords (the `value` production).
BOOL_LITERALS = frozenset({"true", "false"})

RESERVED = DECL_KEYWORDS | CONTEXT_KEYWORDS | GUARANTEE_ATOMS | BOOL_LITERALS

TWO_CHAR_SYMBOLS = frozenset({"->", "==", "!=", "<=", ">="})
ONE_CHAR_SYMBOLS = frozenset({"<", ">", ".", ":", ",", "(", ")", "[", "]"})

# Token kinds.
KEYWORD = "KEYWORD"
IDENT = "IDENT"
INTEGER = "INTEGER"
STRING = "STRING"
SYMBOL = "SYMBOL"
EOF = "EOF"

TokenValue = Union[str, int]


@dataclass(frozen=True)
class Token:
    kind: str
    value: TokenValue
    line: int
    column: int

    def describe(self) -> str:
        """Human-readable phrase for use in 'expected ... but found ...' errors."""
        if self.kind == EOF:
            return "end of file"
        if self.kind == IDENT:
            return f"identifier '{self.value}'"
        if self.kind == INTEGER:
            return f"integer {self.value}"
        if self.kind == STRING:
            return "a string literal"
        # KEYWORD and SYMBOL both name the literal token text.
        return f"'{self.value}'"


def _is_letter(ch: str) -> bool:
    return ("a" <= ch <= "z") or ("A" <= ch <= "Z")


def _is_digit(ch: str) -> bool:
    return "0" <= ch <= "9"


def _is_ident_start(ch: str) -> bool:
    return _is_letter(ch)


def _is_ident_part(ch: str) -> bool:
    return _is_letter(ch) or _is_digit(ch) or ch == "_"


class Lexer:
    def __init__(self, text: str) -> None:
        self._text = text
        self._pos = 0
        self._line = 1
        self._column = 1

    # --- low-level cursor helpers -------------------------------------
    def _peek(self, offset: int = 0) -> str:
        idx = self._pos + offset
        return self._text[idx] if idx < len(self._text) else ""

    def _advance(self) -> str:
        ch = self._text[self._pos]
        self._pos += 1
        if ch == "\n":
            self._line += 1
            self._column = 1
        else:
            self._column += 1
        return ch

    def _skip_trivia(self) -> None:
        while self._pos < len(self._text):
            ch = self._peek()
            if ch in " \t\r\n":
                self._advance()
            elif ch == "#":
                while self._pos < len(self._text) and self._peek() != "\n":
                    self._advance()
            else:
                break

    # --- entry point ---------------------------------------------------
    def tokenize(self) -> List[Token]:
        tokens: List[Token] = []
        while True:
            self._skip_trivia()
            line, col = self._line, self._column
            if self._pos >= len(self._text):
                tokens.append(Token(EOF, "", line, col))
                return tokens
            tokens.append(self._next_token(line, col))

    def _next_token(self, line: int, col: int) -> Token:
        ch = self._peek()

        if _is_ident_start(ch):
            return self._read_word(line, col)

        if _is_digit(ch):
            return self._read_number(line, col, negative=False)

        # '-' is either the arrow '->' or the sign of a negative integer.
        if ch == "-":
            if self._peek(1) == ">":
                self._advance()
                self._advance()
                return Token(SYMBOL, "->", line, col)
            if _is_digit(self._peek(1)):
                return self._read_number(line, col, negative=True)
            raise AionLexError(
                "unexpected '-' (expected '->' or a negative integer)", line, col
            )

        if ch == '"':
            return self._read_string(line, col)

        # Two-character symbols take precedence over their one-character prefix.
        pair = self._text[self._pos:self._pos + 2]
        if pair in TWO_CHAR_SYMBOLS:
            self._advance()
            self._advance()
            return Token(SYMBOL, pair, line, col)

        if ch in ONE_CHAR_SYMBOLS:
            self._advance()
            return Token(SYMBOL, ch, line, col)

        raise AionLexError(f"unexpected character {ch!r}", line, col)

    def _read_word(self, line: int, col: int) -> Token:
        start = self._pos
        while self._pos < len(self._text) and _is_ident_part(self._peek()):
            self._advance()
        word = self._text[start:self._pos]
        if word in RESERVED:
            return Token(KEYWORD, word, line, col)
        return Token(IDENT, word, line, col)

    def _read_number(self, line: int, col: int, negative: bool) -> Token:
        digits = ""
        if negative:
            self._advance()  # consume '-'
        while self._pos < len(self._text) and _is_digit(self._peek()):
            digits += self._advance()
        value = int(digits)
        return Token(INTEGER, -value if negative else value, line, col)

    def _read_string(self, line: int, col: int) -> Token:
        self._advance()  # consume opening quote
        chars: List[str] = []
        while True:
            if self._pos >= len(self._text):
                raise AionLexError("unterminated string literal", line, col)
            ch = self._advance()
            if ch == '"':
                break
            chars.append(ch)
        return Token(STRING, "".join(chars), line, col)
