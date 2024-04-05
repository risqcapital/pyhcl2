from collections.abc import Sequence
from typing import Mapping, Self

from pyhcl2 import Block
from pyhcl2.eval import EvaluationScope, Evaluator
from pyhcl2.parse import parse_file


class VisitedVariablesTracker(Sequence, Mapping):
    key: str | None
    children: list[Self]

    def __init__(self, key: str | None = None):
        self.key = key
        self.children = []

    def __repr__(self):
        return f"VisitedVariablesTracker({self.key})"

    def get_visited_variables(self, keys=tuple()):
        dirty_children = []
        key_tuple = keys + (self.key,) if self.key else keys

        if self.key:
            dirty_children.append(key_tuple)

        for child in self.children:
            dirty_children.extend(child.get_visited_variables(key_tuple))

        return dirty_children

    def __getitem__(self, key):
        # When a key is accessed, we create a new child node to track the access
        child = VisitedVariablesTracker(key=str(key))
        self.children.append(child)
        return child

    def __setitem__(self, key, value):
        # We don't actually store any values, so this is a no-op
        pass

    def __iter__(self):
        # Pretend to be a sequence of one element when iterated over
        yield self

    def __hash__(self):
        # We need to be hashable to be used as a key in a dictionary
        return id(self)

    def __len__(self):
        # Pretend to have a non-zero so bool(self) returns True
        return 1

    def items(self):
        # Pretend to be a mapping of self to self
        return {self: self}.items()

    def _not_implemented(self, *_args, **_kwargs):
        raise NotImplementedError

    __contains__ = _not_implemented
    index = _not_implemented
    count = _not_implemented
    get = _not_implemented
    keys = _not_implemented
    values = _not_implemented

    def _return_self(self, *_args, **_kwargs):
        return self

    __add__ = _return_self
    __sub__ = _return_self
    __mul__ = _return_self
    __truediv__ = _return_self
    __mod__ = _return_self
    __eq__ = _return_self
    __ne__ = _return_self
    __lt__ = _return_self
    __gt__ = _return_self
    __le__ = _return_self
    __ge__ = _return_self
    __and__ = _return_self
    __or__ = _return_self
    __neg__ = _return_self
    __reversed__ = _return_self


if __name__ == '__main__':
    ast = parse_file(open("/home/ben/dev/risq/cicd-framework-test/cicd.hcl"))

    blocks = [stmt for stmt in ast.body if isinstance(stmt, Block)]

    for block_under_test in blocks:
        visited_variables_tracker = VisitedVariablesTracker()

        # noinspection PyTypeChecker
        scope = EvaluationScope(variables=visited_variables_tracker)
        Evaluator(can_short_circuit=False).eval(block_under_test, scope)

        for dirty_child in visited_variables_tracker.get_visited_variables():
            print(block_under_test.key(), "depends_on", dirty_child)
