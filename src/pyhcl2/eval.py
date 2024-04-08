from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Self

from pyhcl2 import BinaryOp
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
    UnaryOp,
)

Value = LiteralValue | dict[str, LiteralValue] | list[LiteralValue]


@dataclass
class EvaluationScope:
    parent: Self | None = None
    variables: dict[str, Value] = field(default_factory=dict)

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
        return item in self.variables or (self.parent and item in self.parent)

    def child(self) -> Self:
        return EvaluationScope(parent=self)


camel_to_snake_pattern = re.compile(r"(?<!^)(?=[A-Z])")


# noinspection PyMethodMayBeStatic
@dataclass
class Evaluator:
    # Note: We MUST not short-circuit if self.can_short_circuit is False
    can_short_circuit: bool = True

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
        for stmt in node.body:
            self.eval(stmt, scope.child())
        return None

    def _eval_attribute(self, node: Attribute, scope: EvaluationScope) -> Value:
        value = self.eval(node.value, scope)
        scope[node.key] = value
        return None

    def _eval_binary_op(self, node: BinaryOp, scope: EvaluationScope) -> Value:
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

        operation = operations[node.op]
        if callable(operation):
            return operation(left, right)
        else:
            return getattr(left, operation)(right)

    def _eval_unary_op(self, node: UnaryOp, scope: EvaluationScope) -> Value:
        value = self.eval(node.expr, scope)

        operations = {
            "-": "__neg__",
            "!": lambda x: not x,
        }

        operation = operations[node.op]
        if callable(operation):
            return operation(value)
        else:
            return getattr(value, operation)()

    def _eval_get_attr(self, node: GetAttr, scope: EvaluationScope) -> Value:
        on = self.eval(node.on, scope)
        return self._evaluate_get_attr(on, node.key, scope)

    def _evaluate_get_attr(
        self, on: Value, key: GetAttrKey, _scope: EvaluationScope
    ) -> Value:
        key = key.ident.name

        try:
            return on[key]
        except KeyError:
            raise ValueError(f"Key {key} not found in {on}")
        except IndexError:
            raise ValueError(f"Index {key} out of bounds in {on}")

    def _eval_get_index(self, node: GetIndex, scope: EvaluationScope) -> Value:
        on = self.eval(node.on, scope)
        return self._evaluate_get_index(on, node.key, scope)

    def _evaluate_get_index(
        self, on: Value, key: GetIndexKey, scope: EvaluationScope
    ) -> Value:
        key = self.eval(key.expr, scope)

        try:
            return on[key]
        except KeyError:
            raise ValueError(f"Key {key} not found in {on}")
        except IndexError:
            raise ValueError(f"Index {key} out of bounds in {on}")

    def _eval_literal(self, node: Literal, _ctx: EvaluationScope) -> Value:
        return node.value

    def _eval_identifier(self, node: Identifier, scope: EvaluationScope) -> Value:
        try:
            return scope[node.name]
        except KeyError:
            raise ValueError(f"Variable {node.name} not set")

    def _eval_object(self, node: Object, scope: EvaluationScope) -> Value:
        result = {}
        for key_expr, value_expr in node.fields.items():
            match key_expr:
                case Identifier(name):
                    key = name
                case Parenthesis(node):
                    key = self.eval(node, scope)
                case _:
                    raise ValueError(f"Invalid key expression {key_expr}")

            value = self.eval(value_expr, scope)
            result[key] = value
        return result

    def _eval_array(self, node: Array, scope: EvaluationScope) -> Value:
        return [self.eval(item, scope) for item in node.values]

    def _eval_function_call(self, node: FunctionCall, scope: EvaluationScope) -> Value:
        raise NotImplementedError("Function calls are not supported yet")

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
        result = []

        iterator = (
            collection.items()
            if isinstance(collection, Mapping)
            else enumerate(collection)
        )

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
        result = {}

        iterator = (
            collection.items()
            if hasattr(collection, "items")
            else enumerate(collection)
        )

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
            value = self.eval(node.value, child_ctx)
            if condition is True:
                result[key] = value

        return result

    def _eval_attr_splat(self, node: AttrSplat, scope: EvaluationScope) -> Value:
        on = self.eval(node.on, scope)

        # Note: `str` is a `Sequence`, so we need to exclude it
        if not isinstance(on, Sequence) and not isinstance(on, str):
            if on is None:
                on = []
            else:
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

        # Note: `str` is a `Sequence`, so we need to exclude it
        if not isinstance(on, Sequence) and not isinstance(on, str):
            if on is None:
                on = []
            else:
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
