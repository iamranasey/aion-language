# Security scope and reporting

AION is an experimental parser and static policy-model validator, not a production
authorization enforcement system. Successful validation checks the declared model
and TEST scenarios; it does not enforce runtime state, emit audit events, or prove
generated code correct. Do not use this implementation as a production security boundary.

For programmatic policy queries, `build_validated_model` rejects invalid specs
before returning a model. Low-level `SemanticModel.build` and `decide` are analysis
primitives, not validation gates. Models are mutable: revalidate after mutation,
and supply only declared entity/role/action names in external queries.

## Semantics that change what a policy means

Two adopted decisions are easy to misread when reasoning about an AION policy as a
security control:

- **A bare `DENY` is not an unconditional block (D11, D16).** The
  highest-specificity matching edge decides: `ALLOW User[Admin] -> archive`
  overrides `DENY User -> archive` for an Admin, while that same `DENY` still
  denies every non-Admin `User`. Writing a broad `DENY` and assuming it closes an
  action for everyone is a specification error, not defence in depth.
- **`RULE` blocks are not isolation boundaries (D17).** All `ALLOW`, `DENY`, and
  `REQUIRE` edges compose into one model with no declaration-order precedence, and
  an exact `(subject, action)` pair appearing in both `ALLOW` and `DENY` anywhere
  in it is a compile error even when no `TEST` exercises it. Splitting a policy
  across blocks neither scopes nor shadows anything.

Conflict detection runs over the whole composed model: an exact pair split across
two `RULE` blocks is reported as a `conflict` diagnostic citing D17. Specificity
produces no diagnostic of its own — it is how the D7 decision procedure computes an
outcome, so a `TEST` block is the way to pin the intended outcome down. Both hold
over the declared model only: `proof`-class guarantees are unsupported in v0.1 and
rejected (D5), and `monitor`-class guarantees are accepted without static checking,
so a spec that validates can still assert runtime properties that nothing in this
repository enforces (D20).

## Untrusted input

The front end reads source and constructs an AST; it does not execute AION input,
call a language model, or access the network. Source size, integer length, and
nesting can consume memory or CPU or exceed Python's processing limits. There is
no hardened in-process resource quota. Process untrusted inputs in a separate
process with host-enforced memory, CPU, time, and file-size limits. The CLI reports
some interpreter limit failures; that is not protection against denial of service.

## Reporting

If the repository's GitHub Security tab offers private vulnerability reporting,
use it. Otherwise ask the maintainer for a private reporting channel without
posting exploit details publicly. No private channel or response SLA is asserted
to exist until the maintainer configures one. Public non-sensitive bugs can use
GitHub issues with a minimal input, implementation revision, and Python version.

## Development controls

Runtime dependencies are standard-library only. CI actions are pinned to commit
hashes and token permissions are read-only. Build dependencies are separate from
runtime dependencies. Review dependency updates and release artifacts; these
controls are not a certification or a claim of complete supply-chain protection.

NIST SSDF is a process reference for future threat modeling, review, vulnerability
handling, and release integrity: https://csrc.nist.gov/pubs/sp/800/218/final.
No formal SSDF compliance, security certification, or external audit is claimed.
