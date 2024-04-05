import typing as t
from pathlib import Path

from lark import Lark

from pyhcl2._ast import Attribute, Expression, Module
from pyhcl2.transformer import ToAstTransformer

PARSER_FILE = Path(__file__).absolute().resolve().parent / ".lark_cache.bin"


def parse_file(file: t.TextIO) -> Module:
    return parse_module(file.read())


def parse_string(text: str, start: str) -> any:
    ast = Lark.open(
        "hcl2.lark",
        parser="lalr",
        start=start,
        cache=str(PARSER_FILE) + "." + start,  # Disable/Delete file to effect changes to the grammar
        rel_to=__file__,
        propagate_positions=True,
        transformer=ToAstTransformer(),
    ).parse(text)

    # noinspection PyTypeChecker
    return ast


def parse_module(text: str) -> Module:
    return Module(parse_string(text + "\n", start="start"))


def parse_expr(text: str) -> Expression:
    return parse_string(text, start="start_expr")


def parse_expr_or_attribute(text: str) -> Expression | Attribute:
    return parse_string(text, start="start_expr_or_attribute")
