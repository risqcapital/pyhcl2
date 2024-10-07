from __future__ import annotations

import re
import sys
from typing import Any

from lark import Discard, Token, Transformer, v_args
from lark.tree import Meta
from lark.visitors import _DiscardType

from pyhcl2._ast import (
    Array,
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
    Object,
    Parenthesis,
    UnaryExpression,
    UnaryOperator,
)

HEREDOC_PATTERN = re.compile(r"<<([a-zA-Z][a-zA-Z0-9._-]+)\n((.|\n)*?)\n\s*\1", re.S)
HEREDOC_TRIM_PATTERN = re.compile(
    r"<<-([a-zA-Z][a-zA-Z0-9._-]+)\n((.|\n)*?)\n\s*\1", re.S
)


class EllipsisMarker:
    pass


# noinspection PyMethodMayBeStatic
class ToAstTransformer(Transformer):
    def __binary_op(self, args: list[Token]) -> BinaryOperator:
        return BinaryOperator(
            type=args[0].value, start_pos=args[0].start_pos, end_pos=args[0].end_pos
        )

    add_op = __binary_op
    mul_op = __binary_op
    comp_op = __binary_op
    eq_op = __binary_op
    or_op = __binary_op
    and_op = __binary_op

    def __binary_expression(self, args: list[Any]) -> BinaryExpression:
        args = self.strip_new_line_tokens(args)
        return BinaryExpression(
            args[1],
            args[0],
            args[2],
            start_pos=args[0].start_pos,
            end_pos=args[2].end_pos,
        )

    term = __binary_expression
    add_expr = __binary_expression
    compare = __binary_expression
    equality = __binary_expression
    and_test = __binary_expression
    or_test = __binary_expression

    def __unary_op(self, args: list[Token]) -> UnaryOperator:
        return UnaryOperator(
            type=args[0].value, start_pos=args[0].start_pos, end_pos=args[0].end_pos
        )

    not_op = __unary_op
    neg_op = __unary_op

    def __unary_expression(self, args: list[Any]) -> UnaryExpression:
        args = self.strip_new_line_tokens(args)
        return UnaryExpression(
            args[0], args[1], start_pos=args[0].start_pos, end_pos=args[1].end_pos
        )

    not_test = __unary_expression
    neg = __unary_expression

    def conditional(self, args: list[Any]) -> Conditional:
        return Conditional(
            args[0],
            args[1],
            args[2],
            start_pos=args[0].start_pos,
            end_pos=args[2].end_pos,
        )

    @v_args(meta=True)
    def get_attr(self, meta: Meta, args: list[Any]) -> GetAttrKey:
        return GetAttrKey(args[0], start_pos=meta.start_pos, end_pos=meta.end_pos)

    def get_attr_expr_term(self, args: list[Any]) -> GetAttr:
        get_attr: GetAttrKey = args[1]
        return GetAttr(
            args[0], get_attr, start_pos=args[0].start_pos, end_pos=get_attr.end_pos
        )

    def float_lit(self, args: list[Token]) -> Literal:
        return Literal(
            float("".join([str(arg) for arg in args])),
            start_pos=args[0].start_pos,
            end_pos=args[-1].end_pos,
        )

    @v_args(meta=True, inline=True)
    def null_lit(self, meta: Meta) -> Literal:
        return Literal(None, start_pos=meta.start_pos, end_pos=meta.end_pos)

    def int_lit(self, args: list[Token]) -> Literal:
        return Literal(
            int("".join([str(arg) for arg in args])),
            start_pos=args[0].start_pos,
            end_pos=args[-1].end_pos,
        )

    #
    def expr_term(self, args: list[Any]) -> Any:  # noqa: ANN401
        args = self.strip_new_line_tokens(args)
        return args[0]

    def bool_lit(self, value: list[Token]) -> Literal:
        match value[0].value.lower():
            case "true":
                return Literal(
                    True, start_pos=value[0].start_pos, end_pos=value[0].end_pos
                )
            case "false":
                return Literal(
                    False, start_pos=value[0].start_pos, end_pos=value[0].end_pos
                )
        raise ValueError(f"Invalid boolean value: {value[0].value}")

    def string_lit(self, value: list[Token]) -> Literal:
        return Literal(
            value[0].value[1:-1], start_pos=value[0].start_pos, end_pos=value[0].end_pos
        )

    def identifier(self, value: list[Token]) -> Expression:
        return Identifier(
            value[0].value, start_pos=value[0].start_pos, end_pos=value[0].end_pos
        )

    def attribute(self, args: list[Expression]) -> Attribute:
        args = self.strip_new_line_tokens(args)
        assert isinstance(args[0], Identifier)
        return Attribute(
            args[0], args[1], start_pos=args[0].start_pos, end_pos=args[1].end_pos
        )

    def body(self, args: list[Any]) -> list[Any]:
        return args

    @v_args(meta=True)
    def block(self, meta: Meta, args: list[Any]) -> Block:
        args = self.strip_new_line_tokens(args)
        return Block(
            args[0],
            args[1:-1],
            args[-1],
            start_pos=meta.start_pos,
            end_pos=meta.end_pos,
        )

    @v_args(meta=True)
    def object(self, meta: Meta, args: list[list[Expression]]) -> Object:
        args = self.strip_new_line_tokens(args)
        fields = {kv[0]: kv[1] for kv in args}
        return Object(fields, start_pos=meta.start_pos, end_pos=meta.end_pos)

    def object_elem(self, args: list[Expression]) -> list[Expression]:
        return args

    @v_args(meta=True)
    def tuple(self, meta: Meta, args: list[Any]) -> Array:
        args = self.strip_new_line_tokens(args)
        return Array(args, start_pos=meta.start_pos, end_pos=meta.end_pos)

    @v_args(meta=True)
    def paren_expr(self, meta: Meta, args: list[Expression]) -> Parenthesis:
        args = self.strip_new_line_tokens(args)
        return Parenthesis(args[0], start_pos=meta.start_pos, end_pos=meta.end_pos)

    @v_args(meta=True)
    def function_call(self, meta: Meta, args: list[Any]) -> FunctionCall:
        args = self.strip_new_line_tokens(args)
        var_args = False
        arguments = args[1] if len(args) > 1 else []
        if len(arguments) > 0 and isinstance(arguments[-1], EllipsisMarker):
            arguments = arguments[:-1]
            var_args = True

        return FunctionCall(
            args[0], arguments, var_args, start_pos=meta.start_pos, end_pos=meta.end_pos
        )

    def arguments(
        self, args: list[Expression | EllipsisMarker]
    ) -> list[Expression | EllipsisMarker]:
        args = self.strip_new_line_tokens(args)
        return args

    def ellipsis(self, args: list[Expression]) -> EllipsisMarker:
        return EllipsisMarker()

    @v_args(meta=True)
    def index(self, meta: Meta, args: list[Expression]) -> GetIndexKey:
        return GetIndexKey(args[0], start_pos=meta.start_pos, end_pos=meta.end_pos)

    @v_args(meta=True)
    def index_expr_term(self, meta: Meta, args: list[Any]) -> GetIndex:
        index: GetIndexKey = args[1]
        return GetIndex(args[0], index, start_pos=meta.start_pos, end_pos=meta.end_pos)

    def attr_splat(self, args: list[Any]) -> list[Any]:
        return args

    @v_args(meta=True)
    def attr_splat_expr_term(self, meta: Meta, args: list[Any]) -> AttrSplat:
        return AttrSplat(*args, start_pos=meta.start_pos, end_pos=meta.end_pos)

    def full_splat(self, args: list[Any]) -> list[Any]:
        return args

    @v_args(meta=True)
    def full_splat_expr_term(self, meta: Meta, args: list[Any]) -> IndexSplat:
        return IndexSplat(*args, start_pos=meta.start_pos, end_pos=meta.end_pos)

    def new_line_or_comment(self, _args: list) -> _DiscardType:
        return Discard

    def new_line_and_or_comma(self, _args: list) -> _DiscardType:
        return Discard

    def start(self, args: list) -> dict:
        args = self.strip_new_line_tokens(args)
        return args[0]

    start_expr = start
    start_expr_or_attribute = start

    def strip_new_line_tokens(self, args: list) -> list:
        return [arg for arg in args if arg != "\n" and not arg == Discard]

    def for_intro(self, args: list[Any]) -> list[Any]:
        args = self.strip_new_line_tokens(args)
        return args

    def for_cond(self, args: list[Any]) -> Expression:
        return args[0]

    # noinspection DuplicatedCode
    @v_args(meta=True)
    def for_tuple_expr(self, meta: Meta, args: list[Any]) -> ForTupleExpression:
        args = self.strip_new_line_tokens(args)
        for_intro = args[0]
        value_ident = for_intro[1] if len(for_intro) == 3 else for_intro[0]
        key_ident = for_intro[0] if len(for_intro) == 3 else None
        collection = for_intro[-1]
        expression = args[1]
        condition = args[2] if len(args) == 3 else None

        return ForTupleExpression(
            key_ident,
            value_ident,
            collection,
            expression,
            condition,
            start_pos=meta.start_pos,
            end_pos=meta.end_pos,
        )

    # noinspection DuplicatedCode
    @v_args(meta=True)
    def for_object_expr(self, meta: Meta, args: list[Any]) -> ForObjectExpression:
        args = self.strip_new_line_tokens(args)
        for_intro = args[0]
        value_ident = for_intro[1] if len(for_intro) == 3 else for_intro[0]
        key_ident = for_intro[0] if len(for_intro) == 3 else None
        collection = for_intro[-1]
        key_expression = args[1]
        value_expression = args[2]

        grouping_mode = isinstance(args[-1], EllipsisMarker) or isinstance(
            args[-2], EllipsisMarker
        )

        condition = (
            args[-1]
            if len(args) >= 4 and not isinstance(args[-1], EllipsisMarker)
            else None
        )

        return ForObjectExpression(
            key_ident,
            value_ident,
            collection,
            key_expression,
            value_expression,
            condition,
            grouping_mode,
            start_pos=meta.start_pos,
            end_pos=meta.end_pos,
        )

    @v_args(meta=True)
    def heredoc_template(self, meta: Meta, args: list[Any]) -> Literal:
        match = HEREDOC_PATTERN.match(str(args[0]))
        if not match:
            raise RuntimeError(f"Invalid Heredoc token: {args[0]}")
        return Literal(
            f'"{match.group(2)}"', start_pos=meta.start_pos, end_pos=meta.end_pos
        )

    @v_args(meta=True)
    def heredoc_template_trim(self, meta: Meta, args: list[Any]) -> Literal:
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
            f'"{"\n".join(lines)}"', start_pos=meta.start_pos, end_pos=meta.end_pos
        )
