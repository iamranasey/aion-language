# AION v0.1 Conformance Seed

These files are the M0 conformance seed described by [`MILESTONES.md`](../MILESTONES.md).
They are hand-checked against [`GRAMMAR.md`](../GRAMMAR.md) until the parser exists.

## Expected results

| File | Class | Expected result |
| --- | --- | --- |
| `order-service.aion` | Positive | Parses; both tests pass |
| `document-access.aion` | Positive | Parses; both tests pass |
| `inventory.aion` | Positive | Parses; both tests pass |
| `negative-dangling-reference.aion` | Negative | Rejects undeclared action, role, obligation, fields, and test action |
| `negative-conflict-and-proof.aion` | Negative | Rejects the exact ALLOW/DENY conflict and unsupported `proof` guarantee |

The negative files intentionally contain more than one independent defect. A
validator should report each applicable diagnostic rather than silently
accepting the specification.
