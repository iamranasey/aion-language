"""Executable acceptance example; host behavior is not AION runtime semantics."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
sys.path.insert(0, str(ROOT / 'examples' / 'refund_demo'))
from service import RefundService


class RefundDemoTests(unittest.TestCase):
    def setUp(self):
        self.service = RefundService()
        self.service.pay('alice', 'p1', 1000)

    def assert_rejected_without_change(self, exception, call):
        before = self.service.snapshot
        with self.assertRaises(exception):
            call()
        self.assertIs(self.service.snapshot, before)

    def test_partial_then_full_refund_and_audit(self):
        self.service.refund('fran', 'p1', 400)
        self.service.refund('fran', 'p1', 600)
        state = self.service.snapshot
        self.assertEqual((state.payments['p1'].amount, state.payments['p1'].refunded), (1000, 1000))
        self.assertEqual([(a.principal, a.action, a.payment_id, a.amount) for a in state.audit],
                         [('alice', 'pay', 'p1', 1000), ('fran', 'refund', 'p1', 400), ('fran', 'refund', 'p1', 600)])
        self.assert_rejected_without_change(ValueError, lambda: self.service.refund('fran', 'p1', 1))

    def test_denied_and_unknown_identities(self):
        for principal in ('sam', 'alice', 'unknown', 'Staff[Finance]'):
            self.assert_rejected_without_change(PermissionError,
                lambda: self.service.refund(principal, 'p1', 1))
        self.assert_rejected_without_change(PermissionError,
            lambda: self.service.pay('fran', 'p2', 100))

    def test_invalid_amounts_and_over_refund(self):
        for amount in (True, False, 0, -1, 1.5, '100', None, 1001):
            self.assert_rejected_without_change(ValueError,
                lambda: self.service.refund('fran', 'p1', amount))
        for amount in (True, 0, -1, 1.5, '100'):
            self.assert_rejected_without_change(ValueError,
                lambda: self.service.pay('alice', 'p2', amount))

    def test_duplicate_missing_and_snapshot_isolation(self):
        self.assert_rejected_without_change(ValueError, lambda: self.service.pay('alice', 'p1', 100))
        self.assert_rejected_without_change(KeyError, lambda: self.service.refund('fran', 'missing', 1))
        before = self.service.snapshot
        with self.assertRaises(TypeError):
            before.payments['p1'] = None
        self.service.refund('fran', 'p1', 1)
        self.assertEqual(before.payments['p1'].refunded, 0)

    def test_concurrent_refunds_cannot_exceed_budget(self):
        def refund(_):
            try:
                self.service.refund('fran', 'p1', 600)
                return True
            except ValueError:
                return False
        with ThreadPoolExecutor(max_workers=2) as executor:
            outcomes = list(executor.map(refund, range(2)))
        self.assertEqual(sorted(outcomes), [False, True])
        self.assertEqual(self.service.snapshot.payments['p1'].refunded, 600)
        self.assertEqual(len(self.service.snapshot.audit), 2)
