from __future__ import annotations

import typing as t

from lark import Lark

from pyhcl2._ast import Attribute, Expression, Module, Node, Stmt
from pyhcl2.transformer import ToAstTransformer


def parse_file(file: t.TextIO) -> Module:
    return parse_module(file.read())


def parse_string(text: str, start: str) -> Node:
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

    return t.cast(Node, ast)


def parse_module(text: str) -> Module:
    return Module(
        t.cast(list[Stmt], parse_string(text, start="start")),
        start_pos=0,
        end_pos=len(text),
    )


def parse_expr(text: str) -> Expression:
    return t.cast(Expression, parse_string(text, start="start_expr"))


def parse_expr_or_attribute(text: str) -> Expression | Attribute:
    return t.cast(
        Expression | Attribute, parse_string(text, start="start_expr_or_attribute")
    )
