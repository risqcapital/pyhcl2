from __future__ import annotations

import sys
from collections.abc import Sequence
from pathlib import Path
from typing import (
    Any,
    Callable,
    ItemsView,
    Iterable,
    Iterator,
    Mapping,
    MutableMapping,
    NoReturn,
    Self,
)

from pyhcl2 import Block, Node
from pyhcl2.eval import EvaluationScope, Evaluator
from pyhcl2.parse import parse_file


class IntrinsicFunctionTracker(Mapping):
    def __getattr__(self, item: str) -> Callable[..., None]:
        return lambda *args: None

    def __getitem__(self, item: str) -> Callable[..., None]:
        return lambda *args: None

    def __contains__(self, item: object) -> bool:
        return True

    def __iter__(self) -> Iterator[Self]:
        return iter(())

    def __len__(self) -> int:
        return 0


class VisitedVariablesTracker(Sequence, MutableMapping, Iterable):
    key: str | None
    children: list[VisitedVariablesTracker]

    def __init__(self, key: str | None = None) -> None:
        self.key = key
        self.children = []

    def __repr__(self) -> str:
        return f"VisitedVariablesTracker({self.key})"

    def get_visited_variables(
        self, keys: tuple[str, ...] = tuple()
    ) -> set[tuple[str, ...]]:
        dirty_children = set()
        key_tuple = (*keys, self.key) if self.key else keys

        if self.key:
            dirty_children.add(key_tuple)

        for child in self.children:
            dirty_children.update(child.get_visited_variables(key_tuple))

        return dirty_children

    def __getitem__(self, key: Any) -> VisitedVariablesTracker:  # noqa: ANN401
        # When a key is accessed, we create a new child node to track the access
        child = VisitedVariablesTracker(key=str(key))
        self.children.append(child)
        return child

    def __setitem__(self, key: Any, value: Any) -> None:  # noqa: ANN401
        # We don't actually store any values, so this is a no-op
        pass

    def __delitem__(self, key: Any) -> None:  # noqa: ANN401
        # We don't actually store any values, so this is a no-op
        pass

    def __iter__(self) -> Iterator[Self]:
        # Pretend to be a sequence of one element when iterated over
        yield self

    def __hash__(self) -> int:
        # We need to be hashable to be used as a key in a dictionary
        return id(self)

    def __len__(self) -> int:
        # Pretend to have a non-zero so bool(self) returns True
        return 1

    def items(self) -> ItemsView[Self, Self]:
        # Pretend to be a mapping of self to self
        return {self: self}.items()

    def _not_implemented(self, *_args: Any, **_kwargs: Any) -> NoReturn:  # noqa: ANN401
        raise NotImplementedError

    __contains__ = _not_implemented
    index = _not_implemented
    count = _not_implemented
    get = _not_implemented  # type: ignore
    keys = _not_implemented
    values = _not_implemented

    def _return_self(self, *_args: Any, **_kwargs: Any) -> Self:  # noqa: ANN401
        return self

    __add__ = _return_self
    __sub__ = _return_self
    __mul__ = _return_self
    __truediv__ = _return_self
    __mod__ = _return_self
    __eq__ = _return_self  # type: ignore
    __ne__ = _return_self  # type: ignore
    __lt__ = _return_self
    __gt__ = _return_self
    __le__ = _return_self
    __ge__ = _return_self
    __and__ = _return_self
    __or__ = _return_self
    __neg__ = _return_self
    __reversed__ = _return_self  # type: ignore


def resolve_variable_references(node: Node) -> set[tuple[str, ...]]:
    visited_variables_tracker = VisitedVariablesTracker()
    # noinspection PyTypeChecker
    scope = EvaluationScope(variables=visited_variables_tracker)
    Evaluator(
        can_short_circuit=False, intrinsic_functions=IntrinsicFunctionTracker()
    ).eval(node, scope)

    return visited_variables_tracker.get_visited_variables()


if __name__ == "__main__":
    ast = parse_file(open(Path(sys.argv[1])))

    blocks = [stmt for stmt in ast.body if isinstance(stmt, Block)]

    for block_under_test in blocks:
        variable_references = resolve_variable_references(block_under_test)

        for dirty_child in variable_references:
            print(block_under_test.key(), "depends_on", dirty_child)
