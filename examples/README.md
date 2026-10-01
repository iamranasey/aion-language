# AION v0.1 Conformance Seed

These files are the M0 conformance seed described by [`MILESTONES.md`](../MILESTONES.md).
All six specs parse and round-trip through the implemented M1 front end,
as checked by [`tests/test_m1.py`](../tests/test_m1.py). The negative specs
are syntactically valid; their defects require M2 semantic validation.

## Expected M2 results (not yet implemented)

The table describes the planned validator and `TEST` interpreter outcomes.
Passing the M1 parser tests does not establish these semantic results.
M2 must apply adopted D16–D20; additional acceptance expectations are recorded
in [`docs/CONFORMANCE.md`](../docs/CONFORMANCE.md). The six existing examples
remain the M0 seed and do not by themselves cover every newly adopted rule.

| File | Class | Expected result |
| --- | --- | --- |
| `order-service.aion` | Positive | Parses; both tests pass |
| `document-access.aion` | Positive | Parses; both tests pass |
| `inventory.aion` | Positive | Parses; both tests pass |
| `role-override.aion` | Positive | Parses; both tests pass. Witnesses the D2/D11 override: a bare `ALLOW` with a role-scoped `DENY` on the same action (Member allowed + audited, Suspended denied) |
| `negative-dangling-reference.aion` | Negative | Rejects undeclared policy action, role, obligation target action, state references, and test action |
| `negative-conflict-and-proof.aion` | Negative | Rejects the exact ALLOW/DENY conflict and unsupported `proof` guarantee |

The negative files intentionally contain more than one independent defect. A
validator should report each applicable diagnostic rather than silently
accepting the specification.
