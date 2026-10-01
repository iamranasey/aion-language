"""Semantic diagnostics for the AION v0.1 validator (M2).

Diagnostics retain declaration-qualified locators and optional source spans.
Pass ParsedSource from parse_with_locations to validate for declaration ranges;
plain structural AST callers still work. Ambiguous duplicate declaration names
retain their textual locator without an invented location.

Diagnostics are *collected*, not raised one at a time: ``validate`` reports every
applicable defect so a negative spec surfaces all of its independent problems
(``examples/README.md``). ``AionSemanticError`` bundles the collected list for
callers that prefer an exception.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List
from .source_map import SourceSpan


# Diagnostic codes. Kept as plain string constants (not an Enum) so they are
# trivially serializable into the M3 IR traceability report and printable in a
# diagnostic line without ceremony.
DUPLICATE_ENTITY = "duplicate-entity"
DUPLICATE_ROLE = "duplicate-role"
DUPLICATE_FIELD = "duplicate-field"
DUPLICATE_ACTION = "duplicate-action"
DUPLICATE_RULE = "duplicate-rule"
DANGLING_ACTION = "dangling-action"
DANGLING_ENTITY = "dangling-entity"
DANGLING_ROLE = "dangling-role"
DANGLING_FIELD = "dangling-field"
CONFLICT = "conflict"
UNSUPPORTED_PROOF = "unsupported-proof"
GUARANTEE_FAILED = "guarantee-failed"
TEST_ARITY = "test-arity"
TEST_ARG_MISMATCH = "test-arg-mismatch"
TEST_FAILED = "test-failed"
COMPARISON_TYPE = "comparison-type"
TEST_ROLE_ARGUMENT = "test-role-argument"


@dataclass(frozen=True)
class Diagnostic:
    """A single semantic defect.

    ``code``   one of the constants above (machine-readable).
    ``where``  declaration-qualified locator, e.g. ``"RULE OrderPolicy"``.
    ``message`` human-readable explanation naming the offending construct.
    """

    code: str
    where: str
    message: str
    span: SourceSpan | None = None

    def __str__(self) -> str:  # pragma: no cover - cosmetic
        return f"{self.where}: [{self.code}] {self.message}"


class AionSemanticError(Exception):
    """Raised by callers that want validation failure as an exception.

    Carries the full ``.diagnostics`` list rather than failing on the first
    defect, so the message enumerates every problem found.
    """

    def __init__(self, diagnostics: List[Diagnostic]) -> None:
        self.diagnostics = list(diagnostics)
        joined = "; ".join(str(d) for d in self.diagnostics)
        super().__init__(f"{len(self.diagnostics)} semantic error(s): {joined}")
