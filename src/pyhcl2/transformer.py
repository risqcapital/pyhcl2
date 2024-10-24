from __future__ import annotations

import re
import sys
from typing import TypeVar, cast

from lark import Discard, Token, Transformer, v_args
from lark.tree import Meta
from lark.visitors import _DiscardType
from pyagnostics.spans import SourceSpan

from pyhcl2.nodes import (
    ArrayExpression,
    Attribute,
    AttrSplat,
    BinaryExpression,
    BinaryOperator,
    Block,
    Conditional,
    Expression,
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
    Stmt,
    UnaryExpression,
    UnaryOperator,
    VarArgsMarker,
)
from pyhcl2.values import Boolean, Float, Integer, Null, String

HEREDOC_PATTERN = re.compile(r"<<([a-zA-Z][a-zA-Z0-9._-]+)\n((.|\n)*?)\n\s*\1", re.S)
HEREDOC_TRIM_PATTERN = re.compile(
    r"<<-([a-zA-Z][a-zA-Z0-9._-]+)\n((.|\n)*?)\n\s*\1", re.S
)
T = TypeVar("T")


# noinspection PyMethodMayBeStatic
class ToAstTransformer(Transformer):
    @v_args(inline=True)
    def __binary_op(self, op: Token) -> BinaryOperator:
        assert op.start_pos is not None
        assert op.end_pos is not None
        return BinaryOperator(type=op.value, span=SourceSpan(op.start_pos, op.end_pos))

    add_op = __binary_op
    mul_op = __binary_op
    comp_op = __binary_op
    eq_op = __binary_op
    or_op = __binary_op
    and_op = __binary_op

    @v_args(inline=True)
    def __binary_expression(
        self, left: Expression, op: BinaryOperator, right: Expression
    ) -> BinaryExpression:
        return BinaryExpression(
            op,
            left,
            right,
            span=SourceSpan(left.span.start, right.span.end),
        )

    term = __binary_expression
    add_expr = __binary_expression
    compare = __binary_expression
    equality = __binary_expression
    and_test = __binary_expression
    or_test = __binary_expression

    @v_args(inline=True)
    def __unary_op(self, op: Token) -> UnaryOperator:
        assert op.start_pos is not None
        assert op.end_pos is not None
        return UnaryOperator(type=op.value, span=SourceSpan(op.start_pos, op.end_pos))

    not_op = __unary_op
    neg_op = __unary_op

    @v_args(inline=True)
    def __unary_expression(
        self, op: UnaryOperator, expr: Expression
    ) -> UnaryExpression:
        return UnaryExpression(op, expr, span=SourceSpan(op.span.start, expr.span.end))

    not_test = __unary_expression
    neg = __unary_expression

    @v_args(inline=True)
    def conditional(
        self, condition: Expression, then_expr: Expression, else_expr: Expression
    ) -> Conditional:
        return Conditional(
            condition,
            then_expr,
            else_expr,
            span=SourceSpan(condition.span.start, else_expr.span.end),
        )

    @v_args(inline=True, meta=True)
    def get_attr(self, meta: Meta, identifier: Identifier) -> GetAttrKey:
        return GetAttrKey(identifier, span=SourceSpan(meta.start_pos, meta.end_pos))

    @v_args(inline=True)
    def get_attr_expr_term(self, on: Expression, key: GetAttrKey) -> GetAttr:
        return GetAttr(on, key, span=SourceSpan(on.span.start, key.span.end))

    @v_args(meta=True)
    def float_lit(self, meta: Meta, args: list[Token]) -> Literal:
        return Literal(
            Float(float("".join([str(arg) for arg in args]))),
            span=SourceSpan(meta.start_pos, meta.end_pos),
        )

    @v_args(meta=True, inline=True)
    def null_lit(self, meta: Meta) -> Literal:
        span = SourceSpan(meta.start_pos, meta.end_pos)
        return Literal(Null(span=span), span=span)

    @v_args(meta=True)
    def int_lit(self, meta: Meta, args: list[Token]) -> Literal:
        span = SourceSpan(meta.start_pos, meta.end_pos)
        return Literal(
            Integer(int("".join([str(arg) for arg in args])), span=span),
            span=span,
        )

    @v_args(inline=True)
    def expr_term(self, expr: Expression) -> Expression:
        return expr

    @v_args(inline=True)
    def bool_lit(self, token: Token) -> Literal:
        assert token.start_pos is not None
        assert token.end_pos is not None
        span = SourceSpan(token.start_pos, token.end_pos)
        match token.value.lower():
            case "true":
                return Literal(
                    Boolean(True, span=span),
                    span=span,
                )
            case "false":
                return Literal(
                    Boolean(False, span=span),
                    span=span,
                )
        raise ValueError(f"Invalid boolean value: {token.value}")

    @v_args(inline=True)
    def string_lit(self, token: Token) -> Literal:
        assert token.start_pos is not None
        assert token.end_pos is not None
        span = SourceSpan(token.start_pos, token.end_pos)
        return Literal(
            String(token.value[1:-1], span=span),
            span=span,
        )

    @v_args(inline=True)
    def identifier(self, ident: Token) -> Expression:
        assert ident.start_pos is not None
        assert ident.end_pos is not None
        return Identifier(ident.value, span=SourceSpan(ident.start_pos, ident.end_pos))

    @v_args(inline=True)
    def attribute(self, ident: Identifier, expr: Expression) -> Attribute:
        return Attribute(ident, expr, span=SourceSpan(ident.span.start, expr.span.end))

    def body(self, args: list[Stmt]) -> list[Stmt]:
        return args

    @v_args(meta=True)
    def block(self, meta: Meta, args: list[Identifier | Literal | Stmt]) -> Block:
        type_key = cast(Identifier, args[0])
        labels = cast(list[Identifier | Literal], args[1:-1])
        body = cast(list[Stmt], args[-1])
        return Block(
            type_key,
            labels,
            body,
            span=SourceSpan(meta.start_pos, meta.end_pos),
        )

    @v_args(meta=True)
    def object(
        self, meta: Meta, args: list[tuple[Expression, Expression]]
    ) -> ObjectExpression:
        return ObjectExpression(
            {kv[0]: kv[1] for kv in args}, span=SourceSpan(meta.start_pos, meta.end_pos)
        )

    @v_args(inline=True)
    def object_elem(
        self, key: Expression, value: Expression
    ) -> tuple[Expression, Expression]:
        return key, value

    @v_args(meta=True)
    def array(self, meta: Meta, values: list[Expression]) -> ArrayExpression:
        return ArrayExpression(values, span=SourceSpan(meta.start_pos, meta.end_pos))

    @v_args(meta=True, inline=True)
    def paren_expr(self, meta: Meta, expr: Expression) -> Parenthesis:
        return Parenthesis(expr, span=SourceSpan(meta.start_pos, meta.end_pos))

    @v_args(meta=True, inline=True)
    def function_call(
        self,
        meta: Meta,
        ident: Identifier,
        args: tuple[list[Expression], VarArgsMarker | None] = ([], None),
    ) -> FunctionCall:
        return FunctionCall(
            ident,
            args[0],
            args[1] is not None,
            span=SourceSpan(meta.start_pos, meta.end_pos),
        )

    def arguments(
        self, args: list[Expression]
    ) -> tuple[list[Expression], VarArgsMarker | None]:
        if len(args) > 0 and isinstance(args[-1], VarArgsMarker):
            return args[:-1], cast(VarArgsMarker, args[-1])
        return args, None

    @v_args(meta=True, inline=True)
    def ellipsis(self, meta: Meta) -> VarArgsMarker:
        return VarArgsMarker(span=SourceSpan(meta.start_pos, meta.end_pos))

    @v_args(meta=True, inline=True)
    def index(self, meta: Meta, expr: Expression) -> GetIndexKey:
        return GetIndexKey(expr, span=SourceSpan(meta.start_pos, meta.end_pos))

    @v_args(meta=True, inline=True)
    def index_expr_term(
        self, meta: Meta, on: Expression, index: GetIndexKey
    ) -> GetIndex:
        return GetIndex(on, index, span=SourceSpan(meta.start_pos, meta.end_pos))

    def attr_splat(self, args: list[Node]) -> list[Node]:
        return args

    @v_args(meta=True, inline=True)
    def attr_splat_expr_term(
        self, meta: Meta, on: Expression, keys: list[GetAttrKey]
    ) -> AttrSplat:
        return AttrSplat(on, keys, span=SourceSpan(meta.start_pos, meta.end_pos))

    def full_splat(self, args: list[Node]) -> list[Node]:
        return args

    @v_args(meta=True, inline=True)
    def full_splat_expr_term(
        self, meta: Meta, on: Expression, keys: list[GetAttrKey | GetIndexKey]
    ) -> IndexSplat:
        return IndexSplat(on, keys, span=SourceSpan(meta.start_pos, meta.end_pos))

    def new_line_or_comment(self, _args: list[Node | Token]) -> _DiscardType:
        return Discard

    def new_line_and_or_comma(self, _args: list[Node | Token]) -> _DiscardType:
        return Discard

    def start(self, args: list[Node | Token]) -> Node | Token:
        return args[0]

    start_expr = start
    start_expr_or_stmt = start

    def for_intro(
        self, args: list[Node | Token]
    ) -> tuple[Identifier | None, Identifier, Expression]:
        return (
            cast(Identifier, args[0]) if len(args) == 3 else None,
            cast(Identifier, args[1 if len(args) == 3 else 0]),
            cast(Expression, args[-1]),
        )

    @v_args(inline=True)
    def for_cond(self, condition: Expression) -> Expression:
        return condition

    @v_args(meta=True, inline=True)
    def for_tuple_expr(
        self,
        meta: Meta,
        for_intro: tuple[Identifier | None, Identifier, Expression],
        expression: Expression,
        condition: Expression | None = None,
    ) -> ForTupleExpression:
        key_ident, value_ident, collection = for_intro
        return ForTupleExpression(
            key_ident,
            value_ident,
            collection,
            expression,
            condition,
            span=SourceSpan(meta.start_pos, meta.end_pos),
        )

    @v_args(meta=True, inline=True)
    def for_object_expr(
        self,
        meta: Meta,
        for_intro: tuple[Identifier | None, Identifier, Expression],
        key_expression: Expression,
        value_expression: Expression,
        *args: VarArgsMarker | Expression,
    ) -> ForObjectExpression:
        key_ident, value_ident, collection = for_intro
        grouping_mode = any(isinstance(arg, VarArgsMarker) for arg in args)
        condition: Expression | None = next(
            (arg for arg in args if isinstance(arg, Expression)), None
        )

        return ForObjectExpression(
            key_ident,
            value_ident,
            collection,
            key_expression,
            value_expression,
            condition,
            grouping_mode,
            span=SourceSpan(meta.start_pos, meta.end_pos),
        )

    @v_args(meta=True)
    def heredoc_template(self, meta: Meta, args: list[Node | Token]) -> Literal:
        match = HEREDOC_PATTERN.match(str(args[0]))
        if not match:
            raise RuntimeError(f"Invalid Heredoc token: {args[0]}")
        return Literal(
            String(f'"{match.group(2)}"'),
            span=SourceSpan(meta.start_pos, meta.end_pos),
        )

    @v_args(meta=True)
    def heredoc_template_trim(self, meta: Meta, args: list[Node | Token]) -> Literal:
        match = HEREDOC_TRIM_PATTERN.match(str(args[0]))
        if not match:
            raise RuntimeError(f"Invalid Heredoc token: {args[0]}")

        text = match.group(2)
        lines = text.split("\n")

        # calculate the min number of leading spaces in each line
        min_spaces = sys.maxsize
        for line in lines:
            leading_spaces = len(line) - len(line.lstrip(" "))
            min_spaces = min(min_spaces, leading_spaces)

        # trim off that number of leading spaces from each line
        lines = [line[min_spaces:] for line in lines]

        return Literal(
            String(f'"{"\n".join(lines)}"'),
            span=SourceSpan(meta.start_pos, meta.end_pos),
        )
