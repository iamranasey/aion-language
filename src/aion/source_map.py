"""Source metadata kept outside AST structural equality."""
from dataclasses import dataclass
from functools import wraps
from .ast_nodes import Spec


@dataclass(frozen=True)
class SourceSpan:
    """One-based start and exclusive end coordinates in the original source."""
    line: int
    column: int
    end_line: int
    end_column: int


@dataclass
class ParsedSource:
    spec: Spec
    spans: dict[int, SourceSpan]

    def span_for(self, node: object) -> SourceSpan:
        """Look up an original node; copied or re-parsed nodes have new identity."""
        return self.spans[id(node)]


def located(method):
    """Record the consumed token range for a production's result node."""
    @wraps(method)
    def wrapped(self, *args, **kwargs):
        first = self._peek()
        result = method(self, *args, **kwargs)
        last = self._tokens[self._i - 1]
        self.spans[id(result)] = SourceSpan(
            first.line, first.column, last.end_line, last.end_column
        )
        return result
    return wrapped
