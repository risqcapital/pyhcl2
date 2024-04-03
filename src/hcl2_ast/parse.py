import typing as t
from pathlib import Path

from lark import Lark

from hcl2_ast._ast import Module, Stmt
from hcl2_ast.transformer import ToAstTransformer

PARSER_FILE = Path(__file__).absolute().resolve().parent / ".lark_cache.bin"


def parse_file(file: t.TextIO) -> Module:
    return parse_string(file.read())


def parse_string(text: str) -> Module:
    ast = Lark.open(
        "hcl2.lark",
        parser="lalr",
        cache=str(PARSER_FILE),  # Disable/Delete file to effect changes to the grammar
        rel_to=__file__,
        propagate_positions=True,
        transformer=ToAstTransformer(),
    ).parse(text + "\n")

    # noinspection PyTypeChecker
    return Module(ast)


if __name__ == "__main__":
    PARSER_FILE.unlink(missing_ok=True)
    while True:
        text = input("> ")

        try:
            print(parse_string(text + "\n").pformat())
        except Exception as e:
            print(e)
