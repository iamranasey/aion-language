# AION v0.1 Conformance Seed

These files are the M0 conformance seed described by [`MILESTONES.md`](../MILESTONES.md).
They were hand-checked against [`GRAMMAR.md`](../GRAMMAR.md) before the front end
existed; they are now machine-checked by the M1 parser (parse + round-trip) and
the M2 validator (semantic diagnostics + the D7 `TEST` interpreter). See
[`tests/test_m1.py`](../tests/test_m1.py) and
[`tests/test_m2.py`](../tests/test_m2.py).

## Expected results

| File | Class | Expected result |
| --- | --- | --- |
| `order-service.aion` | Positive | Parses, round-trips, validates clean; both tests pass |
| `document-access.aion` | Positive | Parses, round-trips, validates clean; both tests pass |
| `inventory.aion` | Positive | Parses, round-trips, validates clean; both tests pass |
| `role-override.aion` | Positive | Parses, round-trips, validates clean; both tests pass. Witnesses the D2/D11 override: a bare `ALLOW` with a role-scoped `DENY` on the same action (Member allowed + audited, Suspended denied) |
| `negative-dangling-reference.aion` | Negative | Parses, then the validator reports exactly 6 diagnostics: undeclared action (`remove`), undeclared role (`Writer`), undeclared obligation action (`publish`), undeclared field (`Document.owner`), undeclared case-mismatched entity (`document.size`, D12), and the undeclared test action (`remove`) |
| `negative-conflict-and-proof.aion` | Negative | Parses, then the validator reports exactly 2 diagnostics: the exact ALLOW/DENY conflict (D2) and the unsupported `proof` guarantee (D5). Its `TEST` is skipped, not double-reported, because the conflict is already a compile error |

The negative files intentionally contain more than one independent defect. The
validator reports each applicable diagnostic rather than silently accepting the
specification or failing on the first defect.
