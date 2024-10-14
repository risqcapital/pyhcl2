from __future__ import annotations

import typing as t

from lark import Lark, UnexpectedCharacters, UnexpectedToken

from pyhcl2.nodes import Expression, Module, Node, Stmt
from pyhcl2.pymiette import Diagnostic, LabeledSpan, SourceSpan
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
        raise Diagnostic(
            code="pyhcl2::lexer::unexpected_character",
            message="The lexer encountered an unexpected character",
            labels=[LabeledSpan(SourceSpan(e.pos_in_stream, e.pos_in_stream + 1), "Unexpected character")],
        ) from e
    except UnexpectedToken as e:
        if e.token.type == "$END":
            raise Diagnostic(
                code="pyhcl2::parser::unexpected_eof",
                message="The parser expected a token, but the input ended",
                labels=[LabeledSpan(SourceSpan(e.token.start_pos, e.token.end_pos), "Unexpected EOF")],
            ) from e
        else:
            raise Diagnostic(
                code="pyhcl2::parser::unexpected_token",
                message="The parser encountered an unexpected token",
                labels=[LabeledSpan(SourceSpan(e.token.start_pos, e.token.end_pos), "Unexpected token")],
            )

    return t.cast(Node, ast)


def parse_module(text: str) -> Module:
    return Module(
        t.cast(list[Stmt], parse_string(text, start="start")),
        start_pos=0,
        end_pos=len(text),
    )


def parse_expr(text: str) -> Expression:
    return t.cast(Expression, parse_string(text, start="start_expr"))


def parse_expr_or_stmt(text: str) -> Expression | Stmt:
    return t.cast(
        Expression | Stmt, parse_string(text, start="start_expr_or_stmt")
    )
