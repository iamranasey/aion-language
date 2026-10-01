"""Conformance properties, source fidelity, and CLI failure contracts."""
import contextlib
import io
from pathlib import Path
import random
import re
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from aion import AionError, parse_text, parse_with_locations, pretty_print
from aion.__main__ import main


class SourceLocations(unittest.TestCase):
    def test_nested_references_have_exact_spans(self):
        parsed = parse_with_locations('SYSTEM S\nRULE R\nALLOW\n  User[Admin] -> read # tail\n')
        rule = parsed.spec.declarations[0]
        edge = rule.blocks[0].edges[0]
        span = parsed.span_for(edge.subject)
        self.assertEqual((span.line, span.column, span.end_line, span.end_column), (4, 3, 4, 14))
        self.assertEqual(parsed.span_for(edge).end_column, 22)
        self.assertEqual(parsed.span_for(rule).end_line, 4)
        self.assertEqual(parse_text(pretty_print(parsed.spec)), parsed.spec)

    def test_multiline_literal_and_crlf(self):
        parsed = parse_with_locations('SYSTEM S\r\nCONSTRAINT c E.f == "a\nb"\r\n')
        literal = parsed.spec.declarations[0].right
        span = parsed.span_for(literal)
        self.assertEqual((span.line, span.column, span.end_line, span.end_column), (2, 21, 3, 3))

    def test_metadata_does_not_change_structural_equality(self):
        first = parse_with_locations('SYSTEM S ENTITY E')
        second = parse_with_locations('# comment\nSYSTEM S\n\nENTITY E\n')
        self.assertEqual(first.spec, second.spec)
        self.assertNotEqual(first.span_for(first.spec), second.span_for(second.spec))


class ConformanceProperties(unittest.TestCase):
    def test_documented_examples_parse_and_round_trip(self):
        for file in ['README.md', 'SPEC.md', 'docs/FUNCTIONAL-VISION.md']:
            blocks = re.findall(r'```aion\n(.*?)```', (ROOT / file).read_text(encoding='utf-8'), re.S)
            self.assertTrue(blocks, file)
            for block in blocks:
                with self.subTest(file=file):
                    tree = parse_text(block)
                    self.assertEqual(tree, parse_text(pretty_print(tree)))

    def test_normative_example_structural_equivalence(self):
        expected = parse_text((ROOT / 'examples/order-service.aion').read_text(encoding='utf-8'))
        for file in ['README.md', 'SPEC.md']:
            block = re.findall(r'```aion\n(.*?)```', (ROOT / file).read_text(encoding='utf-8'), re.S)[0]
            self.assertEqual(expected, parse_text(block), file)

    def test_seeded_generated_programs_round_trip(self):
        rng = random.Random(20261001)
        for i in range(150):
            value = rng.randint(-100000, 100000)
            op = rng.choice(['==', '!=', '<', '<=', '>', '>='])
            pred = rng.choice(['NO_DEAD_ACTIONS', 'not (CONFLICT_FREE or NO_DANGLING_EDGES)', '(NO_DEAD_ACTIONS and CONFLICT_FREE)'])
            source = f'SYSTEM S{i}\nENTITY E fields: [n: int]\nACTION act(E)\nRULE R ALLOW E -> act\nCONSTRAINT c E.n {op} {value}\nGUARANTEE static g {pred}\nTEST t E performs act() EXPECT ALLOWED\n'
            tree = parse_text(source)
            printed = pretty_print(tree)
            self.assertEqual(tree, parse_text(printed))
            self.assertEqual(printed, pretty_print(parse_text(printed)))
            self.assertEqual(tree, parse_text(source.replace('\n', '\n# generated trivia\n')))

    def test_bounded_seeded_malformed_inputs(self):
        rng = random.Random(42)
        alphabet = 'abcXYZ0123 #\n\t[]():,<>!=-"'
        for _ in range(300):
            text = 'SYSTEM S\n' + ''.join(rng.choice(alphabet) for _ in range(rng.randrange(100)))
            try:
                tree = parse_text(text)
            except AionError as error:
                self.assertGreaterEqual(error.line, 1)
                self.assertGreaterEqual(error.column, 1)
                self.assertIn(error.code, ('AION1001', 'AION1002'))
            else:
                self.assertEqual(tree, parse_text(pretty_print(tree)))


class CommandLine(unittest.TestCase):
    def test_deep_predicate_is_controlled_limit_error(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'deep.aion'
            path.write_text('SYSTEM S GUARANTEE static g ' + '(' * 2000 + 'CONFLICT_FREE' + ')' * 2000, encoding='utf-8')
            with contextlib.redirect_stderr(io.StringIO()) as error:
                self.assertEqual(main([str(path)]), 1)
            self.assertIn('AION1004', error.getvalue())

    def test_unknown_option_rejected(self):
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as error:
            main(['file.aion', '--unknown'])
        self.assertEqual(error.exception.code, 2)

    def test_missing_file_is_controlled_error(self):
        with tempfile.TemporaryDirectory() as folder, contextlib.redirect_stderr(io.StringIO()) as output:
            self.assertEqual(main([str(Path(folder) / 'missing.aion')]), 1)
        self.assertIn('AION1003', output.getvalue())

    def test_bad_utf8_is_controlled_error(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'bad.aion'
            path.write_bytes(b'\xff')
            with contextlib.redirect_stderr(io.StringIO()) as output:
                self.assertEqual(main([str(path)]), 1)
            self.assertIn('AION1003', output.getvalue())

    def test_cli_print_round_trip_and_syntax_failure(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'test.aion'
            path.write_text('SYSTEM S ENTITY E', encoding='utf-8')
            with contextlib.redirect_stdout(io.StringIO()) as output:
                self.assertEqual(main([str(path), '--print']), 0)
            self.assertEqual(parse_text(output.getvalue()), parse_text('SYSTEM S ENTITY E'))
            path.write_text('SYSTEM S ENTITY', encoding='utf-8')
            with contextlib.redirect_stderr(io.StringIO()) as error:
                self.assertEqual(main([str(path)]), 1)
            self.assertIn('AION1002', error.getvalue())
