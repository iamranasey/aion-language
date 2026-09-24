"""M1 conformance tests: parser + pretty-printer over the v0.1 suite.

Exit criteria exercised here (MILESTONES.md M1):
  - 100% of the M0 conformance suite parses.
  - `parse -> print -> re-parse` is stable (round-trip) for every spec.
  - Errors carry line and column and identify the expected construct.
  - No LLM / non-determinism in the parse path (structural: stdlib only).

Scope note: at M1 every example is *syntactically* valid, including the two
`negative-*` specs — their defects are semantic (dangling references D3, an
exact-pair conflict D2/D11, the `proof` class D5) and are rejected at M2, not
here. This file therefore asserts they parse cleanly and round-trip; it does
not assert semantic rejection.

Run from the repo root:
    python -m unittest discover -s tests -v
"""

from __future__ import annotations

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir, "src"))

from aion import AionLexError, AionSyntaxError, parse_text, pretty_print  # noqa: E402
from aion.lexer import IDENT, INTEGER, KEYWORD, SYMBOL, Lexer  # noqa: E402

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
EXAMPLES_DIR = os.path.join(REPO_ROOT, "examples")

# Every *.aion under examples/ is part of the M0 conformance seed.
CONFORMANCE_SPECS = sorted(
    f for f in os.listdir(EXAMPLES_DIR) if f.endswith(".aion")
)


def _round_trip(source: str):
    """parse -> print -> re-parse; returns (ast, printed, reparsed_ast)."""
    spec = parse_text(source)
    printed = pretty_print(spec)
    reparsed = parse_text(printed)
    return spec, printed, reparsed


class TestConformanceSuiteParses(unittest.TestCase):
    def test_suite_is_nonempty(self):
        self.assertTrue(
            CONFORMANCE_SPECS,
            "expected example .aion specs to test against",
        )

    def test_every_spec_parses(self):
        for name in CONFORMANCE_SPECS:
            with self.subTest(spec=name):
                path = os.path.join(EXAMPLES_DIR, name)
                with open(path, "r", encoding="utf-8") as handle:
                    source = handle.read()
                spec = parse_text(source)  # must not raise
                self.assertTrue(spec.name, f"{name}: empty SYSTEM name")

    def test_every_spec_round_trips(self):
        for name in CONFORMANCE_SPECS:
            with self.subTest(spec=name):
                path = os.path.join(EXAMPLES_DIR, name)
                with open(path, "r", encoding="utf-8") as handle:
                    source = handle.read()
                spec, printed, reparsed = _round_trip(source)
                self.assertEqual(
                    spec, reparsed,
                    f"{name}: round-trip unstable (re-parsed AST differs)",
                )
                # Printing is idempotent once the AST is canonical.
                self.assertEqual(printed, pretty_print(reparsed))


class TestNegativeSyntax(unittest.TestCase):
    """Malformed inputs must be rejected with a line/column diagnostic.

    These are *syntax* failures (M1). They are distinct from the semantic
    defects in examples/negative-*.aion, which are M2's responsibility.
    """

    def assert_syntax_error(self, source, line=None, column=None):
        with self.assertRaises(AionSyntaxError) as ctx:
            parse_text(source)
        err = ctx.exception
        self.assertIsInstance(err.line, int)
        self.assertIsInstance(err.column, int)
        if line is not None:
            self.assertEqual(err.line, line)
        if column is not None:
            self.assertEqual(err.column, column)
        return err

    def test_missing_system_keyword(self):
        self.assert_syntax_error("ENTITY Foo\n", line=1, column=1)

    def test_unknown_declaration_keyword(self):
        # POLICY is not a declaration keyword in GRAMMAR.md §2.
        self.assert_syntax_error("SYSTEM S\nPOLICY x\n", line=2, column=1)

    def test_reserved_word_as_declared_name(self):
        # 'roles' is reserved and may not be reused as an identifier (§1).
        self.assert_syntax_error("SYSTEM S\nENTITY roles\n", line=2, column=8)

    def test_unclosed_bracket(self):
        self.assert_syntax_error("SYSTEM S\nENTITY E\n    roles: [A, B\n", line=4, column=1)

    def test_action_missing_arrow_target(self):
        # After '->' the result identifier is missing; the offending position is
        # end of input (line 3, col 1), not the '->' token itself.
        self.assert_syntax_error("SYSTEM S\nACTION a(X) ->\n", line=3, column=1)

    def test_guarantee_lowercase_atom_rejected(self):
        # Atoms are uppercase reserved tokens; a lowercase form is an IDENT and
        # is not a valid pred-atom.
        self.assert_syntax_error(
            "SYSTEM S\nGUARANTEE static g no_dangling_edges\n", line=2, column=20
        )

    def test_guarantee_bad_class(self):
        self.assert_syntax_error(
            "SYSTEM S\nGUARANTEE runtime g NO_DEAD_ACTIONS\n", line=2, column=11
        )

    def test_test_missing_expect(self):
        # The scenario parses; the missing EXPECT is detected at end of input.
        self.assert_syntax_error(
            "SYSTEM S\nTEST t\n    A performs b()\n", line=4, column=1
        )

    def test_constraint_lone_equals_is_lex_error(self):
        # A single '=' is not a token in GRAMMAR.md §1 (only '==' is), so this
        # fails in the lexer with a line/column diagnostic, before parsing.
        with self.assertRaises(AionLexError) as ctx:
            parse_text("SYSTEM S\nCONSTRAINT c\n    A.b = 1\n")
        self.assertEqual((ctx.exception.line, ctx.exception.column), (3, 9))

    def test_error_message_names_expected_construct(self):
        err = self.assert_syntax_error("SYSTEM S\nENTITY\n")
        self.assertIn("identifier", err.message)


class TestLexer(unittest.TestCase):
    def test_comments_and_whitespace_are_skipped(self):
        toks = Lexer("# lead\nSYSTEM  S\n").tokenize()
        kinds = [(t.kind, t.value) for t in toks if t.kind != "EOF"]
        self.assertEqual(kinds, [(KEYWORD, "SYSTEM"), (IDENT, "S")])

    def test_two_char_symbols_win_over_prefix(self):
        toks = Lexer("-> == <= >= != < >").tokenize()
        values = [t.value for t in toks if t.kind == SYMBOL]
        self.assertEqual(values, ["->", "==", "<=", ">=", "!=", "<", ">"])

    def test_negative_integer_vs_arrow(self):
        toks = Lexer("-5 ->").tokenize()
        self.assertEqual(toks[0].kind, INTEGER)
        self.assertEqual(toks[0].value, -5)
        self.assertEqual(toks[1].kind, SYMBOL)
        self.assertEqual(toks[1].value, "->")

    def test_line_and_column_tracking(self):
        toks = Lexer("SYSTEM\n    S").tokenize()
        self.assertEqual((toks[0].line, toks[0].column), (1, 1))
        self.assertEqual((toks[1].line, toks[1].column), (2, 5))

    def test_unterminated_string_is_lex_error(self):
        with self.assertRaises(AionLexError):
            Lexer('CONSTRAINT c\n    A.b == "oops\n').tokenize()

    def test_unexpected_character_is_lex_error(self):
        with self.assertRaises(AionLexError):
            Lexer("SYSTEM S\nENTITY E @\n").tokenize()


class TestRoundTripCanonicalForms(unittest.TestCase):
    """Targeted round-trips for constructs the examples exercise sparsely."""

    def test_parenthesized_and_negated_predicates(self):
        source = (
            "SYSTEM S\n"
            "GUARANTEE static g\n"
            "    not (NO_DEAD_ACTIONS and CONFLICT_FREE) or NO_DANGLING_EDGES\n"
        )
        spec, printed, reparsed = _round_trip(source)
        self.assertEqual(spec, reparsed)
        self.assertIn("not (NO_DEAD_ACTIONS and CONFLICT_FREE)", printed)

    def test_bool_and_string_literals(self):
        source = (
            "SYSTEM S\n"
            "ENTITY E\n"
            "    fields: [flag: bool, label: string]\n"
            "CONSTRAINT c1\n"
            "    E.flag == true\n"
            "CONSTRAINT c2\n"
            "    E.label != \"x\"\n"
        )
        spec, printed, reparsed = _round_trip(source)
        self.assertEqual(spec, reparsed)
        self.assertIn("E.flag == true", printed)
        self.assertIn('E.label != "x"', printed)

    def test_action_no_params_no_result(self):
        source = "SYSTEM S\nACTION noop()\n"
        spec, printed, reparsed = _round_trip(source)
        self.assertEqual(spec, reparsed)
        self.assertIn("ACTION noop()", printed)

    def test_monitor_and_proof_classes_parse(self):
        # D5: `proof` is parse-only at v0.1; rejection is an M2 validation step.
        for cls in ("monitor", "proof"):
            with self.subTest(cls=cls):
                source = f"SYSTEM S\nGUARANTEE {cls} g NO_DEAD_ACTIONS\n"
                spec, _, reparsed = _round_trip(source)
                self.assertEqual(spec, reparsed)
                self.assertEqual(spec.declarations[0].cls, cls)


if __name__ == "__main__":
    unittest.main(verbosity=2)
