import typing as t
from pathlib import Path

from lark import Lark

from hcl2_ast._ast import Module
from hcl2_ast.transformer import ToAstTransformer

PARSER_FILE = Path(__file__).absolute().resolve().parent / ".lark_cache.bin"


def parse_file(file: t.TextIO) -> Module:
    return parse_string(file.read())


def parse_string(text: str) -> Module:
    parse_tree = Lark.open(
        "hcl2.lark",
        parser="lalr",
        cache=str(PARSER_FILE),  # Disable/Delete file to effect changes to the grammar
        rel_to=__file__,
        propagate_positions=True,
    ).parse(text + "\n")

    return Module(ToAstTransformer().transform(parse_tree))
