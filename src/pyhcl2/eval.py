from __future__ import annotations

import re
from collections.abc import Callable, Iterable, Mapping, MutableMapping
from dataclasses import dataclass, field
from typing import Self

from pyagnostics.exceptions import DiagnosticError
from pyagnostics.spans import LabeledSpan, SourceSpan
from rich.console import Group
from rich.text import Text

from pyhcl2.nodes import (
    ArrayExpression,
    Attribute,
    AttrSplat,
    BinaryExpression,
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
    Node,
    ObjectExpression,
    Parenthesis,
    UnaryExpression,
)
from pyhcl2.rich_utils import Inline
from pyhcl2.values import Array, Boolean, Integer, Null, Object, String, Unknown, Value

camel_to_snake_pattern = re.compile(r"(?<!^)(?=[A-Z])")


@dataclass
class EvaluationScope:
    parent: Self | None = None
    variables: MutableMapping[str, Value] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for key, value in self.variables.items():
            if not isinstance(value, Value):
                raise TypeError(f"Variable {key} is not a Value")

    def __getitem__(self, item: str) -> Value:
        try:
            return self.variables[item]
        except KeyError:
            pass
        if self.parent:
            return self.parent[item]
        raise KeyError(f"Variable {item} not set")

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


@dataclass
class Evaluator:
    intrinsic_functions: Mapping[str, Callable[..., Value]] = field(
        default_factory=dict
    )

    def eval(self, expr: Node, scope: EvaluationScope = EvaluationScope()) -> Value:  # noqa: PLR0912
        match expr:
            case Block() as expr:
                result = self._eval_block(expr, scope)
            case Literal() as expr:
                result = self._eval_literal(expr, scope)
            case ArrayExpression() as expr:
                result = self._eval_array_expression(expr, scope)
            case ObjectExpression() as expr:
                result = self._eval_object_expression(expr, scope)
            case Identifier() as expr:
                result = self._eval_identifier(expr, scope)
            case Parenthesis() as expr:
                result = self._eval_parenthesis(expr, scope)
            case BinaryExpression() as expr:
                result = self._eval_binary_expression(expr, scope)
            case UnaryExpression() as expr:
                result = self._eval_unary_expression(expr, scope)
            case Attribute() as expr:
                result = self._eval_attribute(expr, scope)
            case GetAttr() as expr:
                result = self._eval_get_attr(expr, scope)
            case GetIndex() as expr:
                result = self._eval_get_index(expr, scope)
            case FunctionCall() as expr:
                result = self._eval_function_call(expr, scope)
            case Conditional() as expr:
                result = self._eval_conditional(expr, scope)
            case ForTupleExpression() as expr:
                result = self._eval_for_tuple_expression(expr, scope)
            case ForObjectExpression() as expr:
                result = self._eval_for_object_expression(expr, scope)
            case AttrSplat() as expr:
                result = self._eval_attr_splat(expr, scope)
            case IndexSplat() as expr:
                result = self._eval_index_splat(expr, scope)
            case _:
                raise DiagnosticError(
                    code="pyhcl2::evaluator::unsupported_node",
                    message=f"Unsupported node type {expr.__class__.__name__}",
                    labels=[
                        LabeledSpan(expr.span, "unsupported expression"),
                    ],
                )

        # rich.print(Inline(Text("eval", style=STYLE_FUNCTION), "(", expr, "):  ", result, NewLine()))
        if result.span is None:
            result = result.with_span(expr.span)
        return result

    def _eval_block(self, block: Block, scope: EvaluationScope) -> Value:
        result: dict[String, Value] = {}

        for stmt in block.body:
            match stmt:
                case Attribute() as attr:
                    key = attr.key.as_string()
                    value = self.eval(stmt, scope.child())

                    if key in result:
                        raise DiagnosticError(
                            code="pyhcl2::evaluator::block::duplicate_key",
                            message="Duplicate key in block",
                            labels=[LabeledSpan(attr.key.span, "duplicate key")],
                        )

                    result[key] = value

                case Block() as block:
                    keys = block.keys
                    value = self.eval(block, scope.child())

                    mapping: MutableMapping[String, Value] = result
                    for key in keys[:-1]:
                        match mapping.get(key, None):
                            case None:
                                mapping = mapping[key] = Object({})
                            case Object() as obj:
                                mapping = obj
                            case _:
                                raise DiagnosticError(
                                    code="pyhcl2::evaluator::block::key_conflict",
                                    message="Key conflict in block",
                                    labels=[LabeledSpan(block.span, "key conflict")],
                                )

                    match mapping.get(keys[-1], None):
                        case None:
                            mapping[keys[-1]] = Array([value])
                        case Array() as array:
                            array.append(value)
                        case _:
                            raise DiagnosticError(
                                code="pyhcl2::evaluator::block::key_conflict",
                                message="Key conflict in block",
                                labels=[LabeledSpan(block.span, "key conflict")],
                            )

        return Object(result)

    @staticmethod
    def _eval_literal(expr: Literal, _scope: EvaluationScope) -> Value:
        return expr.value

    def _eval_array_expression(
        self, expr: ArrayExpression, scope: EvaluationScope
    ) -> Value:
        return Array([self.eval(item, scope) for item in expr.values])

    def _eval_object_expression(
        self, obj: ObjectExpression, scope: EvaluationScope
    ) -> Value:
        result: dict[String, Value] = {}

        unknown_keys = []

        for key_expr, value_expr in obj.fields.items():
            resolved_key: String
            match key_expr:
                case Identifier(name):
                    resolved_key = String(name)
                case Literal(String() as string):
                    resolved_key = string
                case Parenthesis(expr):
                    key = self.eval(expr, scope)

                    match key:
                        case Unknown() as key:
                            unknown_keys.append(key)
                            continue
                        case String() as key:
                            resolved_key = key
                        case _:
                            raise DiagnosticError(
                                code="pyhcl2::evaluator::object::unsupported_key",
                                message="Unsupported key type in object",
                                labels=[LabeledSpan(expr.span, key.type_name)],
                            )
                case _:
                    raise DiagnosticError(
                        code="pyhcl2::evaluator::object::unsupported_key",
                        message="Unsupported key type in object",
                        labels=[LabeledSpan(key_expr.span, "unsupported key")],
                        notes=[
                            Inline(
                                "[blue]help:[/blue] ",
                                "Did you mean `",
                                Parenthesis(key_expr),
                                " = ",
                                value_expr,
                                "`?",
                            )
                        ],
                    )
            value = self.eval(value_expr, scope)
            if isinstance(value, Unknown):
                value = value.indirect()
            result[resolved_key] = value

        if unknown_keys:
            return Unknown.indirect(*unknown_keys)

        return Object(result)

    @staticmethod
    def _eval_identifier(identifier: Identifier, scope: EvaluationScope) -> Value:
        try:
            return scope[identifier.name]
        except KeyError:
            return Unknown.ident(identifier)

    def _eval_parenthesis(self, paren: Parenthesis, scope: EvaluationScope) -> Value:
        return self.eval(paren.expr, scope)

    def _eval_binary_expression(
        self, expr: BinaryExpression, scope: EvaluationScope
    ) -> Value:
        operation = {
            "+": "__add__",
            "-": "__sub__",
            "*": "__mul__",
            "/": "__truediv__",
            "%": "__mod__",
            "==": "__equals__",
            "!=": "__not_equals__",
            "<": "__lt__",
            ">": "__gt__",
            "<=": "__le__",
            ">=": "__ge__",
            "&&": "__and__",
            "||": "__or__",
        }[expr.op.type]

        left = self.eval(expr.left, scope)
        try:
            if isinstance(left, Unknown):
                return Unknown.indirect(left, self.eval(expr.right, scope))

            operator = getattr(left, operation)
            right = self.eval(expr.right, scope)

            if isinstance(right, Unknown):
                return right

            result = operator(right)

            if result is NotImplemented:
                raise NotImplementedError()  # noqa: TRY301
            else:
                return result

        except (AttributeError, NotImplementedError):
            right = self.eval(expr.right, scope)
            raise DiagnosticError(
                code="pyhcl2::evaluator::binary_expression::unsupported_operator",
                message=f"Binary operator `{expr.op.type}` not implemented for operands of types {left.type_name} and {right.type_name}",
                labels=[
                    LabeledSpan(expr.left.span, left.type_name),
                    LabeledSpan(expr.op.span, "unsupported operator"),
                    LabeledSpan(expr.right.span, right.type_name),
                ],
            ) from None
        except ArithmeticError as e:
            right = self.eval(expr.right, scope)
            raise DiagnosticError(
                code="pyhcl2::evaluator::binary_expression::arithmetic_error",
                message=f"An {e} error occurred",
                labels=[
                    LabeledSpan(
                        expr.left.span, Group(Text("left operand:", end=" "), left)
                    ),
                    LabeledSpan(expr.op.span, str(e)),
                    LabeledSpan(
                        expr.right.span, Group(Text("right operand:", end=" "), right)
                    ),
                ],
            ).with_context("while evaluating binary expression")

    def _eval_unary_expression(
        self, expr: UnaryExpression, scope: EvaluationScope
    ) -> Value:
        value = self.eval(expr.expr, scope)

        try:
            operation = {
                "-": "__neg__",
                "!": "__not__",
            }[expr.op.type]
            result = getattr(value, operation)()

            if result is NotImplemented:
                raise NotImplementedError()  # noqa: TRY301
            else:
                return result

        except (AttributeError, NotImplementedError):
            raise DiagnosticError(
                code="pyhcl2::evaluator::unsupported_unary_operator",
                message=f"Unary operator `{expr.op.type}` not implemented for operand of type {value.type_name}",
                labels=[
                    LabeledSpan(expr.op.span, "unsupported operator"),
                    LabeledSpan(expr.expr.span, value.type_name),
                ],
            )

    def _eval_attribute(self, attr: Attribute, scope: EvaluationScope) -> Value:
        value = self.eval(attr.value, scope)
        scope[attr.key.name] = value
        return value

    def _eval_get_attr(self, expr: GetAttr, scope: EvaluationScope) -> Value:
        on = self.eval(expr.on, scope)
        return self._evaluate_get_attr(on, expr.on.span, expr.key, scope)

    def _eval_get_index(self, expr: GetIndex, scope: EvaluationScope) -> Value:
        on = self.eval(expr.on, scope)
        return self._evaluate_get_index(on, expr.on.span, expr.key, scope)

    @staticmethod
    def _evaluate_get_attr(
        on: Value, on_span: SourceSpan, key: GetAttrKey, _scope: EvaluationScope
    ) -> Value:
        key_value = key.ident.name

        if isinstance(on, Unknown):
            return on.direct(key.ident.span, key.ident.name)

        if not isinstance(on, Object):
            raise DiagnosticError(
                code="pyhcl2::evaluator::get_attr::unsupported_type",
                message="Cannot get attribute from non-object type",
                labels=[
                    LabeledSpan(on_span, on.type_name),
                    LabeledSpan(key.ident.span, "unsupported attribute"),
                ],
            )

        try:
            return on[String(key_value)]
        except KeyError:
            return Unknown().direct(key.ident.span, key_value)

    def _evaluate_get_index(
        self, on: Value, on_span: SourceSpan, key: GetIndexKey, scope: EvaluationScope
    ) -> Value:
        key_value = self.eval(key.expr, scope)

        try:
            match on, key_value:
                case Unknown() as on, Unknown() as key_value:
                    return Unknown.indirect(on, key_value)
                case Unknown() as on, String(raw_str):
                    return on.direct(key.expr.span, raw_str)
                case Unknown() as on, Integer():
                    return Unknown.indirect(on, key_value)
                case Object() as obj, String() as key_value:
                    return obj[key_value]
                case Array() as on, Integer(int_raw):
                    return on[int_raw]
                case Object(), Unknown() as key_value:
                    return key_value
                case _:
                    raise DiagnosticError(
                        code="pyhcl2::evaluator::get_index::unsupported_type",
                        message=f"Cannot index into {on.type_name} with {key_value.type_name} key",
                        labels=[
                            LabeledSpan(on_span, on.type_name),
                            LabeledSpan(key.expr.span, key_value.type_name),
                        ],
                    )
        except KeyError:
            raise DiagnosticError(
                code="pyhcl2::evaluator::get_index::missing_key",
                message="Key not found in object",
                labels=[
                    LabeledSpan(on_span, on.type_name),
                    LabeledSpan(key.expr.span, "key"),
                ],
            )
        except IndexError:
            raise DiagnosticError(
                code="pyhcl2::evaluator::get_index::index_out_of_bounds",
                message="Index out of bounds",
                labels=[
                    LabeledSpan(on_span, on.type_name),
                    LabeledSpan(key.expr.span, "index"),
                ],
            )

    def _eval_function_call(self, call: FunctionCall, scope: EvaluationScope) -> Value:
        if call.var_args:
            # TODO
            raise DiagnosticError(
                code="pyhcl2::evaluator::function_call::unsupported_var_args",
                message="Function calls with var args are not supported",
                labels=[LabeledSpan(call.span, "call with var args")],
            )

        if call.ident.name in self.intrinsic_functions:
            args = [self.eval(arg, scope) for arg in call.args]
            if any(isinstance(arg.resolve(), Unknown) for arg in args):
                return Unknown.indirect(*args)

            try:
                return self.intrinsic_functions[call.ident.name](*args)
            except TypeError as e:
                raise DiagnosticError(
                    code="pyhcl2::evaluator::function_call::invalid_args",
                    message="Invalid arguments passed to function",
                    labels=[LabeledSpan(call.args_span, "invalid arguments")],
                ) from e

        raise DiagnosticError(
            code="pyhcl2::evaluator::function_call::unsupported_function",
            message=f"Intrinsic function `{call.ident.name}` does not exist",
            labels=[LabeledSpan(call.ident.span, "unsupported function")],
        )

    def _eval_conditional(self, expr: Conditional, scope: EvaluationScope) -> Value:
        condition = self.eval(expr.cond, scope)

        match condition:
            case Unknown() as condition:
                return Unknown.indirect(
                    condition,
                    self.eval(expr.then_expr, scope),
                    self.eval(expr.else_expr, scope),
                )
            case Boolean(True):
                return self.eval(expr.then_expr, scope)
            case Boolean(False):
                return self.eval(expr.else_expr, scope)
            case _:
                raise DiagnosticError(
                    code="pyhcl2::evaluator::conditional::unsupported_condition",
                    message=f"Unsupported condition type {condition.type_name}",
                    labels=[LabeledSpan(expr.cond.span, condition.type_name)],
                )

    def _eval_for_tuple_expression(
        self, expr: ForTupleExpression, scope: EvaluationScope
    ) -> Value:
        collection = self.eval(expr.collection, scope)
        results: list[Value] = []

        iterator: Iterable[tuple[Value, Value]]

        match collection:
            case Object(obj):
                iterator = obj.items()
            case Array(array):
                iterator = [(Integer(k), v) for k, v in enumerate(array)]
            case Unknown() as collection:
                unknown = collection.indirect()
                iterator = [(unknown, unknown)]
            case _:
                raise DiagnosticError(
                    code="pyhcl2::evaluator::for_tuple_expression::unsupported_collection",
                    message=f"Unsupported collection type {collection.type_name}",
                    labels=[LabeledSpan(expr.collection.span, collection.type_name)],
                )

        for k, v in iterator:
            child_scope = scope.child()
            child_scope[expr.value_ident.name] = v
            if expr.key_ident:
                child_scope[expr.key_ident.name] = k

            condition = (
                self.eval(expr.condition, child_scope)
                if expr.condition is not None
                else Boolean(True)
            )

            match condition:
                case Unknown() as condition:
                    results.append(
                        Unknown.indirect(condition, self.eval(expr.value, child_scope))
                    )
                case Boolean(True):
                    result = self.eval(expr.value, child_scope)
                    match result:
                        case Unknown() as result:
                            results.append(result.indirect())
                        case _:
                            results.append(result)
                case Boolean(False):
                    pass
                case _:
                    assert expr.condition is not None
                    raise DiagnosticError(
                        code="pyhcl2::evaluator::for_tuple_expression::unsupported_condition",
                        message=f"Unsupported condition type {condition.type_name}",
                        labels=[LabeledSpan(expr.condition.span, condition.type_name)],
                    )

        return Array(results)

    def _eval_for_object_expression(  # noqa: PLR0912
        self, expr: ForObjectExpression, scope: EvaluationScope
    ) -> Value:
        if expr.grouping_mode:
            raise DiagnosticError(
                code="pyhcl2::evaluator::for_object_expression::unsupported_grouping_mode",
                message="Grouping mode is not supported",
                labels=[LabeledSpan(expr.span, "grouping mode")],
            )

        collection = self.eval(expr.collection, scope)
        results: dict[String, Value] = {}
        unknown_blockers = []

        iterator: Iterable[tuple[Value, Value]]

        match collection:
            case Object(obj):
                iterator = obj.items()
            case Array(array):
                iterator = [(Integer(k), v) for k, v in enumerate(array)]
            case Unknown() as collection:
                unknown = collection.indirect()
                iterator = [(unknown, unknown)]
            case _:
                raise DiagnosticError(
                    code="pyhcl2::evaluator::for_object_expression::unsupported_collection",
                    message=f"Unsupported collection type {collection.type_name}",
                    labels=[LabeledSpan(expr.collection.span, collection.type_name)],
                )

        for k, v in iterator:
            child_scope = scope.child()
            child_scope[expr.value_ident.name] = v
            if expr.key_ident:
                child_scope[expr.key_ident.name] = k

            condition = (
                self.eval(expr.condition, child_scope)
                if expr.condition is not None
                else Boolean(True)
            )

            match condition:
                case Unknown() as condition:
                    unknown_blockers.append(
                        Unknown.indirect(
                            condition,
                            self.eval(expr.key, child_scope),
                            self.eval(expr.value, child_scope),
                        )
                    )
                case Boolean(True):
                    key = self.eval(expr.key, child_scope)
                    match key:
                        case Unknown() as key:
                            unknown_blockers.append(
                                Unknown.indirect(
                                    key, self.eval(expr.value, child_scope)
                                )
                            )
                        case String() as key:
                            results[key] = self.eval(expr.value, child_scope)
                        case _:
                            raise DiagnosticError(
                                code="pyhcl2::evaluator::for_object_expression::unsupported_key",
                                message=f"Unsupported key type {key.type_name}",
                                labels=[LabeledSpan(expr.key.span, key.type_name)],
                            )
                case Boolean(False):
                    pass
                case _:
                    assert expr.condition is not None
                    raise DiagnosticError(
                        code="pyhcl2::evaluator::for_object_expression::unsupported_condition",
                        message=f"Unsupported condition type {condition.type_name}",
                        labels=[LabeledSpan(expr.condition.span, condition.type_name)],
                    )

        if unknown_blockers:
            return Unknown.indirect(*unknown_blockers)

        return Object(results)

    def _eval_attr_splat(self, expr: AttrSplat, scope: EvaluationScope) -> Value:
        on = self.eval(expr.on, scope)

        match on:
            case Null():
                return Array([])
            case Array(array):
                iterable = array
            case _:
                iterable = [on]

        values = []

        for i, v in enumerate(iterable):
            try:
                span = expr.on.span
                value = v
                for key in expr.keys:
                    value = self._evaluate_get_attr(value, span, key, scope)
                    span = SourceSpan(span.start, key.span.end)
                values.append(value)
            except DiagnosticError as e:
                e.notes.append(
                    Inline(
                        "[blue]help:[/blue] The resulting expression was ",
                        v,
                        *expr.keys,
                    )
                )
                raise e.with_context(f"while evaluating element {i}").with_context(
                    "while evaluating attribute splat expression"
                )
        if isinstance(on, Unknown):
            return Unknown.indirect(*values)

        return Array(values)

    def _eval_index_splat(self, expr: IndexSplat, scope: EvaluationScope) -> Value:
        on = self.eval(expr.on, scope)

        match on:
            case Null():
                return Array([])
            case Array(array):
                iterable = array
            case _:
                iterable = [on]

        values = []

        for i, v in enumerate(iterable):
            try:
                span = expr.on.span
                value = v
                for key in expr.keys:
                    match key:
                        case GetAttrKey():
                            value = self._evaluate_get_attr(value, span, key, scope)
                        case GetIndexKey():
                            value = self._evaluate_get_index(value, span, key, scope)
                    span = SourceSpan(span.start, key.span.end)
                values.append(value)
            except DiagnosticError as e:
                e.notes.append(
                    Inline(
                        "[blue]help:[/blue] The resulting expression was ",
                        v,
                        *expr.keys,
                    )
                )
                raise e.with_context(f"while evaluating element {i}").with_context(
                    "while evaluating index splat expression"
                )

        if isinstance(on, Unknown):
            return Unknown.indirect(*values)

        return Array(values)
