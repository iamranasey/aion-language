# Executable refund acceptance example

This is an **exploratory, handwritten application adapter** using the implemented
M2 policy evaluator. It is not generated code, a new conformance seed, an AION
runtime, or completion of M3/M4. Its purpose is to give a future backend a small,
executable acceptance target. No real money moves.

From the repository root, with Python 3.10 or later:

```powershell
python -m pip install -e .
python examples/refund_demo/service.py
python -m unittest discover -s tests -p test_refund_demo.py -v
```

The demo creates a payment of 1000 minor units, denies a support user's refund,
allows a finance user's refund of 400, and rejects another refund of 601. The
final payment has amount 1000 and refunded 400, with two committed audit records.
The full repository test command includes this example's tests.

## Responsibility and traceability

| Source or requirement | Current implementation | Evidence |
| --- | --- | --- |
| `Access` ALLOW/DENY | Validated M2 model, called by `_authorize` | Customer/finance allowed; support, unknown IDs and customer refunds denied |
| `Access` REQUIRE AUDIT | M2 audit decision plus handwritten `_commit` | Exact records checked for successful writes |
| `original_payment_preserved` | Handwritten immutable Payment replacement and before/after check | Original amount preserved after partial/full refunds |
| `refund_budget`, `refund_nonnegative` | Handwritten cumulative refund check | Excessive and concurrent refunds rejected |
| `valid_policy` and three TESTs | M2 validation on service construction | Every test constructs and validates the policy |
| Positive integer amounts, unique payment IDs | Adapter-specific input checks | Bad types, duplicate IDs, zero/negative amounts rejected |
| Atomic in-memory state and audit | Lock and single immutable snapshot replacement | Rejections preserve snapshot; concurrent budget test |

D16 specificity allows Finance despite the broader Staff denial. D17–D19
validation runs before the adapter exposes operations. Under D20, the compiler
checks state references and types only: it does **not** generate or verify the
Python state checks. Changing the AION constraints requires manually reviewing
the adapter; arbitrary policy files are deliberately not accepted by its API.

## Explicit host assumptions

- A fixed trusted directory maps `alice`, `sam`, and `fran` to subjects. This is
  not authentication: callers able to invoke the Python API can supply those IDs.
- One in-memory service instance; no network, database, persistence or external
  payment integration. A lock coordinates threads, not processes.
- Integer minor units; successful refunds accumulate against a single payment.
  Finance may refund any payment in the instance. No ownership model is implied.
- Only successful state changes enter the audit tuple. Denied/invalid attempts
  raise exceptions. Audit is not durable or tamper-resistant storage.
- Duplicate payment IDs are rejected. Refund retries are not idempotent: repeated
  valid calls are distinct refunds until the budget is exhausted.
- Records/snapshots are immutable through the public API; private Python members
  are not a security boundary.

## Backend acceptance target and proposed decisions

The remaining specification-to-generated-system path is **not implemented**.
After M3's documented serialized IR and information-preservation criteria are
met, M4 can generate a policy artifact and run these authorization cases against
that artifact. Keep the host adapter explicit until runtime decisions are adopted.

The following are PROPOSED for maintainer review, not numbered language decisions:

1. **Instance binding:** define which runtime object each entity field reference
   denotes. This demo binds Payment to the addressed payment record.
2. **Transition checks:** define before/after snapshots and constraint timing.
   This demo checks candidate state before committing it.
3. **Failure and obligations:** define transaction scope and audit failure behavior.
   This demo commits state and a success audit record in one in-memory replacement.
4. **Retries and identity:** define whether these belong to the host contract or
   language. This demo leaves identity to its caller and has no refund retry keys.

A generated state backend must reject unsupported constructs rather than silently
drop them, emit source-to-IR-to-output traceability, and pass the rejection and
state tests against its generated artifact. This README's manual mapping does not
satisfy that M4 traceability requirement.
