from __future__ import annotations

import typing as t
from contextlib import AbstractContextManager
from dataclasses import dataclass
from types import TracebackType

from lark import Lark, Token, UnexpectedCharacters, UnexpectedToken
from pyagnostics.exceptions import DiagnosticError
from pyagnostics.source import InMemorySource, attach_diagnostic_source_code
from pyagnostics.spans import LabeledSpan, SourceId, SourceSpan

from pyhcl2.nodes import Expression, Module, Node, Stmt
from pyhcl2.rich_utils import HclHighlighter
from pyhcl2.transformer import ToAstTransformer


def parse_file(file: t.TextIO, source_id: SourceId | None = None) -> Module:
    return parse_module(file.read(), source_id=source_id)


@dataclass
class ParsedModule(AbstractContextManager[Module]):
    module: Module
    source_code: InMemorySource
    source_id: SourceId
    _context: AbstractContextManager[SourceId] | None = None

    def __enter__(self) -> Module:
        self._context = attach_diagnostic_source_code(
            self.source_code,
            highlighter=HclHighlighter(self.module),
            source_id=self.source_id,
        )
        self._context.__enter__()
        return self.module

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> bool | None:
        if self._context is None:
            return None
        return self._context.__exit__(exc_type, exc, tb)


def parse_module_with_source(text: str, name: str | None = None) -> ParsedModule:
    source_id = SourceId()
    source_code = InMemorySource(text, name=name)
    with attach_diagnostic_source_code(source_code, source_id=source_id):
        module = parse_module(text, source_id=source_id)
    return ParsedModule(module=module, source_code=source_code, source_id=source_id)


def parse_string(text: str, start: str, source_id: SourceId | None = None) -> Node:
    resolved_source_id = source_id or SourceId()
    try:
        lark = Lark.open(
            "hcl2.lark",
            parser="lalr",
            start=start,
            cache=True,
            rel_to=__file__,
            propagate_positions=True,
        )
        parse_tree = lark.parse(text)
        ast = ToAstTransformer(source_id=resolved_source_id).transform(parse_tree)

    except UnexpectedCharacters as e:
        assert e.pos_in_stream is not None
        label_span = SourceSpan(
            e.pos_in_stream, e.pos_in_stream + 1, source_id=resolved_source_id
        )
        raise DiagnosticError(
            code="pyhcl2::lexer::unexpected_character",
            message="The lexer encountered an unexpected character",
            labels=[
                LabeledSpan(
                    label_span,
                    "Unexpected character",
                )
            ],
        ) from None
    except UnexpectedToken as e:
        if e.token.type == "$END":
            label_span = SourceSpan(
                e.token.start_pos, e.token.end_pos, source_id=resolved_source_id
            )
            raise DiagnosticError(
                code="pyhcl2::parser::unexpected_eof",
                message="The parser expected a token, but the input ended",
                labels=[LabeledSpan(label_span, "Unexpected EOF")],
            ) from e
        else:
            assert isinstance(e.token, Token)
            assert e.token.start_pos is not None
            assert e.token.end_pos is not None
            label_span = SourceSpan(
                e.token.start_pos, e.token.end_pos, source_id=resolved_source_id
            )
            if e.token.value == "\n":
                raise DiagnosticError(
                    code="pyhcl2::parser::unexpected_newline",
                    message="The parser encountered an unexpected newline",
                    labels=[
                        LabeledSpan(
                            label_span,
                            "Unexpected newline",
                        )
                    ],
                ) from None
            else:
                raise DiagnosticError(
                    code="pyhcl2::parser::unexpected_token",
                    message="The parser encountered an unexpected token",
                    labels=[
                        LabeledSpan(
                            label_span,
                            "Unexpected token",
                        )
                    ],
                    notes=[
                        f"Got {e.token.value!r} instead",
                    ],
                ) from None

    return t.cast(Node, ast)


def parse_module(text: str, source_id: SourceId | None = None) -> Module:
    resolved_source_id = source_id or SourceId()
    return Module(
        t.cast(
            list[Stmt], parse_string(text, start="start", source_id=resolved_source_id)
        ),
        span=SourceSpan(
            0,
            len(text),
            source_id=resolved_source_id,
        ),
    )


def parse_expr(text: str, source_id: SourceId | None = None) -> Expression:
    resolved_source_id = source_id or SourceId()
    return t.cast(
        Expression,
        parse_string(text, start="start_expr", source_id=resolved_source_id),
    )


def parse_expr_or_stmt(
    text: str, source_id: SourceId | None = None
) -> Expression | Stmt:
    resolved_source_id = source_id or SourceId()
    return t.cast(
        Expression | Stmt,
        parse_string(text, start="start_expr_or_stmt", source_id=resolved_source_id),
    )
