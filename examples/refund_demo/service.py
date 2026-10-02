"""Exploratory, handwritten host adapter; not an AION generator or runtime."""
from dataclasses import dataclass
from pathlib import Path
from threading import RLock
from types import MappingProxyType
from typing import Mapping

from aion import build_validated_model, parse_text
from aion.ast_nodes import Subject


@dataclass(frozen=True)
class Payment:
    amount: int
    refunded: int = 0


@dataclass(frozen=True)
class Audit:
    principal: str
    action: str
    payment_id: str
    amount: int


@dataclass(frozen=True)
class Snapshot:
    payments: Mapping[str, Payment]
    audit: tuple[Audit, ...]


class RefundService:
    """Single-process in-memory demo with a trusted, fixed identity directory.

    Principal IDs are supplied by the trusted caller, not authenticated here.
    Amounts are integer minor units. Successful writes and audit records commit
    together under one lock. Restarting loses all data.
    """

    def __init__(self):
        self._model = build_validated_model(parse_text(
            Path(__file__).with_name('policy.aion').read_text(encoding='utf-8')))
        self._identities = {'alice': ('Customer', None),
                            'sam': ('Staff', 'Support'),
                            'fran': ('Staff', 'Finance')}
        self._lock = RLock()
        self._state = Snapshot(MappingProxyType({}), ())

    @property
    def snapshot(self):
        with self._lock:
            return self._state

    def _authorize(self, principal, action):
        identity = self._identities.get(principal)
        if identity is None:
            raise PermissionError('Unknown principal')
        decision = self._model.decide(Subject(*identity), action)
        if decision.outcome != 'ALLOWED':
            raise PermissionError(f'{principal} cannot {action}')
        # This adapter requires audit for every write, even if policy is edited.
        if not decision.audit:
            raise ValueError('Adapter requires AUDIT for every write')

    @staticmethod
    def _amount(amount):
        if type(amount) is not int or amount <= 0:
            raise ValueError('Amount must be a positive integer in minor units')

    def pay(self, principal, payment_id, amount):
        with self._lock:
            self._authorize(principal, 'pay')
            self._amount(amount)
            if not isinstance(payment_id, str) or not payment_id:
                raise ValueError('Payment ID must be a nonempty string')
            if payment_id in self._state.payments:
                raise ValueError('Payment already exists')
            self._commit(principal, 'pay', payment_id, amount, Payment(amount))

    def refund(self, principal, payment_id, amount):
        with self._lock:
            self._authorize(principal, 'refund')
            self._amount(amount)
            before = self._state.payments[payment_id]
            after = Payment(before.amount, before.refunded + amount)
            # Handwritten mappings of the named invariant/constraints in policy.
            if after.amount != before.amount:
                raise ValueError('original_payment_preserved')
            if not 0 <= after.refunded <= after.amount:
                raise ValueError('refund_budget / refund_nonnegative')
            self._commit(principal, 'refund', payment_id, amount, after)

    def _commit(self, principal, action, payment_id, amount, payment):
        payments = dict(self._state.payments)
        payments[payment_id] = payment
        audit = self._state.audit + (Audit(principal, action, payment_id, amount),)
        self._state = Snapshot(MappingProxyType(payments), audit)


def main():
    service = RefundService()
    service.pay('alice', 'payment-1', 1000)
    print('ALLOWED: Alice paid 1000 minor units')
    try:
        service.refund('sam', 'payment-1', 100)
    except PermissionError as error:
        print(f'DENIED: {error}')
    service.refund('fran', 'payment-1', 400)
    print('ALLOWED: Finance refunded 400 minor units')
    try:
        service.refund('fran', 'payment-1', 601)
    except ValueError as error:
        print(f'REJECTED: {error}')
    print(f'Final payment: {service.snapshot.payments["payment-1"]}')
    print(f'Committed audit records: {len(service.snapshot.audit)}')


if __name__ == '__main__':
    main()
