from __future__ import annotations

import typing as t

from lark import Lark, Token, UnexpectedCharacters, UnexpectedToken
from pyagnostics.exceptions import DiagnosticError
from pyagnostics.spans import LabeledSpan, SourceSpan

from pyhcl2.nodes import Expression, Module, Node, Stmt
from pyhcl2.transformer import ToAstTransformer


def parse_file(file: t.TextIO) -> Module:
    return parse_module(file.read())


def parse_string(text: str, start: str) -> Node:
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
        ast = ToAstTransformer().transform(parse_tree)

    except UnexpectedCharacters as e:
        assert e.pos_in_stream is not None
        raise DiagnosticError(
            code="pyhcl2::lexer::unexpected_character",
            message="The lexer encountered an unexpected character",
            labels=[
                LabeledSpan(
                    SourceSpan(e.pos_in_stream, e.pos_in_stream + 1),
                    "Unexpected character",
                )
            ],
        ) from None
    except UnexpectedToken as e:
        if e.token.type == "$END":
            raise DiagnosticError(
                code="pyhcl2::parser::unexpected_eof",
                message="The parser expected a token, but the input ended",
                labels=[
                    LabeledSpan(
                        SourceSpan(e.token.start_pos, e.token.end_pos), "Unexpected EOF"
                    )
                ],
            ) from e
        else:
            assert isinstance(e.token, Token)
            assert e.token.start_pos is not None
            assert e.token.end_pos is not None
            if e.token.value == "\n":
                raise DiagnosticError(
                    code="pyhcl2::parser::unexpected_newline",
                    message="The parser encountered an unexpected newline",
                    labels=[
                        LabeledSpan(
                            SourceSpan(e.token.start_pos, e.token.end_pos),
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
                            SourceSpan(e.token.start_pos, e.token.end_pos),
                            "Unexpected token",
                        )
                    ],
                    notes=[
                        f"Got {e.token.value!r} instead",
                    ],
                ) from None

    return t.cast(Node, ast)


def parse_module(text: str) -> Module:
    return Module(
        t.cast(list[Stmt], parse_string(text, start="start")),
        span=SourceSpan(0, len(text)),
    )


def parse_expr(text: str) -> Expression:
    return t.cast(Expression, parse_string(text, start="start_expr"))


def parse_expr_or_stmt(text: str) -> Expression | Stmt:
    return t.cast(Expression | Stmt, parse_string(text, start="start_expr_or_stmt"))
