from __future__ import annotations

import re
import sys

from lark import Discard, Token, Transformer

from pyhcl2._ast import (
    Array,
    Attribute,
    AttrSplat,
    BinaryOp,
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
    UnaryOp,
)

HEREDOC_PATTERN = re.compile(r'<<([a-zA-Z][a-zA-Z0-9._-]+)\n((.|\n)*?)\n\s*\1', re.S)
HEREDOC_TRIM_PATTERN = re.compile(r'<<-([a-zA-Z][a-zA-Z0-9._-]+)\n((.|\n)*?)\n\s*\1', re.S)


class EllipsisMarker:
    pass


# noinspection PyMethodMayBeStatic
class ToAstTransformer(Transformer):
    def add_op(self, args: list[Token]) -> str:
        return args[0].value

    def mul_op(self, args: list[Token]) -> str:
        return args[0].value

    def comp_op(self, args: list[Token]) -> str:
        return args[0].value

    def term(self, args: list[any]) -> BinaryOp:
        return BinaryOp(args[1], args[0], args[2])

    def add_expr(self, args: list[any]) -> BinaryOp:
        return BinaryOp(args[1], args[0], args[2])

    def compare(self, args: list[any]) -> BinaryOp:
        args = self.strip_new_line_tokens(args)
        return BinaryOp(args[1], args[0], args[2])

    def and_test(self, args: list[any]) -> BinaryOp:
        args = self.strip_new_line_tokens(args)
        return BinaryOp("&&", args[0], args[1])

    def or_test(self, args: list[any]) -> BinaryOp:
        return BinaryOp("||", args[0], args[1])

    def not_test(self, args: list[any]) -> UnaryOp:
        return UnaryOp("!", args[0])

    def neg(self, args: list[any]) -> UnaryOp:
        return UnaryOp("-", args[0])

    def conditional(self, args: list[any]) -> Conditional:
        return Conditional(args[0], args[1], args[2])

    def get_attr(self, args: list[any]) -> GetAttrKey:
        # print("get_attr", args)
        return GetAttrKey(args[0])

    def get_attr_expr_term(self, args: list[any]) -> GetAttr:
        # print("get_attr_expr_term", args)
        get_attr: GetAttrKey = args[1]
        return GetAttr(args[0], get_attr)

    def float_lit(self, args: list[Token]) -> Literal:
        return Literal(float("".join([str(arg) for arg in args])))

    def null_lit(self, _args: list[Token]) -> Literal:
        return Literal(None)

    def int_lit(self, args: list[Token]) -> Literal:
        # print("int_lit", args)
        return Literal(int("".join([str(arg) for arg in args])))

    #
    def expr_term(self, args: list[any]) -> any:
        args = self.strip_new_line_tokens(args)
        # print("expr_term", args)
        return args[0]

    def bool_lit(self, value: list[Token]) -> Literal:
        # print("bool_lit", value)
        match value[0].value.lower():
            case "true":
                return Literal(True)
            case "false":
                return Literal(False)
        raise ValueError(f"Invalid boolean value: {value[0].value}")

    def string_lit(self, value: list[Token]) -> Literal:
        # print("string_lit", value)
        return Literal(value[0].value[1:-1])

    def identifier(self, value: list[Token]) -> Expression:
        # print("identifier", value)
        return Identifier(value[0].value)

    def attribute(self, args: list[Expression]) -> Attribute:
        args = self.strip_new_line_tokens(args)
        # print("attribute", args)
        return Attribute(args[0].name, args[1])

    def body(self, args: list[any]) -> list[any]:
        return args

    def block(self, args: list[any]) -> Block:
        args = self.strip_new_line_tokens(args)
        return Block(args[0].name, args[1:-1], args[-1])

    def object(self, args: list[list[Expression]]) -> Object:
        args = self.strip_new_line_tokens(args)
        # print("object", args)
        fields = {
            kv[0]: kv[1] for kv in args
        }

        return Object(fields)

    def object_elem(self, args: list[Expression]) -> list[Expression]:
        # print("object_elem", args)
        return args

    def tuple(self, args: list[any]) -> Array:
        args = self.strip_new_line_tokens(args)
        return Array(args)

    def paren_expr(self, args: list[Expression]) -> Parenthesis:
        args = self.strip_new_line_tokens(args)
        return Parenthesis(args[0])

    def function_call(self, args: list[any]) -> FunctionCall:
        args = self.strip_new_line_tokens(args)
        # print(args)
        var_args = False
        arguments = args[1] if len(args) > 1 else []
        if len(arguments) > 0 and isinstance(args[-1], EllipsisMarker):
            arguments = arguments[:-1]
            var_args = True

        return FunctionCall(args[0], arguments, var_args)

    def arguments(self, args: list[Expression | EllipsisMarker]) -> list[Expression]:
        args = self.strip_new_line_tokens(args)
        # print("arguments", args)
        return args

    def ellipsis(self, args: list[Expression]) -> EllipsisMarker:
        # print("elipsis", args)
        return EllipsisMarker()

    def index(self, args: list[Expression]) -> GetIndexKey:
        # print("index", args)
        return GetIndexKey(args[0])

    def index_expr_term(self, args: list[any]) -> GetIndex:
        # print("index_expr_term", args)
        index: GetIndexKey = args[1]
        return GetIndex(args[0], index)

    def attr_splat(self, args: list[any]) -> list[any]:
        # print("attr_splat", args)
        return args

    def attr_splat_expr_term(self, args: list[any]) -> AttrSplat:
        # print("attr_splat_expr_term", args)
        return AttrSplat(*args)

    def full_splat(self, args: list[any]) -> list[any]:
        # print("full_splat", args)
        return args

    def full_splat_expr_term(self, args: list[any]) -> IndexSplat:
        # print("full_splat_expr_term", args)
        return IndexSplat(*args)

    def new_line_or_comment(self, _args: list) -> Discard:
        return Discard()

    def new_line_and_or_comma(self, _args: list) -> Discard:
        return Discard()

    def start(self, args: list) -> dict:
        args = self.strip_new_line_tokens(args)
        return args[0]

    start_expr = start
    start_expr_or_attribute = start

    def strip_new_line_tokens(self, args: list) -> list:
        return [arg for arg in args if arg != "\n" and not isinstance(arg, Discard)]

    def for_intro(self, args: list[any]) -> list[any]:
        args = self.strip_new_line_tokens(args)
        # print("for_intro", args)
        return args

    def for_cond(self, args: list[any]) -> Expression:
        # print("for_cond", args)
        return args[0]

    # noinspection DuplicatedCode
    def for_tuple_expr(self, args: list[any]) -> ForTupleExpression:
        args = self.strip_new_line_tokens(args)
        # print("for_tuple_expr", args)
        for_intro = args[0]
        value_ident = for_intro[0]
        key_ident = for_intro[1] if len(for_intro) == 3 else None  # noqa: PLR2004
        collection = for_intro[-1]
        expression = args[1]
        condition = args[2] if len(args) == 3 else None  # noqa: PLR2004

        return ForTupleExpression(
            key_ident,
            value_ident,
            collection,
            expression,
            condition
        )

    # noinspection DuplicatedCode
    def for_object_expr(self, args: list[any]) -> ForObjectExpression:
        args = self.strip_new_line_tokens(args)
        # print("for_tuple_expr", args)
        for_intro = args[0]
        value_ident = for_intro[0]
        key_ident = for_intro[1] if len(for_intro) == 3 else None  # noqa: PLR2004
        collection = for_intro[-1]
        key_expression = args[1]
        value_expression = args[2]
        condition = args[3] if len(args) == 4 else None  # noqa: PLR2004

        return ForObjectExpression(
            key_ident,
            value_ident,
            collection,
            key_expression,
            value_expression,
            condition
        )

    def heredoc_template(self, args: list[any]) -> Literal:
        match = HEREDOC_PATTERN.match(str(args[0]))
        if not match:
            raise RuntimeError("Invalid Heredoc token: %s" % args[0])
        return Literal('"%s"' % match.group(2))

    def heredoc_template_trim(self, args: list[any]) -> Literal:
        match = HEREDOC_TRIM_PATTERN.match(str(args[0]))
        if not match:
            raise RuntimeError("Invalid Heredoc token: %s" % args[0])

        text = match.group(2)
        lines = text.split('\n')

        # calculate the min number of leading spaces in each line
        min_spaces = sys.maxsize
        for line in lines:
            leading_spaces = len(line) - len(line.lstrip(' '))
            min_spaces = min(min_spaces, leading_spaces)

        # trim off that number of leading spaces from each line
        lines = [line[min_spaces:] for line in lines]

        return Literal('"%s"' % '\n'.join(lines))
