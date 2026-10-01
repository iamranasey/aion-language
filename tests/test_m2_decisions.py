"""Adopted D16–D20 regressions, with a finite independent policy oracle."""
import contextlib
import io
import itertools
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from aion import parse_text, parse_with_locations, validate, build_validated_model, AionSemanticError
from aion.semantic import SemanticModel
from aion.ast_nodes import Subject
from aion.__main__ import main


def codes(source):
    return [d.code for d in validate(parse_text(source))]


class AdoptedSemantics(unittest.TestCase):
    def test_validated_model_rejects_invalid_input(self):
        with self.assertRaises(AionSemanticError):
            build_validated_model(parse_text('SYSTEM S ENTITY E ACTION act(E) TEST t E performs act() EXPECT ALLOWED'))
        source = 'SYSTEM S ENTITY E ACTION act(E) RULE R ALLOW E -> act'
        model = build_validated_model(parse_with_locations(source))
        self.assertEqual(model.decide(Subject('E'), 'act').outcome, 'ALLOWED')

    def test_symbol_tables_cover_every_category(self):
        source = ('SYSTEM S ENTITY E fields: [x: int] ACTION act(E) RULE R ALLOW E -> act '
                  'INVARIANT i after act, E.x unchanged CONSTRAINT c E.x == 1 '
                  'GUARANTEE static g CONFLICT_FREE TEST t E performs act() EXPECT ALLOWED')
        model = build_validated_model(parse_text(source))
        self.assertEqual(set(model.symbols), {'entity','action','rule','invariant','constraint','guarantee','test'})

    def test_published_vectors(self):
        vectors = json.loads((ROOT / 'tests/fixtures/m2-conformance.json').read_text(encoding='utf-8'))
        for case in vectors:
            with self.subTest(case=case['name']):
                self.assertEqual(codes(case['source']), case['diagnostic_codes'])

    def test_each_namespace_rejects_duplicates(self):
        pre = 'SYSTEM S ENTITY E fields: [x: int] ACTION act(E) RULE R ALLOW E -> act '
        for kind, decl in {
            'entity': 'ENTITY F', 'action': 'ACTION other(E)', 'rule': 'RULE Q',
            'invariant': 'INVARIANT i after act, E.x unchanged',
            'constraint': 'CONSTRAINT c E.x == 0',
            'guarantee': 'GUARANTEE static g CONFLICT_FREE',
            'test': 'TEST t E performs act() EXPECT ALLOWED',
        }.items():
            with self.subTest(kind=kind):
                self.assertEqual(codes(f'{pre} {decl} {decl}'), [f'duplicate-{kind}'])

    def test_comparison_type_matrix(self):
        for left, right, op in itertools.product(['int','bool','string'], ['int','bool','string'], ['==','!=','<','<=','>','>=']):
            valid = left == right if op in ('==','!=') else left == right == 'int'
            literal = {'int':'1','bool':'true','string':'"a"'}[right]
            for operand in [literal, 'E.y']:
                with self.subTest(left=left,right=right,op=op,operand=operand):
                    source = f'SYSTEM S ENTITY E fields: [x: {left}, y: {right}] CONSTRAINT c E.x {op} {operand}'
                    self.assertEqual(codes(source), [] if valid else ['comparison-type'])

    def test_dangling_field_does_not_cascade_to_type_error(self):
        self.assertEqual(codes('SYSTEM S ENTITY E CONSTRAINT c E.missing < true'), ['dangling-field'])

    def test_state_values_are_not_executed(self):
        self.assertEqual(codes('SYSTEM S ENTITY E fields: [x: int] CONSTRAINT c E.x < 0 CONSTRAINT d E.x > 5'), [])

    def test_forward_refs_and_namespaces(self):
        source = ('SYSTEM S RULE E ALLOW E -> E ACTION E(E) '
                  'ENTITY E roles: [x] fields: [x: int] TEST E E performs E() EXPECT ALLOWED')
        self.assertEqual(codes(source), [])

    def test_duplicate_action_does_not_hide_dangling_reference(self):
        result = codes('SYSTEM S ENTITY E ACTION act(E) ACTION act(Ghost)')
        self.assertEqual(result, ['duplicate-action','dangling-entity'])

    def test_global_conflict_guarantee_and_test_never_silently_pass(self):
        source = ('SYSTEM S ENTITY E ACTION act(E) RULE R ALLOW E -> act '
                  'RULE Q DENY E -> act GUARANTEE static g CONFLICT_FREE '
                  'TEST t E performs act() EXPECT ALLOWED')
        self.assertEqual(codes(source), ['conflict','guarantee-failed'])

    def test_duplicate_audit_is_idempotent(self):
        source = ('SYSTEM S ENTITY E ACTION act(E) RULE R ALLOW E -> act REQUIRE act -> AUDIT '
                  'RULE Q REQUIRE act -> AUDIT TEST t E performs act() EXPECT ALLOWED, AUDIT')
        self.assertEqual(codes(source), [])


class FinitePolicyOracle(unittest.TestCase):
    def test_all_policy_combinations_and_rule_orders(self):
        # Enumerate four possible edges: bare/role-qualified x allow/deny.
        # Expected decisions come from a truth table, not the implementation.
        edges = [('ALLOW','E'),('DENY','E'),('ALLOW','E[A]'),('DENY','E[A]')]
        for flags in itertools.product([False,True],repeat=4):
            chosen = [(i,k,s) for i,((k,s),enabled) in enumerate(zip(edges,flags)) if enabled]
            for reverse in [False,True]:
                ordered = list(reversed(chosen)) if reverse else chosen
                source = 'SYSTEM S ENTITY E roles: [A] ACTION act(E) ' + ' '.join(
                    f'RULE R{i} {kind} {subject} -> act {subject} -> act' for i,kind,subject in ordered)
                model, duplicate_errors = SemanticModel.build(parse_text(source))
                self.assertEqual(duplicate_errors, [])
                self.assertEqual(len(model.conflicts()), int(flags[0] and flags[1])+int(flags[2] and flags[3]))
                for role in [None,'A']:
                    a,d = flags[2:4] if role and any(flags[2:4]) else flags[:2]
                    expected = 'CONFLICT' if a and d else 'ALLOWED' if a else 'DENIED'
                    self.assertEqual(model.decide(Subject('E',role),'act').outcome, expected)


class SemanticLocationsAndCLI(unittest.TestCase):
    def test_locations_are_optional_and_do_not_change_ast(self):
        source = 'SYSTEM S\nENTITY E fields: [x: int]\nCONSTRAINT c E.x == true\n'
        parsed = parse_with_locations(source)
        errors = validate(parsed)
        self.assertEqual((errors[0].span.line, errors[0].span.column), (3,1))
        self.assertIsNone(validate(parsed.spec)[0].span)
        self.assertEqual(parsed.spec, parse_text(source))

    def test_ambiguous_duplicate_locator_has_no_invented_span(self):
        self.assertIsNone(validate(parse_with_locations('SYSTEM S ENTITY E ENTITY E'))[0].span)

    def test_cli_validate_and_parse_only(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/'bad.aion'
            path.write_text('SYSTEM S\nENTITY E fields: [x: int]\nCONSTRAINT c E.x == true',encoding='utf-8')
            with contextlib.redirect_stderr(io.StringIO()) as err:
                self.assertEqual(main([str(path)]),1)
            self.assertIn(':3:1:',err.getvalue())
            self.assertIn('[comparison-type]',err.getvalue())
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(main([str(path),'--no-validate']),0)

    def test_default_entrypoint_argument(self):
        from unittest.mock import patch
        with patch.object(sys,'argv',['aion',str(ROOT/'examples/order-service.aion')]), contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(main(),0)

    def test_doc_examples_validate(self):
        import re
        for file in ['README.md','SPEC.md','docs/FUNCTIONAL-VISION.md']:
            for source in re.findall(r'```aion\n(.*?)```',(ROOT/file).read_text(encoding='utf-8'),re.S):
                self.assertEqual(validate(parse_text(source)),[],file)
