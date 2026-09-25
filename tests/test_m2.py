"""M2 conformance + unit tests: semantic model and static validation.

Exit criteria exercised here (MILESTONES.md M2):
  - Symbol tables for entities, roles, fields, actions, rules.
  - Dangling-reference diagnostics (D3) for every construct that can dangle.
  - Policy-conflict detection (D2): exact-pair ALLOW∩DENY reported as errors;
    role-override resolution (D11) implemented and tested.
  - All five static guarantee predicates implemented; failing guarantees are
    compile errors.
  - A TEST interpreter implementing the D7 decision procedure; every TEST block
    in the conformance suite evaluates to its stated expectation.
  - Negative conformance specs each produce exactly the intended diagnostic —
    no false positives, no silent passes.

Run from the repo root:
    python -m unittest discover -s tests -v
"""

from __future__ import annotations

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir, "src"))

from aion import parse_text  # noqa: E402
from aion import ast_nodes as ast  # noqa: E402
from aion.diagnostics import (  # noqa: E402
    CONFLICT,
    DANGLING_ACTION,
    DANGLING_ENTITY,
    DANGLING_FIELD,
    DANGLING_ROLE,
    DUPLICATE_ACTION,
    DUPLICATE_ENTITY,
    DUPLICATE_FIELD,
    DUPLICATE_ROLE,
    DUPLICATE_RULE,
    GUARANTEE_FAILED,
    TEST_ARG_MISMATCH,
    TEST_ARITY,
    TEST_FAILED,
    UNSUPPORTED_PROOF,
    AionSemanticError,
)
from aion.semantic import ALLOWED, CONFLICT as CONFLICT_OUTCOME, DENIED, SemanticModel  # noqa: E402
from aion.validate import validate, validate_or_raise  # noqa: E402

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
EXAMPLES_DIR = os.path.join(REPO_ROOT, "examples")

POSITIVE_SPECS = [
    "order-service.aion",
    "document-access.aion",
    "inventory.aion",
    "role-override.aion",
]


def _model(source: str) -> SemanticModel:
    model, dups = SemanticModel.build(parse_text(source))
    assert not dups, f"unexpected duplicate diagnostics: {dups}"
    return model


def _codes(diagnostics):
    return [d.code for d in diagnostics]


def _load(name: str) -> str:
    with open(os.path.join(EXAMPLES_DIR, name), "r", encoding="utf-8") as fh:
        return fh.read()


class TestPositiveConformance(unittest.TestCase):
    """The four positive specs validate clean and every TEST passes."""

    def test_positive_specs_have_no_diagnostics(self):
        for name in POSITIVE_SPECS:
            with self.subTest(spec=name):
                spec = parse_text(_load(name))
                self.assertEqual(validate(spec), [], f"{name} should be valid")

    def test_validate_or_raise_does_not_raise_for_positives(self):
        for name in POSITIVE_SPECS:
            with self.subTest(spec=name):
                validate_or_raise(parse_text(_load(name)))  # must not raise


class TestNegativeConformance(unittest.TestCase):
    """Each negative spec yields exactly its intended diagnostics."""

    def test_dangling_reference_reports_every_defect(self):
        spec = parse_text(_load("negative-dangling-reference.aion"))
        diagnostics = validate(spec)
        self.assertEqual(len(diagnostics), 6, [str(d) for d in diagnostics])
        # One of each intended defect, in validator order.
        self.assertEqual(_codes(diagnostics), [
            DANGLING_ACTION,   # User -> remove (undeclared action)
            DANGLING_ROLE,     # User[Writer] (undeclared role)
            DANGLING_ACTION,   # publish -> AUDIT (undeclared obligation action)
            DANGLING_FIELD,    # Document.owner (undeclared field)
            DANGLING_ENTITY,   # document.size (lowercase entity, D12)
            DANGLING_ACTION,   # TEST remove(Document) (undeclared action)
        ])

    def test_dangling_reference_names_the_offending_constructs(self):
        diagnostics = validate(parse_text(_load("negative-dangling-reference.aion")))
        joined = " ".join(str(d) for d in diagnostics)
        for needle in ("remove", "Writer", "publish", "owner", "document"):
            self.assertIn(needle, joined)

    def test_conflict_and_proof_reports_exactly_two(self):
        spec = parse_text(_load("negative-conflict-and-proof.aion"))
        diagnostics = validate(spec)
        self.assertEqual(len(diagnostics), 2, [str(d) for d in diagnostics])
        self.assertEqual(_codes(diagnostics), [CONFLICT, UNSUPPORTED_PROOF])

    def test_conflict_test_is_not_double_reported(self):
        # The TEST expects ALLOWED but the pair is an exact-pair conflict, which
        # is already a compile error; the interpreter must skip it, not add a
        # redundant TEST_FAILED.
        diagnostics = validate(parse_text(_load("negative-conflict-and-proof.aion")))
        self.assertNotIn(TEST_FAILED, _codes(diagnostics))


class TestDecisionProcedure(unittest.TestCase):
    """D1/D7/D11: fail-closed, matching, specificity override, conflict."""

    BASE = (
        "SYSTEM S\n"
        "ENTITY U\n    roles: [A, B]\n"
        "ACTION go(U)\n"
    )

    def test_fail_closed_when_no_allow(self):
        model = _model(self.BASE + "RULE R\nDENY\n    U -> go\n")
        self.assertEqual(model.decide(ast.Subject("U"), "go").outcome, DENIED)
        self.assertEqual(model.decide(ast.Subject("U", "A"), "go").outcome, DENIED)

    def test_bare_allow_matches_role_request(self):
        model = _model(self.BASE + "RULE R\nALLOW\n    U -> go\n")
        self.assertEqual(model.decide(ast.Subject("U", "A"), "go").outcome, ALLOWED)
        self.assertEqual(model.decide(ast.Subject("U"), "go").outcome, ALLOWED)

    def test_role_request_does_not_match_other_role_edge(self):
        model = _model(self.BASE + "RULE R\nALLOW\n    U[A] -> go\n")
        self.assertEqual(model.decide(ast.Subject("U", "A"), "go").outcome, ALLOWED)
        # A request for role B is not matched by an A-only allow → fail closed.
        self.assertEqual(model.decide(ast.Subject("U", "B"), "go").outcome, DENIED)
        # A bare request matches only bare edges (D7) → not matched → denied.
        self.assertEqual(model.decide(ast.Subject("U"), "go").outcome, DENIED)

    def test_specificity_override_deny_wins_for_role_only(self):
        # role-override.aion's shape: broad ALLOW, role-scoped DENY carve-out.
        model = _model(
            self.BASE + "RULE R\nALLOW\n    U -> go\nDENY\n    U[A] -> go\n"
        )
        self.assertEqual(model.decide(ast.Subject("U", "A"), "go").outcome, DENIED)
        self.assertEqual(model.decide(ast.Subject("U", "B"), "go").outcome, ALLOWED)
        self.assertEqual(model.decide(ast.Subject("U"), "go").outcome, ALLOWED)

    def test_specificity_override_allow_wins_over_broad_deny(self):
        model = _model(
            self.BASE + "RULE R\nALLOW\n    U[A] -> go\nDENY\n    U -> go\n"
        )
        self.assertEqual(model.decide(ast.Subject("U", "A"), "go").outcome, ALLOWED)
        self.assertEqual(model.decide(ast.Subject("U", "B"), "go").outcome, DENIED)

    def test_exact_pair_is_conflict(self):
        model = _model(
            self.BASE + "RULE R\nALLOW\n    U[A] -> go\nDENY\n    U[A] -> go\n"
        )
        self.assertEqual(model.decide(ast.Subject("U", "A"), "go").outcome,
                         CONFLICT_OUTCOME)
        self.assertEqual(model.conflicts(), [("R", "U", "A", "go")])

    def test_broad_deny_narrow_allow_is_not_a_conflict(self):
        model = _model(
            self.BASE + "RULE R\nALLOW\n    U[A] -> go\nDENY\n    U -> go\n"
        )
        self.assertEqual(model.conflicts(), [])

    def test_audit_propagates_from_require(self):
        model = _model(
            self.BASE + "RULE R\nALLOW\n    U -> go\nREQUIRE\n    go -> AUDIT\n"
        )
        decision = model.decide(ast.Subject("U"), "go")
        self.assertEqual(decision.outcome, ALLOWED)
        self.assertTrue(decision.audit)

    def test_no_audit_without_require(self):
        model = _model(self.BASE + "RULE R\nALLOW\n    U -> go\n")
        self.assertFalse(model.decide(ast.Subject("U"), "go").audit)


class TestGuaranteeAtoms(unittest.TestCase):
    def test_no_dead_actions_false_when_action_unallowed(self):
        model = _model(
            "SYSTEM S\nENTITY U\n    roles: [A]\n"
            "ACTION live(U)\nACTION dead(U)\n"
            "RULE R\nALLOW\n    U -> live\n"
        )
        self.assertTrue(model.action_is_live("live"))
        self.assertFalse(model.action_is_live("dead"))
        self.assertFalse(model.atom_no_dead_actions())

    def test_conflict_free_atom(self):
        clean = _model(
            "SYSTEM S\nENTITY U\n    roles: [A]\nACTION go(U)\n"
            "RULE R\nALLOW\n    U -> go\n"
        )
        self.assertTrue(clean.atom_conflict_free())
        conflicted = _model(
            "SYSTEM S\nENTITY U\n    roles: [A]\nACTION go(U)\n"
            "RULE R\nALLOW\n    U[A] -> go\nDENY\n    U[A] -> go\n"
        )
        self.assertFalse(conflicted.atom_conflict_free())

    def test_no_dangling_edges_atom(self):
        model = _model(
            "SYSTEM S\nENTITY U\nACTION go(U)\nRULE R\nALLOW\n    U -> ghost\n"
        )
        self.assertFalse(model.atom_no_dangling_edges())

    def test_no_dangling_obligations_atom(self):
        model = _model(
            "SYSTEM S\nENTITY U\nACTION go(U)\n"
            "RULE R\nALLOW\n    U -> go\nREQUIRE\n    ghost -> AUDIT\n"
        )
        self.assertFalse(model.atom_no_dangling_obligations())

    def test_no_dangling_state_refs_atom(self):
        model = _model(
            "SYSTEM S\nENTITY U\nACTION go(U)\n"
            "ENTITY Box\n    fields: [n: int]\n"
            "CONSTRAINT c\n    Box.missing > 0\n"
        )
        self.assertFalse(model.atom_no_dangling_state_refs())

    def test_static_guarantee_failure_is_a_diagnostic(self):
        spec = parse_text(
            "SYSTEM S\nENTITY U\n    roles: [A]\n"
            "ACTION live(U)\nACTION dead(U)\n"
            "RULE R\nALLOW\n    U -> live\n"
            "GUARANTEE static no_dead\n    NO_DEAD_ACTIONS\n"
        )
        diagnostics = validate(spec)
        self.assertEqual(_codes(diagnostics), [GUARANTEE_FAILED])

    def test_monitor_class_is_not_statically_checked(self):
        # A monitor guarantee whose predicate would be false statically is still
        # accepted at compile time (D5: monitors are runtime obligations).
        spec = parse_text(
            "SYSTEM S\nENTITY U\n    roles: [A]\n"
            "ACTION live(U)\nACTION dead(U)\n"
            "RULE R\nALLOW\n    U -> live\n"
            "GUARANTEE monitor no_dead\n    NO_DEAD_ACTIONS\n"
        )
        self.assertEqual(validate(spec), [])

    def test_proof_class_is_rejected(self):
        spec = parse_text(
            "SYSTEM S\nENTITY U\nACTION go(U)\nRULE R\nALLOW\n    U -> go\n"
            "GUARANTEE proof p\n    NO_DANGLING_EDGES\n"
        )
        self.assertEqual(_codes(validate(spec)), [UNSUPPORTED_PROOF])


class TestPredicateEvaluation(unittest.TestCase):
    """§2: `and`/`or` fold left-to-right with NO precedence; `not` and parens."""

    # CONFLICT_FREE=true, NO_DEAD_ACTIONS=false, NO_DANGLING_OBLIGATIONS=false.
    MODEL_SRC = (
        "SYSTEM S\nENTITY U\n    roles: [A]\n"
        "ACTION live(U)\nACTION dead(U)\n"
        "RULE R\nALLOW\n    U -> live\nREQUIRE\n    ghost -> AUDIT\n"
    )

    def _pred(self, text: str) -> ast.PredExpr:
        spec = parse_text(self.MODEL_SRC + f"GUARANTEE static g\n    {text}\n")
        return spec.declarations[-1].pred

    def test_atoms_evaluate_as_expected(self):
        model = _model(self.MODEL_SRC)
        self.assertTrue(model.eval_atom("CONFLICT_FREE"))
        self.assertFalse(model.eval_atom("NO_DEAD_ACTIONS"))
        self.assertFalse(model.eval_atom("NO_DANGLING_OBLIGATIONS"))

    def test_left_to_right_no_precedence(self):
        model = _model(self.MODEL_SRC)
        # (CONFLICT_FREE or NO_DEAD_ACTIONS) and NO_DANGLING_OBLIGATIONS
        #   = (true or false) and false = false
        # With C-style precedence it would be true or (false and false) = true,
        # so this assertion pins the left-to-right rule.
        expr = self._pred(
            "CONFLICT_FREE or NO_DEAD_ACTIONS and NO_DANGLING_OBLIGATIONS"
        )
        self.assertFalse(model.eval_pred(expr))

    def test_negation(self):
        model = _model(self.MODEL_SRC)
        self.assertTrue(model.eval_pred(self._pred("not NO_DEAD_ACTIONS")))
        self.assertFalse(model.eval_pred(self._pred("not CONFLICT_FREE")))

    def test_parentheses_override_grouping(self):
        model = _model(self.MODEL_SRC)
        # CONFLICT_FREE or (NO_DEAD_ACTIONS and NO_DANGLING_OBLIGATIONS)
        #   = true or (false and false) = true
        expr = self._pred(
            "CONFLICT_FREE or (NO_DEAD_ACTIONS and NO_DANGLING_OBLIGATIONS)"
        )
        self.assertTrue(model.eval_pred(expr))


class TestTestInterpreter(unittest.TestCase):
    """D15: subject binds the actor, args bind the remaining params, arity."""

    SPEC = (
        "SYSTEM S\n"
        "ENTITY U\n    roles: [A]\n"
        "ENTITY Box\n"
        "ACTION go(U, Box)\n"
        "RULE R\nALLOW\n    U -> go\n"
    )

    def test_passing_test(self):
        spec = parse_text(self.SPEC + "TEST t\n    U performs go(Box)\n    EXPECT ALLOWED\n")
        self.assertEqual(validate(spec), [])

    def test_arity_mismatch(self):
        spec = parse_text(self.SPEC + "TEST t\n    U performs go()\n    EXPECT ALLOWED\n")
        self.assertEqual(_codes(validate(spec)), [TEST_ARITY])

    def test_arg_entity_mismatch(self):
        spec = parse_text(
            "SYSTEM S\nENTITY U\n    roles: [A]\nENTITY Box\nENTITY Other\n"
            "ACTION go(U, Box)\nRULE R\nALLOW\n    U -> go\n"
            "TEST t\n    U performs go(Other)\n    EXPECT ALLOWED\n"
        )
        self.assertEqual(_codes(validate(spec)), [TEST_ARG_MISMATCH])

    def test_undeclared_arg_entity(self):
        spec = parse_text(self.SPEC + "TEST t\n    U performs go(Ghost)\n    EXPECT ALLOWED\n")
        self.assertEqual(_codes(validate(spec)), [DANGLING_ENTITY])

    def test_outcome_mismatch_is_test_failed(self):
        spec = parse_text(self.SPEC + "TEST t\n    U performs go(Box)\n    EXPECT DENIED\n")
        self.assertEqual(_codes(validate(spec)), [TEST_FAILED])

    def test_audit_expectation_mismatch_is_test_failed(self):
        spec = parse_text(
            self.SPEC + "TEST t\n    U performs go(Box)\n    EXPECT ALLOWED, AUDIT\n"
        )
        self.assertEqual(_codes(validate(spec)), [TEST_FAILED])

    def test_subject_need_not_equal_actor_entity(self):
        # D15: an unrelated subject is allowed; the outcome is decided by D7, so
        # a non-matching subject simply yields DENIED (fail-closed), not an error.
        spec = parse_text(
            "SYSTEM S\nENTITY U\n    roles: [A]\nENTITY Box\nENTITY Stranger\n"
            "ACTION go(U, Box)\nRULE R\nALLOW\n    U -> go\n"
            "TEST t\n    Stranger attempts go(Box)\n    EXPECT DENIED\n"
        )
        self.assertEqual(validate(spec), [])


class TestDuplicates(unittest.TestCase):
    def test_duplicate_entity(self):
        spec = parse_text("SYSTEM S\nENTITY U\nENTITY U\n")
        self.assertIn(DUPLICATE_ENTITY, _codes(validate(spec)))

    def test_duplicate_role(self):
        spec = parse_text("SYSTEM S\nENTITY U\n    roles: [A, A]\n")
        self.assertIn(DUPLICATE_ROLE, _codes(validate(spec)))

    def test_duplicate_field(self):
        spec = parse_text(
            "SYSTEM S\nENTITY U\n    fields: [n: int, n: int]\n"
        )
        self.assertIn(DUPLICATE_FIELD, _codes(validate(spec)))

    def test_duplicate_action(self):
        spec = parse_text("SYSTEM S\nENTITY U\nACTION go(U)\nACTION go(U)\n")
        self.assertIn(DUPLICATE_ACTION, _codes(validate(spec)))

    def test_duplicate_rule(self):
        spec = parse_text(
            "SYSTEM S\nENTITY U\nACTION go(U)\n"
            "RULE R\nALLOW\n    U -> go\nRULE R\nALLOW\n    U -> go\n"
        )
        self.assertIn(DUPLICATE_RULE, _codes(validate(spec)))


class TestSemanticErrorWrapper(unittest.TestCase):
    def test_validate_or_raise_carries_all_diagnostics(self):
        spec = parse_text(_load("negative-dangling-reference.aion"))
        with self.assertRaises(AionSemanticError) as ctx:
            validate_or_raise(spec)
        self.assertEqual(len(ctx.exception.diagnostics), 6)


if __name__ == "__main__":
    unittest.main(verbosity=2)
