from __future__ import annotations

import sys
from collections.abc import Callable, Iterator, Mapping
from pathlib import Path
from typing import (
    Self,
    cast,
)

import rich
from rich.console import NewLine

from pyhcl2.eval import EvaluationScope, Evaluator
from pyhcl2.nodes import Block, Node
from pyhcl2.parse import parse_file
from pyhcl2.rich_utils import Inline
from pyhcl2.values import Unknown, Value


class IntrinsicFunctionTracker(Mapping):
    def __getattr__(self, item: str) -> Callable[..., Value]:
        return lambda *args: Unknown.indirect(*args)

    def __getitem__(self, item: str) -> Callable[..., Value]:
        return lambda *args: Unknown.indirect(*args)

    def __contains__(self, item: object) -> bool:
        return True

    def __iter__(self) -> Iterator[Self]:
        return iter(())

    def __len__(self) -> int:
        return 0


def resolve_variable_references(node: Node) -> set[tuple[str, ...]]:
    # noinspection PyTypeChecker
    scope = EvaluationScope()
    result = Evaluator(intrinsic_functions=IntrinsicFunctionTracker()).eval(node, scope)

    match result.resolve():
        case Unknown() as unknown:
            return set(
                [
                    cast(tuple[str, ...], ref.key)
                    for ref in unknown.references
                    if not any(part is None for part in ref.key)
                ]
            )
        case _:
            return set()


if __name__ == "__main__":
    ast = parse_file(open(Path(sys.argv[1])))
    rich.print(ast)

    blocks = [stmt for stmt in ast.body if isinstance(stmt, Block)]

    for block_under_test in blocks:
        variable_references = resolve_variable_references(block_under_test)

        for dirty_child in variable_references:
            rich.print(
                Inline(
                    ".".join(block_under_test.key()),
                    " depends_on ",
                    ".".join(dirty_child),
                    NewLine(),
                )
            )
