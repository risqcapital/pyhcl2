from __future__ import annotations

from pyagnostics.spans import SourceId, SourceSpan

from pyhcl2.nodes import Expression, Module, Stmt
from pyhcl2.parse import parse_expr, parse_expr_or_stmt, parse_module

SOURCE_ID = SourceId.unsafe_from_value(1)


def span(start: int, end: int) -> SourceSpan:
    return SourceSpan(start, end, source_id=SOURCE_ID)


def parse_expr_with_id(text: str) -> Expression:
    return parse_expr(text, source_id=SOURCE_ID)


def parse_expr_or_stmt_with_id(text: str) -> Expression | Stmt:
    return parse_expr_or_stmt(text, source_id=SOURCE_ID)


def parse_module_with_id(text: str) -> Module:
    return parse_module(text, source_id=SOURCE_ID)
