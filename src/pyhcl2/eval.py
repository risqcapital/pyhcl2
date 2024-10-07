from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Iterable,
    MutableMapping,
    Self,
    TypeAliasType,
    cast,
)

from pyhcl2 import BinaryExpression
from pyhcl2._ast import (
    Array,
    Attribute,
    AttrSplat,
    Block,
    Conditional,
    ForObjectExpression,
    ForTupleExpression,
    FunctionCall,
    GetAttr,
    GetAttrKey,
    GetIndex,
    GetIndexKey,
    Identifier,
    IndexSplat,
    Literal,
    LiteralValue,
    Node,
    Object,
    Parenthesis,
    UnaryExpression,
)

if TYPE_CHECKING:
    # Mypy doesn't properly support TypeAliasType yet
    Value = LiteralValue | Mapping[str, "Value"] | Sequence["Value"]
else:
    Value = TypeAliasType(
        "Value", LiteralValue | Mapping[str, "Value"] | Sequence["Value"]
    )


@dataclass
class EvaluationScope:
    parent: Self | None = None
    variables: MutableMapping[str, Value] = field(default_factory=dict)

    def __getitem__(self, item: str) -> Value:
        try:
            return self.variables[item]
        except KeyError:
            pass
        if self.parent:
            return self.parent[item]
        raise ValueError(f"Variable {item} not set")

    def __setitem__(self, key: str, value: Value) -> None:
        self.variables[key] = value

    def __contains__(self, item: Value) -> bool:
        if item in self.variables:
            return True
        if self.parent:
            return item in self.parent
        return False

    def child(self) -> EvaluationScope:
        return EvaluationScope(parent=self)


camel_to_snake_pattern = re.compile(r"(?<!^)(?=[A-Z])")


# noinspection PyMethodMayBeStatic
@dataclass
class Evaluator:
    # Note: We MUST not short-circuit if self.can_short_circuit is False
    can_short_circuit: bool = True
    intrinsic_functions: Mapping[str, Callable[..., Value]] = field(
        default_factory=dict
    )

    def eval(self, expr: Node, scope: EvaluationScope = EvaluationScope()) -> Value:
        method = (
            f"_eval_{camel_to_snake_pattern.sub('_', expr.__class__.__name__).lower()}"
        )
        # print(f"Calling {method} with {expr}")
        if hasattr(self, method):
            return getattr(self, method)(expr, scope)
        else:
            raise ValueError(f"Unsupported expression type {expr}")

    def _eval_block(self, node: Block, scope: EvaluationScope) -> Value:
        result: dict[str, Value] = {}

        for stmt in node.body:
            if isinstance(stmt, Block):
                key = stmt.key_path
                value = self.eval(stmt, scope.child())
                result_iter = result
                for k in key[:-1]:
                    result_iter = cast(dict[str, Value], result_iter.setdefault(k, {}))
                cast(list[Value], result_iter.setdefault(key[-1], [])).append(value)

            elif isinstance(stmt, Attribute):
                key = stmt.key_path
                value = self.eval(stmt, scope.child())
                result_iter = result
                for k in key[:-1]:
                    result_iter = cast(dict[str, Value], result_iter.setdefault(k, {}))
                result_iter[key[-1]] = value
            else:
                raise TypeError(f"Unsupported statement type {stmt}")

        return result

    def _eval_attribute(self, node: Attribute, scope: EvaluationScope) -> Value:
        value = self.eval(node.value, scope)
        scope[node.key.name] = value
        return value

    def _eval_binary_expression(
        self, node: BinaryExpression, scope: EvaluationScope
    ) -> Value:
        # Note: We MUST not short-circuit if self.can_short_circuit is False
        # TODO: Implement short-circuiting ONLY if self.can_short_circuit is True
        left = self.eval(node.left, scope)
        right = self.eval(node.right, scope)

        operations = {
            "+": "__add__",
            "-": "__sub__",
            "*": "__mul__",
            "/": "__truediv__",
            "%": "__mod__",
            "==": "__eq__",
            "!=": "__ne__",
            "<": "__lt__",
            ">": "__gt__",
            "<=": "__le__",
            ">=": "__ge__",
            "&&": lambda x, y: x and y,
            "||": lambda x, y: x or y,
        }

        operation = operations[node.op.type]
        if callable(operation):
            return operation(left, right)
        else:
            assert isinstance(operation, str)
            return getattr(left, operation)(right)

    def _eval_unary_expression(
        self, node: UnaryExpression, scope: EvaluationScope
    ) -> Value:
        value = self.eval(node.expr, scope)

        operations = {
            "-": "__neg__",
            "!": lambda x: not x,
        }

        operation = operations[node.op.type]
        if callable(operation):
            return operation(value)
        else:
            assert isinstance(operation, str)
            return getattr(value, operation)()

    def _eval_get_attr(self, node: GetAttr, scope: EvaluationScope) -> Value:
        on = self.eval(node.on, scope)
        return self._evaluate_get_attr(on, node.key, scope)

    def _evaluate_get_attr(
        self, on: Value, key: GetAttrKey, _scope: EvaluationScope
    ) -> Value:
        key_value = key.ident.name

        try:
            assert isinstance(on, Mapping)
            return on[key_value]
        except KeyError:
            raise ValueError(f"Key {key_value} not found in {on}")
        except IndexError:
            raise ValueError(f"Index {key_value} out of bounds in {on}")

    def _eval_get_index(self, node: GetIndex, scope: EvaluationScope) -> Value:
        on = self.eval(node.on, scope)
        return self._evaluate_get_index(on, node.key, scope)

    def _evaluate_get_index(
        self, on: Value, key: GetIndexKey, scope: EvaluationScope
    ) -> Value:
        key_value = self.eval(key.expr, scope)

        # TODO: Figure out a better way to handle this
        if str(key_value.__class__.__name__) == "VisitedVariablesTracker":
            return None

        try:
            if isinstance(on, Mapping):
                assert isinstance(key_value, str)
                return on[key_value]
            elif isinstance(on, Sequence) and not isinstance(on, str):
                assert isinstance(key_value, int)
                return on[key_value]
            else:
                raise TypeError(f"Invalid index operation on {type(on)} {on}")
        except KeyError:
            raise ValueError(f"Key {key_value} not found in {on}")
        except IndexError:
            raise ValueError(f"Index {key_value} out of bounds in {on}")

    def _eval_literal(self, node: Literal, _ctx: EvaluationScope) -> Value:
        return node.value

    def _eval_identifier(self, node: Identifier, scope: EvaluationScope) -> Value:
        try:
            return scope[node.name]
        except KeyError:
            raise ValueError(f"Variable {node.name} not set")

    def _eval_object(self, node: Object, scope: EvaluationScope) -> Value:
        result: dict[str, Value] = {}
        for key_expr, value_expr in node.fields.items():
            key: Value
            match key_expr:
                case Identifier(name):
                    key = name
                case Literal(str(literal)):
                    key = literal
                case Parenthesis(expr):
                    key = self.eval(expr, scope)
                    if not isinstance(key, str):
                        raise TypeError(f"Invalid key expression {key_expr}")
                case _:
                    raise ValueError(f"Invalid key expression {key_expr}")

            value = self.eval(value_expr, scope)
            result[key] = value
        return result

    def _eval_array(self, node: Array, scope: EvaluationScope) -> Value:
        return [self.eval(item, scope) for item in node.values]

    def _eval_function_call(self, func: FunctionCall, scope: EvaluationScope) -> Value:
        if func.var_args:
            raise NotImplementedError("Var arg function calls are not supported yet")

        if func.ident.name in self.intrinsic_functions:
            return self.intrinsic_functions[func.ident.name](
                *[self.eval(arg, scope) for arg in func.args]
            )

        raise NotImplementedError(f"Unsupported function call {func.ident.name}")

    def _eval_conditional(self, node: Conditional, scope: EvaluationScope) -> Value:
        condition = self.eval(node.cond, scope)
        # Note: We MUST not short-circuit if self.can_short_circuit is False
        # TODO: Implement short-circuiting ONLY if self.can_short_circuit is True
        then_result = self.eval(node.then_expr, scope)
        else_result = self.eval(node.else_expr, scope)

        if condition:
            return then_result
        else:
            return else_result

    def _eval_parenthesis(self, node: Parenthesis, scope: EvaluationScope) -> Value:
        return self.eval(node.expr, scope)

    def _eval_for_tuple_expression(
        self, node: ForTupleExpression, scope: EvaluationScope
    ) -> Value:
        collection = self.eval(node.collection, scope)
        result: list[Value] = []

        if collection is None:
            return result

        iterator: Iterable[tuple[Any, Value]] | None = (
            collection.items()
            if isinstance(collection, Mapping)
            else enumerate(collection)
            if isinstance(collection, Sequence) and not isinstance(collection, str)
            else None
        )  # type: ignore

        if iterator is None:
            raise TypeError(f"Type of {collection} is not iterable")

        for k, v in iterator:
            child_ctx = scope.child()
            child_ctx[node.value_ident.name] = v
            if node.key_ident:
                child_ctx[node.key_ident.name] = k

            condition = (
                self.eval(node.condition, child_ctx)
                if node.condition is not None
                else True
            )
            # Note: We MUST not short-circuit if self.can_short_circuit is False
            # TODO: Implement short-circuiting ONLY if self.can_short_circuit is True
            value = self.eval(node.value, child_ctx)
            if condition is True:
                result.append(value)

        return result

    def _eval_for_object_expression(
        self, node: ForObjectExpression, scope: EvaluationScope
    ) -> Value:
        if node.grouping_mode:
            raise NotImplementedError("Grouping mode is not supported yet")

        collection = self.eval(node.collection, scope)
        result: dict[str, Value] = {}

        if collection is None:
            return result

        iterator: Iterable[tuple[str | int, Value]] | None = (
            collection.items()
            if hasattr(collection, "items")
            else enumerate(collection)
            if isinstance(collection, Sequence) and not isinstance(collection, str)
            else None
        )

        if iterator is None:
            raise TypeError(f"Type of {collection} is not iterable")

        for k, v in iterator:
            child_ctx = scope.child()
            child_ctx[node.value_ident.name] = v
            if node.key_ident:
                child_ctx[node.key_ident.name] = k

            condition = (
                self.eval(node.condition, child_ctx)
                if node.condition is not None
                else True
            )
            # Note: We MUST NOT short-circuit evals so that we can be used as a variable tracker
            # TODO: Implement short-circuiting ONLY if self.can_short_circuit is True
            key = self.eval(node.key, child_ctx)
            if not isinstance(key, str):
                raise TypeError(f"Type of {node.key} is not string")
            value = self.eval(node.value, child_ctx)
            if condition is True:
                result[key] = value

        return result

    def _eval_attr_splat(self, node: AttrSplat, scope: EvaluationScope) -> Value:
        on = self.eval(node.on, scope)

        if on is None:
            return []

        if not isinstance(on, Sequence) or isinstance(on, str):
            on = [on]

        values = []

        for v in on:
            value = v
            for key in node.keys:
                value = self._evaluate_get_attr(value, key, scope)
            values.append(value)

        return values

    def _eval_index_splat(self, node: IndexSplat, scope: EvaluationScope) -> Value:
        on = self.eval(node.on, scope)

        if on is None:
            return []

        if not isinstance(on, Sequence) or isinstance(on, str):
            on = [on]

        values = []

        for v in on:
            value = v
            for key in node.keys:
                match key:
                    case GetAttrKey(_):
                        value = self._evaluate_get_attr(value, key, scope)
                    case GetIndexKey(_):
                        value = self._evaluate_get_index(value, key, scope)
            values.append(value)

        return values
