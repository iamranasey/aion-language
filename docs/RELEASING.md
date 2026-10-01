# Compatibility and release procedure

The language version (v0.1) and Python package version (currently 0.1.0.dev0) are
separate. This is an unreleased development package. Python 3.10–3.14 is the
configured CI range; do not claim every platform passed until its job succeeds.

Before a release:

1. Review the diff, unresolved semantic proposals, and support claims. Record
   language changes through the decision log; document API and CLI changes.
2. Require passing conformance and installed-wheel checks across the CI matrix.
3. Build sdist and wheel from the release commit in a clean environment using
   `python -m build`; run `python -m twine check dist/*` and install the wheel in
   a fresh environment. Include LICENSE and verify package contents.
4. Record Python/build-tool versions and resolved dependencies. Calculate artifact
   SHA-256 hashes; retain test results and generate provenance/SBOM when publishing
   automation is adopted. Reproducible builds are a future goal, not asserted.
5. Update the version and release notes, tag the reviewed commit, and publish only
   with maintainer authorization. No automated publication is configured here.

Pre-1.0 APIs may change, but breaking changes need explicit release notes and
migration guidance. Existing parse_text/parse_file AST equality remains structural.
Source locations are optional metadata tied to the original parse, not stable
node identifiers across serialization or pretty-printing.

CLI contract: exit 0 for successful syntactic parse and round trip; exit 1 for
input/processing failure; exit 2 for argument misuse. `--help` exits 0. Error
families: AION1001 lexical, AION1002 syntax, AION1003 file/encoding, AION1004
interpreter processing limit. These are broad families, not future M2 rule codes.

Packaging follows the Python Packaging User Guide:
https://packaging.python.org/en/latest/guides/writing-pyproject-toml/.
Specification conformance guidance:
https://www.w3.org/TR/spec-variability/.
