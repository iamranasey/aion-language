# Security scope and reporting

AION is an experimental parser and static policy-model validator, not a production
authorization enforcement system. Successful validation checks the declared model
and TEST scenarios; it does not enforce runtime state, emit audit events, or prove
generated code correct. Do not use this implementation as a production security boundary.

For programmatic policy queries, `build_validated_model` rejects invalid specs
before returning a model. Low-level `SemanticModel.build` and `decide` are analysis
primitives, not validation gates. Models are mutable: revalidate after mutation,
and supply only declared entity/role/action names in external queries.

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
