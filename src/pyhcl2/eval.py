from __future__ import annotations

import re
from collections.abc import Mapping, Iterable
from typing import (
    Callable, Self, MutableMapping,
)

from dataclasses import dataclass, field

import rich
from rich.console import Group, NewLine
from rich.text import Text

from pyhcl2.pymiette import Diagnostic, LabeledSpan, SourceSpan
from pyhcl2.rich_utils import Inline
from pyhcl2.nodes import (
    Node, Literal, ArrayExpression, ObjectExpression, Identifier, Parenthesis,
    BinaryExpression, UnaryExpression, Attribute, GetAttr, GetAttrKey, GetIndex, GetIndexKey, FunctionCall, Conditional,
    ForTupleExpression, ForObjectExpression,
)
from pyhcl2.values import Value, Array, Object, String, Unresolved, Integer, Boolean

camel_to_snake_pattern = re.compile(r"(?<!^)(?=[A-Z])")

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

    def eval(self, expr: Node, scope: EvaluationScope = EvaluationScope()) -> Value:
        method = (
            f"_eval_{camel_to_snake_pattern.sub('_', expr.__class__.__name__).lower()}"
        )
        if hasattr(self, method):
            result = getattr(self, method)(expr, scope)
            rich.print(Inline(method, "(", expr, "): ", result, NewLine()))
            return result
        else:
            raise Diagnostic(
                code="pyhcl2::evaluator::unsupported_node",
                message=f"Unsupported node type {expr.__class__.__name__}",
                labels=[
                    LabeledSpan(expr.span, "unsupported expression"),
                ],
                help=f"Attempted to call {method}, but it does not exist",
            )

    @staticmethod
    def _eval_literal(expr: Literal, _scope: EvaluationScope) -> Value:
        return expr.value

    def _eval_array_expression(self, expr: ArrayExpression, scope: EvaluationScope) -> Value:
        return Array([self.eval(item, scope) for item in expr.values])

    def _eval_object_expression(self, obj: ObjectExpression, scope: EvaluationScope) -> Value:
        result: dict[String, Value] = {}

        unresolved_keys = []

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
                        case Unresolved() as key:
                            unresolved_keys.append(key)
                            continue
                        case String() as key:
                            resolved_key = key
                        case _:
                            raise Diagnostic(
                                code="pyhcl2::evaluator::object::unsupported_key",
                                message="Unsupported key type in object",
                                labels=[LabeledSpan(expr.span, key.type_name)],
                            )
                case _:
                    raise Diagnostic(
                        code="pyhcl2::evaluator::object::unsupported_key",
                        message="Unsupported key type in object",
                        labels=[LabeledSpan(key_expr.span, "unsupported key")],
                        help=Inline("Did you mean `", Parenthesis(key_expr), " = ", value_expr, "`?"),
                    )
            value = self.eval(value_expr, scope)
            if isinstance(value, Unresolved):
                value = value.merge(value_expr.span)
            result[resolved_key] = value

        if unresolved_keys:
            return Unresolved.concat(*unresolved_keys).expand(obj.span)

        return Object(result)

    @staticmethod
    def _eval_identifier(identifier: Identifier, scope: EvaluationScope) -> Value:
        try:
            return scope[identifier.name]
        except KeyError:
            return Unresolved.ident(identifier)

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

        # TODO: short circuit logical operator evaluation

        left = self.eval(expr.left, scope)
        try:

            if isinstance(left, Unresolved):
                return left.merge(expr.span, self.eval(expr.right, scope))

            operator = getattr(left, operation)
            right = self.eval(expr.right, scope)

            if isinstance(right, Unresolved):
                return right.expand(expr.span)

            result = operator(right)

            if result is NotImplemented:
                raise NotImplementedError

            return result
        except (AttributeError, NotImplementedError) as e:
            right = self.eval(expr.right, scope)
            raise Diagnostic(
                code="pyhcl2::evaluator::binary_expression::unsupported_operator",
                message=f"Binary operator `{expr.op.type}` not implemented for operands of types {left.type_name} and {right.type_name}",
                labels=[
                    LabeledSpan(expr.left.span, left.type_name),
                    LabeledSpan(expr.op.span, "unsupported operator"),
                    LabeledSpan(expr.right.span, right.type_name),
                ],
            )
        except ArithmeticError as e:
            right = self.eval(expr.right, scope)
            raise Diagnostic(
                    code="pyhcl2::evaluator::binary_expression::arithmetic_error",
                    message=f"An {e} error occurred",
                    labels=[
                        LabeledSpan(expr.left.span, Group(Text("left operand:", end=" "), left)),
                        LabeledSpan(expr.op.span, str(e)),
                        LabeledSpan(expr.right.span, Group(Text("right operand:", end=" "), right)),
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
                raise NotImplementedError

            return result

        except (AttributeError, NotImplementedError):
            raise Diagnostic(
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

        if isinstance(on, Unresolved):
            return on.reference(key.ident.span, key.ident.name)

        if not isinstance(on, Object):
            raise Diagnostic(
                code="pyhcl2::evaluator::get_attr::unsupported_type",
                message="Cannot get attribute from non-object type",
                labels=[
                    LabeledSpan(on_span, on.type_name),
                    LabeledSpan(key.ident.span, "unsupported attribute"),
                ],
            )

        try:
            return on._raw[String(key_value)]
        except KeyError:
            raise Diagnostic(
                code="pyhcl2::evaluator::get_attr::missing_key",
                message="Key not found in object",
                labels=[
                    LabeledSpan(on_span, on.type_name),
                    LabeledSpan(key.ident.span, f"key"),
                ],
            )
            # return Unresolved(key.ident.span, [VariableReference((None, key_value,), key.ident.span)])

    def _evaluate_get_index(self, on: Value, on_span: SourceSpan, key: GetIndexKey, scope: EvaluationScope) -> Value:
        key_value = self.eval(key.expr, scope)

        try:
            match on, key_value:
                case Unresolved() as on, Unresolved() as key_value:
                    return on.merge(key.span, key_value)
                case Unresolved() as on, String(raw_str):
                    return on.reference(key.expr.span, raw_str)
                case Unresolved() as on, Integer():
                    return on.merge(key.span, key_value)
                case Object(obj_raw), String() as key_value:
                    return obj_raw[key_value]
                case Array(on_raw), Integer(int_raw):
                    return on_raw[int_raw]
                case Object(), Unresolved() as key_value:
                    return key_value.expand(key.span)
                case _:
                    raise Diagnostic(
                        code="pyhcl2::evaluator::get_index::unsupported_type",
                        message=f"Cannot index into {on.type_name} with {key_value.type_name} key",
                        labels=[
                            LabeledSpan(on_span, on.type_name),
                            LabeledSpan(key.expr.span, key_value.type_name),
                        ],
                    )
        except KeyError:
            raise Diagnostic(
                code="pyhcl2::evaluator::get_index::missing_key",
                message="Key not found in object",
                labels=[
                    LabeledSpan(on_span, on.type_name),
                    LabeledSpan(key.expr.span, "key"),
                ],
            )
        except IndexError:
            raise Diagnostic(
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
            raise Diagnostic(
                code="pyhcl2::evaluator::function_call::unsupported_var_args",
                message="Function calls with var args are not supported",
                labels=[LabeledSpan(call.span, "call with var args")],
            )

        if call.ident.name in self.intrinsic_functions:
            try:
                return self.intrinsic_functions[call.ident.name](
                    *[self.eval(arg, scope) for arg in call.args]
                )
            except TypeError as e:
                raise Diagnostic(
                    code="pyhcl2::evaluator::function_call::invalid_args",
                    message="Invalid arguments passed to function",
                    labels=[LabeledSpan(call.args_span, "invalid arguments")],
                ) from e

        raise Diagnostic(
            code="pyhcl2::evaluator::function_call::unsupported_function",
            message=f"Intrinsic function `{call.ident.name}` does not exist",
            labels=[LabeledSpan(call.ident.span, "unsupported function")],
        )

    def _eval_conditional(self, expr: Conditional, scope: EvaluationScope) -> Value:
        condition = self.eval(expr.cond, scope)

        match condition:
            case Unresolved() as condition:
                return condition.merge(
                    expr.span,
                    self.eval(expr.then_expr, scope),
                    self.eval(expr.else_expr, scope)
                )
            case Boolean(True):
                return self.eval(expr.then_expr, scope)
            case Boolean(False):
                return self.eval(expr.else_expr, scope)
            case _:
                raise Diagnostic(
                    code="pyhcl2::evaluator::conditional::unsupported_condition",
                    message=f"Unsupported condition type {condition.type_name}",
                    labels=[LabeledSpan(expr.cond.span, condition.type_name)],
                )

    def _eval_for_tuple_expression(self, expr: ForTupleExpression, scope: EvaluationScope) -> Value:
        collection = self.eval(expr.collection, scope)
        results: list[Value] = []

        iterator: Iterable[tuple[Value, Value]]

        match collection:
            case Object(obj):
                iterator = obj.items()
            case Array(array):
                iterator = [(Integer(k), v) for k,v in enumerate(array)]
            case Unresolved() as collection:
                unresolved = collection.merge(expr.span)
                iterator = [(unresolved, unresolved)]
            case _:
                raise Diagnostic(
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
                self.eval(expr.condition, child_scope) if expr.condition is not None else Boolean(True)
            )

            match condition:
                case Unresolved() as condition:
                    results.append(condition.merge(expr.span, self.eval(expr.value, child_scope)))
                case Boolean(True):
                    result = self.eval(expr.value, child_scope)
                    match result:
                        case Unresolved() as result:
                            results.append(result.merge(expr.span))
                        case _:
                            results.append(result)
                case Boolean(False):
                    pass
                case _:
                    assert expr.condition is not None
                    raise Diagnostic(
                        code="pyhcl2::evaluator::for_tuple_expression::unsupported_condition",
                        message=f"Unsupported condition type {condition.type_name}",
                        labels=[LabeledSpan(expr.condition.span, condition.type_name)],
                    )

        return Array(results)

    def _eval_for_object_expression(self, expr: ForObjectExpression, scope: EvaluationScope) -> Value:
        if expr.grouping_mode:
            raise Diagnostic(
                code="pyhcl2::evaluator::for_object_expression::unsupported_grouping_mode",
                message="Grouping mode is not supported",
                labels=[LabeledSpan(expr.span, "grouping mode")],
            )

        collection = self.eval(expr.collection, scope)
        results: dict[String, Value] = {}
        unresolved_blockers = []

        iterator: Iterable[tuple[Value, Value]]

        match collection:
            case Object(obj):
                iterator = obj.items()
            case Array(array):
                iterator = [(Integer(k), v) for k,v in enumerate(array)]
            case Unresolved() as collection:
                unresolved = collection.merge(expr.span)
                iterator = [(unresolved, unresolved)]
            case _:
                raise Diagnostic(
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
                self.eval(expr.condition, child_scope) if expr.condition is not None else Boolean(True)
            )

            match condition:
                case Unresolved() as condition:
                    unresolved_blockers.append(condition.merge(
                        expr.span,
                        self.eval(expr.key, child_scope),
                        self.eval(expr.value, child_scope)
                    ))
                case Boolean(True):
                    key = self.eval(expr.key, child_scope)
                    match key:
                        case Unresolved() as key:
                            unresolved_blockers.append(key.merge(expr.span, self.eval(expr.value, child_scope)))
                        case String() as key:
                            results[key] = self.eval(expr.value, child_scope)
                        case _:
                            raise Diagnostic(
                                code="pyhcl2::evaluator::for_object_expression::unsupported_key",
                                message=f"Unsupported key type {key.type_name}",
                                labels=[LabeledSpan(expr.key.span, key.type_name)],
                            )
                case Boolean(False):
                    pass
                case _:
                    assert expr.condition is not None
                    raise Diagnostic(
                        code="pyhcl2::evaluator::for_object_expression::unsupported_condition",
                        message=f"Unsupported condition type {condition.type_name}",
                        labels=[LabeledSpan(expr.condition.span, condition.type_name)],
                    )

        if unresolved_blockers:
            return Unresolved.concat(*unresolved_blockers).expand(expr.span)

        return Object(results)
