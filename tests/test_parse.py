import pytest
from lark import UnexpectedToken
from pyhcl2 import (
    Array,
    Attribute,
    AttrSplat,
    BinaryOp,
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
    Module,
    Object,
    Parenthesis,
    UnaryOp,
    parse_expr,
    parse_expr_or_attribute,
    parse_module,
)


def test_parse_literal_null() -> None:
    assert parse_expr("null") == Literal(None)


def test_parse_literal_string() -> None:
    assert parse_expr('"Hello World"') == Literal("Hello World")


def test_parse_literal_bool() -> None:
    assert parse_expr("true") == Literal(True)
    assert parse_expr("false") == Literal(False)


def test_parse_literal_number() -> None:
    assert parse_expr("42") == Literal(42)
    assert parse_expr("42.0") == Literal(42.0)
    assert parse_expr("42.42") == Literal(42.42)


def test_parse_identifier() -> None:
    assert parse_expr("foo") == Identifier("foo")
    assert parse_expr("bar") == Identifier("bar")


def test_parse_unary_expr() -> None:
    assert parse_expr("-a") == UnaryOp("-", Identifier("a"))
    assert parse_expr("!a") == UnaryOp("!", Identifier("a"))


def test_parse_binary_expr() -> None:
    assert parse_expr("a == b") == BinaryOp("==", Identifier("a"), Identifier("b"))
    assert parse_expr("a != b") == BinaryOp("!=", Identifier("a"), Identifier("b"))
    assert parse_expr("a < b") == BinaryOp("<", Identifier("a"), Identifier("b"))
    assert parse_expr("a > b") == BinaryOp(">", Identifier("a"), Identifier("b"))
    assert parse_expr("a <= b") == BinaryOp("<=", Identifier("a"), Identifier("b"))
    assert parse_expr("a >= b") == BinaryOp(">=", Identifier("a"), Identifier("b"))
    assert parse_expr("a - b") == BinaryOp("-", Identifier("a"), Identifier("b"))
    assert parse_expr("a * b") == BinaryOp("*", Identifier("a"), Identifier("b"))
    assert parse_expr("a / b") == BinaryOp("/", Identifier("a"), Identifier("b"))
    assert parse_expr("a % b") == BinaryOp("%", Identifier("a"), Identifier("b"))
    assert parse_expr("a && b") == BinaryOp("&&", Identifier("a"), Identifier("b"))
    assert parse_expr("a || b") == BinaryOp("||", Identifier("a"), Identifier("b"))
    assert parse_expr("a + b") == BinaryOp("+", Identifier("a"), Identifier("b"))


def test_parse_binary_precedence() -> None:
    assert parse_expr("a + b * c") == BinaryOp(
        "+", Identifier("a"), BinaryOp("*", Identifier("b"), Identifier("c"))
    )
    assert parse_expr("a * b + c") == BinaryOp(
        "+", BinaryOp("*", Identifier("a"), Identifier("b")), Identifier("c")
    )
    assert parse_expr("a < b + c") == BinaryOp(
        "<", Identifier("a"), BinaryOp("+", Identifier("b"), Identifier("c"))
    )
    assert parse_expr("a + b < c") == BinaryOp(
        "<", BinaryOp("+", Identifier("a"), Identifier("b")), Identifier("c")
    )
    assert parse_expr("a == b >= c") == BinaryOp(
        "==", Identifier("a"), BinaryOp(">=", Identifier("b"), Identifier("c"))
    )
    assert parse_expr("a >= b == c") == BinaryOp(
        "==", BinaryOp(">=", Identifier("a"), Identifier("b")), Identifier("c")
    )
    assert parse_expr("a == b && c") == BinaryOp(
        "&&", BinaryOp("==", Identifier("a"), Identifier("b")), Identifier("c")
    )
    assert parse_expr("a && b == c") == BinaryOp(
        "&&", Identifier("a"), BinaryOp("==", Identifier("b"), Identifier("c"))
    )
    assert parse_expr("a || b && c") == BinaryOp(
        "||", Identifier("a"), BinaryOp("&&", Identifier("b"), Identifier("c"))
    )
    assert parse_expr("a && b || c") == BinaryOp(
        "||", BinaryOp("&&", Identifier("a"), Identifier("b")), Identifier("c")
    )


def test_parse_conditional() -> None:
    assert parse_expr("a ? b : c") == Conditional(
        Identifier("a"), Identifier("b"), Identifier("c")
    )


def test_parse_paren() -> None:
    assert parse_expr("(a)") == Parenthesis(Identifier("a"))


def test_parse_array() -> None:
    assert parse_expr("[1, 2, 3]") == Array([Literal(1), Literal(2), Literal(3)])
    assert parse_expr("[1, 2, 3, 4]") == Array(
        [Literal(1), Literal(2), Literal(3), Literal(4)]
    )


def test_parse_array_complex() -> None:
    assert parse_expr("[(for), foo, baz]") == Array(
        [Parenthesis(Identifier("for")), Identifier("foo"), Identifier("baz")]
    )
    with pytest.raises(UnexpectedToken):
        parse_expr("[for, foo, baz]")


def test_parse_object() -> None:
    assert parse_expr('{ foo = "bar" }') == Object({Identifier("foo"): Literal("bar")})
    assert parse_expr("{ foo: bar }") == Object({Identifier("foo"): Identifier("bar")})


def test_parse_object_complex() -> None:
    assert parse_expr("{ (foo) = bar }") == Object(
        {Parenthesis(Identifier("foo")): Identifier("bar")}
    )
    assert parse_expr('{ foo = "bar", baz = 42 }') == Object(
        {Identifier("foo"): Literal("bar"), Identifier("baz"): Literal(42)}
    )

    with pytest.raises(UnexpectedToken):
        parse_expr("{ for = 1, baz = 2 }")

    assert parse_expr('{ "for" = 1, baz = 2}') == Object(
        {Literal("for"): Literal(1), Identifier("baz"): Literal(2)}
    )
    assert parse_expr("{ baz = 2, for = 1}") == Object(
        {Identifier("baz"): Literal(2), Identifier("for"): Literal(1)}
    )
    assert parse_expr("{ (for) = 1, baz = 2}") == Object(
        {Parenthesis(Identifier("for")): Literal(1), Identifier("baz"): Literal(2)}
    )


def test_parse_function_call() -> None:
    assert parse_expr("foo()") == FunctionCall(Identifier("foo"), [])
    assert parse_expr("foo(1, 2, 3)") == FunctionCall(
        Identifier("foo"), [Literal(1), Literal(2), Literal(3)]
    )
    assert parse_expr("foo(1, 2, 3...)") == FunctionCall(
        Identifier("foo"), [Literal(1), Literal(2), Literal(3)], var_args=True
    )


def test_parse_get_attr() -> None:
    assert parse_expr("foo.bar") == GetAttr(
        Identifier("foo"), GetAttrKey(Identifier("bar"))
    )


def test_parse_get_index() -> None:
    assert parse_expr("foo[0]") == GetIndex(Identifier("foo"), GetIndexKey(Literal(0)))
    assert parse_expr("foo[bar]") == GetIndex(
        Identifier("foo"), GetIndexKey(Identifier("bar"))
    )


def test_parse_get_attr_splat() -> None:
    assert parse_expr("foo.*") == AttrSplat(Identifier("foo"), [])
    assert parse_expr("foo.*.bar") == AttrSplat(
        Identifier("foo"), [GetAttrKey(Identifier("bar"))]
    )


def test_parse_index_splat() -> None:
    assert parse_expr("foo[*]") == IndexSplat(Identifier("foo"), [])
    assert parse_expr("foo[*].bar") == IndexSplat(
        Identifier("foo"), [GetAttrKey(Identifier("bar"))]
    )
    assert parse_expr("foo[*][3]") == IndexSplat(
        Identifier("foo"), [GetIndexKey(Literal(3))]
    )
    assert parse_expr("foo[*].bar[3]") == IndexSplat(
        Identifier("foo"), [GetAttrKey(Identifier("bar")), GetIndexKey(Literal(3))]
    )


def test_parse_for_tuple_expr() -> None:
    assert parse_expr("[for a in b: a]") == ForTupleExpression(
        key_ident=None,
        value_ident=Identifier("a"),
        collection=Identifier("b"),
        value=Identifier("a"),
        condition=None,
    )
    assert parse_expr("[for a, b in c: a]") == ForTupleExpression(
        key_ident=Identifier("a"),
        value_ident=Identifier("b"),
        collection=Identifier("c"),
        value=Identifier("a"),
        condition=None,
    )
    assert parse_expr("[for a in b: a if a]") == ForTupleExpression(
        key_ident=None,
        value_ident=Identifier("a"),
        collection=Identifier("b"),
        value=Identifier("a"),
        condition=Identifier("a"),
    )
    assert parse_expr("[for a, b in c: a if a]") == ForTupleExpression(
        key_ident=Identifier("a"),
        value_ident=Identifier("b"),
        collection=Identifier("c"),
        value=Identifier("a"),
        condition=Identifier("a"),
    )


def test_parse_for_object_expr() -> None:
    assert parse_expr("{for a, b in c: a => b}") == ForObjectExpression(
        key_ident=Identifier("a"),
        value_ident=Identifier("b"),
        collection=Identifier("c"),
        key=Identifier("a"),
        value=Identifier("b"),
        condition=None,
        grouping_mode=False,
    )

    assert parse_expr("{for a in b: a => a}") == ForObjectExpression(
        key_ident=None,
        value_ident=Identifier("a"),
        collection=Identifier("b"),
        key=Identifier("a"),
        value=Identifier("a"),
        condition=None,
        grouping_mode=False,
    )

    assert parse_expr("{for a in b: a => a if a}") == ForObjectExpression(
        key_ident=None,
        value_ident=Identifier("a"),
        collection=Identifier("b"),
        key=Identifier("a"),
        value=Identifier("a"),
        condition=Identifier("a"),
        grouping_mode=False,
    )

    assert parse_expr("{for i, v in array : v => i...}") == ForObjectExpression(
        key_ident=Identifier("i"),
        value_ident=Identifier("v"),
        collection=Identifier("array"),
        key=Identifier("v"),
        value=Identifier("i"),
        condition=None,
        grouping_mode=True,
    )

    assert parse_expr("{for i, v in array : v => i... if i}") == ForObjectExpression(
        key_ident=Identifier("i"),
        value_ident=Identifier("v"),
        collection=Identifier("array"),
        key=Identifier("v"),
        value=Identifier("i"),
        condition=Identifier("i"),
        grouping_mode=True,
    )


def test_parse_attribute() -> None:
    assert parse_expr_or_attribute("a = b") == Attribute("a", Identifier("b"))


def test_parse_block() -> None:
    assert parse_module("""
    locals {
        a = b
    }
    """) == Module([Block("locals", [], [Attribute("a", Identifier("b"))])])

    assert parse_module("""
    resource "a" {
        a = b
    }
    """) == Module(
        [Block("resource", [Literal("a")], [Attribute("a", Identifier("b"))])]
    )

    assert parse_module("""
    resource a "b" {
        a = b
    }
    """) == Module(
        [
            Block(
                "resource",
                [Identifier("a"), Literal("b")],
                [Attribute("a", Identifier("b"))],
            )
        ]
    )

    assert parse_module("""
    locals {
        a = 1
        b = 2
    }
    """) == Module(
        [Block("locals", [], [Attribute("a", Literal(1)), Attribute("b", Literal(2))])]
    )
