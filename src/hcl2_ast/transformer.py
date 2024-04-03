""" Uses python-hcl2 to parse a Kraken configuration file, but outputs it in a different format that instead
retains the order of assignments and blocks. """

import typing as t

from hcl2.transformer import DictTransformer  # type: ignore[import]
from lark import Token

from hcl2_ast._ast import (
    Array,
    Attribute,
    AttrSplat,
    BinaryOp,
    Block,
    Expression,
    FunctionCall,
    GetAttr,
    GetIndex,
    Identifier,
    IndexSplat,
    Literal,
    Object,
    Conditional,
    UnaryOp,
)


class ToAstTransformer(DictTransformer):  # type: ignore[misc]
    def to_expression(self, value: t.Any) -> Expression:
        if isinstance(value, Expression):
            return value
        elif type(value) == str:
            if "Identifier(" in value:
                # Something in Lark (?) converts the value to a string, but that's only if we don't handle
                # the case of this value elsewhere.
                raise RuntimeError("unhandled syntactical element: " + repr(value))
            return Literal(value)
        else:
            raise TypeError(value)

    # DictTransformer

    def add_op(self, args):
        return str(args[0])

    def mul_op(self, args):
        return str(args[0])

    def comp_op(self, args):
        return str(args[0])

    def term(self, args):
        return BinaryOp(args[1], args[0], args[2])

    def add_expr(self, args):
        return BinaryOp(args[1], args[0], args[2])

    def compare(self, args):
        return BinaryOp(args[1], args[0], args[2])

    def not_test(self, args):
        return UnaryOp("!", args[0])

    def and_test(self, args):
        return BinaryOp("&&", args[0], args[1])

    def or_test(self, args):
        return BinaryOp("||", args[0], args[1])

    def neg(self, args):
        return UnaryOp("-", args[0])

    def conditional(self, args):
        return Conditional(args[0], args[1], args[2])


    def get_attr(self, args: t.List[t.Any]) -> Expression:
        return self.to_expression(args[0])

    def get_attr_expr_term(self, args: t.List[t.Any]) -> GetAttr:
        assert len(args) == 2, args
        if isinstance(args[0], Expression):
            on = args[0]
        else:
            on = Identifier(args[0])
        return GetAttr(on, args[1].name)

    def float_lit(self, args: t.List[t.Any]) -> Literal:
        return Literal(super().float_lit(args))

    def int_lit(self, args: t.List[t.Any]) -> Literal:
        return Literal(super().int_lit(args))

    def expr_term(self, args: t.List[t.Any]) -> t.Union[Literal, t.Any]:
        if isinstance(args[0], Token) and args[0].type == "STRING_LIT":
            return Literal(self.strip_quotes(args[0].value))
        return super().expr_term(args)

    def identifier(self, value: t.List[Token]) -> Expression:
        # Making identifier a token by capitalizing it to IDENTIFIER
        # seems to return a token object instead of the str
        # So treat it like a regular rule
        # In this case we just convert the whole thing to a string
        if value[0].value == "null":
            return Literal(None)
        if value[0].value == "true":
            return Literal(True)
        if value[0].value == "false":
            return Literal(False)
        return Identifier(str(value[0]))

    def attribute(self, args: t.List[t.Any]) -> Attribute:
        return Attribute(args[0].name, self.to_expression(args[1]))

    def function_call(self, args: t.List[t.Any]) -> FunctionCall:
        args = self.strip_new_line_tokens(args)
        assert len(args) in (1, 2), args
        if len(args) == 1:
            args.append([])
        args[1] = [self.to_expression(self.strip_quotes(arg)) for arg in args[1]]
        return FunctionCall(args[0].name, args[1])

    def body(self, args: t.List[t.Any]) -> t.List[t.Any]:
        return args

    def block(self, args: t.List[t.Any]) -> Block:
        args = self.strip_new_line_tokens(args)

        # if the last token is a string instead of an object then the block is empty
        # such as 'foo "bar" "baz" {}'
        # in that case append an empty object
        if isinstance(args[-1], str):
            args.append({})

        name = args[0].name
        body = args[-1]
        args = [self.to_expression(self.strip_quotes(arg)) for arg in args[1:-1]]

        return Block(name, args, body)

    def object(self, args: t.List[t.Any]) -> Object:
        args = self.strip_new_line_tokens(args)
        result: t.Dict[str, t.Any] = {}
        for arg in args:
            result.update(arg)
        return Object(result)

    def tuple(self, args: t.List[t.Any]) -> Array:
        return Array(super().tuple(args))

    def index(self, args: t.List[t.Any]) -> t.Any:
        return args[0]

    def index_expr_term(self, args: t.List[t.Any]) -> GetIndex:
        return GetIndex(args[0], args[1])

    def attr_splat(self, args: t.List[t.Any]) -> t.List[t.Any]:
        return args

    def attr_splat_expr_term(self, args: t.List[t.Any]) -> Expression:
        node: Expression = AttrSplat(args[0])
        for other in args[1]:
            if isinstance(other, Identifier):
                node = GetAttr(node, other.name)
            else:
                assert False, type(other)
        return node

    def full_splat(self, args: t.List[t.Any]) -> t.List[t.Any]:
        return args

    def full_splat_expr_term(self, args: t.List[t.Any]) -> Expression:
        node: Expression = IndexSplat(args[0])
        for other in args[1]:
            if isinstance(other, Identifier):
                node = GetAttr(node, other.name)
            else:
                assert False, type(other)
        return node
    def __default__(self, data, children, meta):
        raise RuntimeError(f"unhandled syntactical element: {data!r}")
