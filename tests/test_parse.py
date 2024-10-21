import textwrap

import pytest
from pyagnostics.exceptions import DiagnosticError
from pyagnostics.spans import SourceSpan

from pyhcl2.nodes import (
    ArrayExpression,
    Attribute,
    AttrSplat,
    BinaryExpression,
    BinaryOperator,
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
    ObjectExpression,
    Parenthesis,
    UnaryExpression,
    UnaryOperator,
)
from pyhcl2.parse import (
    parse_expr,
    parse_expr_or_stmt,
    parse_module,
)
from pyhcl2.values import Boolean, Float, Integer, Null, String


def test_parse_literal_null() -> None:
    assert parse_expr("null") == Literal(Null(), span=SourceSpan(0, 4))


def test_parse_literal_string() -> None:
    assert parse_expr('"Hello World"') == Literal(
        String("Hello World"), span=SourceSpan(0, 13)
    )


def test_parse_literal_bool() -> None:
    assert parse_expr("true") == Literal(Boolean(True), span=SourceSpan(0, 4))
    assert parse_expr("false") == Literal(Boolean(False), span=SourceSpan(0, 5))


def test_parse_literal_number() -> None:
    assert parse_expr("42") == Literal(Integer(42), span=SourceSpan(0, 2))
    assert parse_expr("42.0") == Literal(Float(42.0), span=SourceSpan(0, 4))
    assert parse_expr("42.42") == Literal(Float(42.42), span=SourceSpan(0, 5))


def test_parse_identifier() -> None:
    assert parse_expr("foo") == Identifier("foo", span=SourceSpan(0, 3))
    assert parse_expr("bar") == Identifier("bar", span=SourceSpan(0, 3))


def test_parse_unary_expr() -> None:
    assert parse_expr("-a") == UnaryExpression(
        UnaryOperator("-", span=SourceSpan(0, 1)),
        Identifier("a", span=SourceSpan(1, 2)),
        span=SourceSpan(0, 2),
    )
    assert parse_expr("!a") == UnaryExpression(
        UnaryOperator("!", span=SourceSpan(0, 1)),
        Identifier("a", span=SourceSpan(1, 2)),
        span=SourceSpan(0, 2),
    )


def test_parse_binary_expr() -> None:
    assert parse_expr("a == b") == BinaryExpression(
        BinaryOperator("==", span=SourceSpan(2, 4)),
        Identifier("a", span=SourceSpan(0, 1)),
        Identifier("b", span=SourceSpan(5, 6)),
        span=SourceSpan(0, 6),
    )
    assert parse_expr("a != b") == BinaryExpression(
        BinaryOperator("!=", span=SourceSpan(2, 4)),
        Identifier("a", span=SourceSpan(0, 1)),
        Identifier("b", span=SourceSpan(5, 6)),
        span=SourceSpan(0, 6),
    )
    assert parse_expr("a < b") == BinaryExpression(
        BinaryOperator("<", span=SourceSpan(2, 3)),
        Identifier("a", span=SourceSpan(0, 1)),
        Identifier("b", span=SourceSpan(4, 5)),
        span=SourceSpan(0, 5),
    )
    assert parse_expr("a > b") == BinaryExpression(
        BinaryOperator(">", span=SourceSpan(2, 3)),
        Identifier("a", span=SourceSpan(0, 1)),
        Identifier("b", span=SourceSpan(4, 5)),
        span=SourceSpan(0, 5),
    )
    assert parse_expr("a <= b") == BinaryExpression(
        BinaryOperator("<=", span=SourceSpan(2, 4)),
        Identifier("a", span=SourceSpan(0, 1)),
        Identifier("b", span=SourceSpan(5, 6)),
        span=SourceSpan(0, 6),
    )
    assert parse_expr("a >= b") == BinaryExpression(
        BinaryOperator(">=", span=SourceSpan(2, 4)),
        Identifier("a", span=SourceSpan(0, 1)),
        Identifier("b", span=SourceSpan(5, 6)),
        span=SourceSpan(0, 6),
    )
    assert parse_expr("a - b") == BinaryExpression(
        BinaryOperator("-", span=SourceSpan(2, 3)),
        Identifier("a", span=SourceSpan(0, 1)),
        Identifier("b", span=SourceSpan(4, 5)),
        span=SourceSpan(0, 5),
    )
    assert parse_expr("a * b") == BinaryExpression(
        BinaryOperator("*", span=SourceSpan(2, 3)),
        Identifier("a", span=SourceSpan(0, 1)),
        Identifier("b", span=SourceSpan(4, 5)),
        span=SourceSpan(0, 5),
    )
    assert parse_expr("a / b") == BinaryExpression(
        BinaryOperator("/", span=SourceSpan(2, 3)),
        Identifier("a", span=SourceSpan(0, 1)),
        Identifier("b", span=SourceSpan(4, 5)),
        span=SourceSpan(0, 5),
    )
    assert parse_expr("a % b") == BinaryExpression(
        BinaryOperator("%", span=SourceSpan(2, 3)),
        Identifier("a", span=SourceSpan(0, 1)),
        Identifier("b", span=SourceSpan(4, 5)),
        span=SourceSpan(0, 5),
    )
    assert parse_expr("a && b") == BinaryExpression(
        BinaryOperator("&&", span=SourceSpan(2, 4)),
        Identifier("a", span=SourceSpan(0, 1)),
        Identifier("b", span=SourceSpan(5, 6)),
        span=SourceSpan(0, 6),
    )
    assert parse_expr("a || b") == BinaryExpression(
        BinaryOperator("||", span=SourceSpan(2, 4)),
        Identifier("a", span=SourceSpan(0, 1)),
        Identifier("b", span=SourceSpan(5, 6)),
        span=SourceSpan(0, 6),
    )
    assert parse_expr("a + b") == BinaryExpression(
        BinaryOperator("+", span=SourceSpan(2, 3)),
        Identifier("a", span=SourceSpan(0, 1)),
        Identifier("b", span=SourceSpan(4, 5)),
        span=SourceSpan(0, 5),
    )


def test_parse_binary_precedence() -> None:
    assert parse_expr("a + b * c") == BinaryExpression(
        BinaryOperator("+", span=SourceSpan(2, 3)),
        Identifier("a", span=SourceSpan(0, 1)),
        BinaryExpression(
            BinaryOperator("*", span=SourceSpan(6, 7)),
            Identifier("b", span=SourceSpan(4, 5)),
            Identifier("c", span=SourceSpan(8, 9)),
            span=SourceSpan(4, 9),
        ),
        span=SourceSpan(0, 9),
    )
    assert parse_expr("a * b + c") == BinaryExpression(
        BinaryOperator("+", span=SourceSpan(6, 7)),
        BinaryExpression(
            BinaryOperator("*", span=SourceSpan(2, 3)),
            Identifier("a", span=SourceSpan(0, 1)),
            Identifier("b", span=SourceSpan(4, 5)),
            span=SourceSpan(0, 5),
        ),
        Identifier("c", span=SourceSpan(8, 9)),
        span=SourceSpan(0, 9),
    )
    assert parse_expr("a < b + c") == BinaryExpression(
        BinaryOperator("<", span=SourceSpan(2, 3)),
        Identifier("a", span=SourceSpan(0, 1)),
        BinaryExpression(
            BinaryOperator("+", span=SourceSpan(6, 7)),
            Identifier("b", span=SourceSpan(4, 5)),
            Identifier("c", span=SourceSpan(8, 9)),
            span=SourceSpan(4, 9),
        ),
        span=SourceSpan(0, 9),
    )
    assert parse_expr("a + b < c") == BinaryExpression(
        BinaryOperator("<", span=SourceSpan(6, 7)),
        BinaryExpression(
            BinaryOperator("+", span=SourceSpan(2, 3)),
            Identifier("a", span=SourceSpan(0, 1)),
            Identifier("b", span=SourceSpan(4, 5)),
            span=SourceSpan(0, 5),
        ),
        Identifier("c", span=SourceSpan(8, 9)),
        span=SourceSpan(0, 9),
    )
    assert parse_expr("a == b >= c") == BinaryExpression(
        BinaryOperator("==", span=SourceSpan(2, 4)),
        Identifier("a", span=SourceSpan(0, 1)),
        BinaryExpression(
            BinaryOperator(">=", span=SourceSpan(7, 9)),
            Identifier("b", span=SourceSpan(5, 6)),
            Identifier("c", span=SourceSpan(10, 11)),
            span=SourceSpan(5, 11),
        ),
        span=SourceSpan(0, 11),
    )
    assert parse_expr("a >= b == c") == BinaryExpression(
        BinaryOperator("==", span=SourceSpan(7, 9)),
        BinaryExpression(
            BinaryOperator(">=", span=SourceSpan(2, 4)),
            Identifier("a", span=SourceSpan(0, 1)),
            Identifier("b", span=SourceSpan(5, 6)),
            span=SourceSpan(0, 6),
        ),
        Identifier("c", span=SourceSpan(10, 11)),
        span=SourceSpan(0, 11),
    )
    assert parse_expr("a == b && c") == BinaryExpression(
        BinaryOperator("&&", span=SourceSpan(7, 9)),
        BinaryExpression(
            BinaryOperator("==", span=SourceSpan(2, 4)),
            Identifier("a", span=SourceSpan(0, 1)),
            Identifier("b", span=SourceSpan(5, 6)),
            span=SourceSpan(0, 6),
        ),
        Identifier("c", span=SourceSpan(10, 11)),
        span=SourceSpan(0, 11),
    )
    assert parse_expr("a && b == c") == BinaryExpression(
        BinaryOperator("&&", span=SourceSpan(2, 4)),
        Identifier("a", span=SourceSpan(0, 1)),
        BinaryExpression(
            BinaryOperator("==", span=SourceSpan(7, 9)),
            Identifier("b", span=SourceSpan(5, 6)),
            Identifier("c", span=SourceSpan(10, 11)),
            span=SourceSpan(5, 11),
        ),
        span=SourceSpan(0, 11),
    )
    assert parse_expr("a || b && c") == BinaryExpression(
        BinaryOperator("||", span=SourceSpan(2, 4)),
        Identifier("a", span=SourceSpan(0, 1)),
        BinaryExpression(
            BinaryOperator("&&", span=SourceSpan(7, 9)),
            Identifier("b", span=SourceSpan(5, 6)),
            Identifier("c", span=SourceSpan(10, 11)),
            span=SourceSpan(5, 11),
        ),
        span=SourceSpan(0, 11),
    )
    assert parse_expr("a && b || c") == BinaryExpression(
        BinaryOperator("||", span=SourceSpan(7, 9)),
        BinaryExpression(
            BinaryOperator("&&", span=SourceSpan(2, 4)),
            Identifier("a", span=SourceSpan(0, 1)),
            Identifier("b", span=SourceSpan(5, 6)),
            span=SourceSpan(0, 6),
        ),
        Identifier("c", span=SourceSpan(10, 11)),
        span=SourceSpan(0, 11),
    )


def test_parse_conditional() -> None:
    assert parse_expr("a ? b : c") == Conditional(
        Identifier("a", span=SourceSpan(0, 1)),
        Identifier("b", span=SourceSpan(4, 5)),
        Identifier("c", span=SourceSpan(8, 9)),
        span=SourceSpan(0, 9),
    )


def test_parse_paren() -> None:
    assert parse_expr("(a)") == Parenthesis(
        Identifier("a", span=SourceSpan(1, 2)), span=SourceSpan(0, 3)
    )


def test_parse_array() -> None:
    assert parse_expr("[1, 2, 3]") == ArrayExpression(
        [
            Literal(Integer(1), span=SourceSpan(1, 2)),
            Literal(Integer(2), span=SourceSpan(4, 5)),
            Literal(Integer(3), span=SourceSpan(7, 8)),
        ],
        span=SourceSpan(0, 9),
    )
    assert parse_expr("[1, 2, 3, 4]") == ArrayExpression(
        [
            Literal(Integer(1), span=SourceSpan(1, 2)),
            Literal(Integer(2), span=SourceSpan(4, 5)),
            Literal(Integer(3), span=SourceSpan(7, 8)),
            Literal(Integer(4), span=SourceSpan(10, 11)),
        ],
        span=SourceSpan(0, 12),
    )


def test_parse_array_complex() -> None:
    assert parse_expr("[(for), foo, baz]") == ArrayExpression(
        [
            Parenthesis(
                Identifier("for", span=SourceSpan(2, 5)), span=SourceSpan(1, 6)
            ),
            Identifier("foo", span=SourceSpan(8, 11)),
            Identifier("baz", span=SourceSpan(13, 16)),
        ],
        span=SourceSpan(0, 17),
    )
    with pytest.raises(DiagnosticError):
        parse_expr("[for, foo, baz]")


def test_parse_object() -> None:
    assert parse_expr('{ foo = "bar" }') == ObjectExpression(
        {
            Identifier("foo", span=SourceSpan(2, 5)): Literal(
                String("bar"), span=SourceSpan(8, 13)
            )
        },
        span=SourceSpan(0, 15),
    )
    assert parse_expr("{ foo: bar }") == ObjectExpression(
        {
            Identifier("foo", span=SourceSpan(2, 5)): Identifier(
                "bar", span=SourceSpan(7, 10)
            )
        },
        span=SourceSpan(0, 12),
    )


def test_parse_object_complex() -> None:
    assert parse_expr("{ (foo) = bar }") == ObjectExpression(
        {
            Parenthesis(
                Identifier("foo", span=SourceSpan(3, 6)), span=SourceSpan(2, 7)
            ): Identifier("bar", span=SourceSpan(10, 13))
        },
        span=SourceSpan(0, 15),
    )
    assert parse_expr('{ foo = "bar", baz = 42 }') == ObjectExpression(
        {
            Identifier("foo", span=SourceSpan(2, 5)): Literal(
                String("bar"), span=SourceSpan(8, 13)
            ),
            Identifier("baz", span=SourceSpan(15, 18)): Literal(
                Integer(42), span=SourceSpan(21, 23)
            ),
        },
        span=SourceSpan(0, 25),
    )

    with pytest.raises(DiagnosticError):
        parse_expr("{ for = 1, baz = 2 }")

    assert parse_expr('{ "for" = 1, baz = 2}') == ObjectExpression(
        {
            Literal(String("for"), span=SourceSpan(2, 7)): Literal(
                Integer(1), span=SourceSpan(10, 11)
            ),
            Identifier("baz", span=SourceSpan(13, 16)): Literal(
                Integer(2), span=SourceSpan(19, 20)
            ),
        },
        span=SourceSpan(0, 21),
    )
    assert parse_expr("{ baz = 2, for = 1}") == ObjectExpression(
        {
            Identifier("baz", span=SourceSpan(2, 5)): Literal(
                Integer(2), span=SourceSpan(8, 9)
            ),
            Identifier("for", span=SourceSpan(11, 14)): Literal(
                Integer(1), span=SourceSpan(17, 18)
            ),
        },
        span=SourceSpan(0, 19),
    )
    assert parse_expr("{ (for) = 1, baz = 2}") == ObjectExpression(
        {
            Parenthesis(
                Identifier("for", span=SourceSpan(3, 6)), span=SourceSpan(2, 7)
            ): Literal(Integer(1), span=SourceSpan(10, 11)),
            Identifier("baz", span=SourceSpan(13, 16)): Literal(
                Integer(2), span=SourceSpan(19, 20)
            ),
        },
        span=SourceSpan(0, 21),
    )


def test_parse_function_call() -> None:
    assert parse_expr("foo()") == FunctionCall(
        Identifier("foo", span=SourceSpan(0, 3)), [], span=SourceSpan(0, 5)
    )
    assert parse_expr("foo(1, 2, 3)") == FunctionCall(
        Identifier("foo", span=SourceSpan(0, 3)),
        [
            Literal(Integer(1), span=SourceSpan(4, 5)),
            Literal(Integer(2), span=SourceSpan(7, 8)),
            Literal(Integer(3), span=SourceSpan(10, 11)),
        ],
        span=SourceSpan(0, 12),
    )
    assert parse_expr("foo(1, 2, 3...)") == FunctionCall(
        Identifier("foo", span=SourceSpan(0, 3)),
        [
            Literal(Integer(1), span=SourceSpan(4, 5)),
            Literal(Integer(2), span=SourceSpan(7, 8)),
            Literal(Integer(3), span=SourceSpan(10, 11)),
        ],
        var_args=True,
        span=SourceSpan(0, 15),
    )


def test_parse_get_attr() -> None:
    assert parse_expr("foo.bar") == GetAttr(
        Identifier("foo", span=SourceSpan(0, 3)),
        GetAttrKey(Identifier("bar", span=SourceSpan(4, 7)), span=SourceSpan(3, 7)),
        span=SourceSpan(0, 7),
    )


def test_parse_get_index() -> None:
    assert parse_expr("foo[0]") == GetIndex(
        Identifier("foo", span=SourceSpan(0, 3)),
        GetIndexKey(Literal(Integer(0), span=SourceSpan(4, 5)), span=SourceSpan(3, 6)),
        span=SourceSpan(0, 6),
    )
    assert parse_expr("foo[bar]") == GetIndex(
        Identifier("foo", span=SourceSpan(0, 3)),
        GetIndexKey(Identifier("bar", span=SourceSpan(4, 7)), span=SourceSpan(3, 8)),
        span=SourceSpan(0, 8),
    )


def test_parse_get_attr_splat() -> None:
    assert parse_expr("foo.*") == AttrSplat(
        Identifier("foo", span=SourceSpan(0, 3)), [], span=SourceSpan(0, 5)
    )
    assert parse_expr("foo.*.bar") == AttrSplat(
        Identifier("foo", span=SourceSpan(0, 3)),
        [GetAttrKey(Identifier("bar", span=SourceSpan(6, 9)), span=SourceSpan(5, 9))],
        span=SourceSpan(0, 9),
    )


def test_parse_index_splat() -> None:
    assert parse_expr("foo[*]") == IndexSplat(
        Identifier("foo", span=SourceSpan(0, 3)), [], span=SourceSpan(0, 6)
    )
    assert parse_expr("foo[*].bar") == IndexSplat(
        Identifier("foo", span=SourceSpan(0, 3)),
        [GetAttrKey(Identifier("bar", span=SourceSpan(7, 10)), span=SourceSpan(6, 10))],
        span=SourceSpan(0, 10),
    )
    assert parse_expr("foo[*][3]") == IndexSplat(
        Identifier("foo", span=SourceSpan(0, 3)),
        [
            GetIndexKey(
                Literal(Integer(3), span=SourceSpan(7, 8)), span=SourceSpan(6, 9)
            )
        ],
        span=SourceSpan(0, 9),
    )
    assert parse_expr("foo[*].bar[3]") == IndexSplat(
        Identifier("foo", span=SourceSpan(0, 3)),
        [
            GetAttrKey(
                Identifier("bar", span=SourceSpan(7, 10)), span=SourceSpan(6, 10)
            ),
            GetIndexKey(
                Literal(Integer(3), span=SourceSpan(11, 12)), span=SourceSpan(10, 13)
            ),
        ],
        span=SourceSpan(0, 13),
    )


def test_parse_for_tuple_expr() -> None:
    assert parse_expr("[for a in b: a]") == ForTupleExpression(
        key_ident=None,
        value_ident=Identifier("a", span=SourceSpan(5, 6)),
        collection=Identifier("b", span=SourceSpan(10, 11)),
        value=Identifier("a", span=SourceSpan(13, 14)),
        condition=None,
        span=SourceSpan(0, 15),
    )
    assert parse_expr("[for a, b in c: a]") == ForTupleExpression(
        key_ident=Identifier("a", span=SourceSpan(5, 6)),
        value_ident=Identifier("b", span=SourceSpan(8, 9)),
        collection=Identifier("c", span=SourceSpan(13, 14)),
        value=Identifier("a", span=SourceSpan(16, 17)),
        condition=None,
        span=SourceSpan(0, 18),
    )
    assert parse_expr("[for a in b: a if a]") == ForTupleExpression(
        key_ident=None,
        value_ident=Identifier("a", span=SourceSpan(5, 6)),
        collection=Identifier("b", span=SourceSpan(10, 11)),
        value=Identifier("a", span=SourceSpan(13, 14)),
        condition=Identifier("a", span=SourceSpan(18, 19)),
        span=SourceSpan(0, 20),
    )
    assert parse_expr("[for a, b in c: a if a]") == ForTupleExpression(
        key_ident=Identifier("a", span=SourceSpan(5, 6)),
        value_ident=Identifier("b", span=SourceSpan(8, 9)),
        collection=Identifier("c", span=SourceSpan(13, 14)),
        value=Identifier("a", span=SourceSpan(16, 17)),
        condition=Identifier("a", span=SourceSpan(21, 22)),
        span=SourceSpan(0, 23),
    )


def test_parse_for_object_expr() -> None:
    assert parse_expr("{for a, b in c: a => b}") == ForObjectExpression(
        key_ident=Identifier("a", span=SourceSpan(5, 6)),
        value_ident=Identifier("b", span=SourceSpan(8, 9)),
        collection=Identifier("c", span=SourceSpan(13, 14)),
        key=Identifier("a", span=SourceSpan(16, 17)),
        value=Identifier("b", span=SourceSpan(21, 22)),
        condition=None,
        grouping_mode=False,
        span=SourceSpan(0, 23),
    )

    assert parse_expr("{for a in b: a => a}") == ForObjectExpression(
        key_ident=None,
        value_ident=Identifier("a", span=SourceSpan(5, 6)),
        collection=Identifier("b", span=SourceSpan(10, 11)),
        key=Identifier("a", span=SourceSpan(13, 14)),
        value=Identifier("a", span=SourceSpan(18, 19)),
        condition=None,
        grouping_mode=False,
        span=SourceSpan(0, 20),
    )

    assert parse_expr("{for a in b: a => a if a}") == ForObjectExpression(
        key_ident=None,
        value_ident=Identifier("a", span=SourceSpan(5, 6)),
        collection=Identifier("b", span=SourceSpan(10, 11)),
        key=Identifier("a", span=SourceSpan(13, 14)),
        value=Identifier("a", span=SourceSpan(18, 19)),
        condition=Identifier("a", span=SourceSpan(23, 24)),
        grouping_mode=False,
        span=SourceSpan(0, 25),
    )

    assert parse_expr("{for i, v in array : v => i...}") == ForObjectExpression(
        key_ident=Identifier("i", span=SourceSpan(5, 6)),
        value_ident=Identifier("v", span=SourceSpan(8, 9)),
        collection=Identifier("array", span=SourceSpan(13, 18)),
        key=Identifier("v", span=SourceSpan(21, 22)),
        value=Identifier("i", span=SourceSpan(26, 27)),
        condition=None,
        grouping_mode=True,
        span=SourceSpan(0, 31),
    )

    assert parse_expr("{for i, v in array : v => i... if i}") == ForObjectExpression(
        key_ident=Identifier("i", span=SourceSpan(5, 6)),
        value_ident=Identifier("v", span=SourceSpan(8, 9)),
        collection=Identifier("array", span=SourceSpan(13, 18)),
        key=Identifier("v", span=SourceSpan(21, 22)),
        value=Identifier("i", span=SourceSpan(26, 27)),
        condition=Identifier("i", span=SourceSpan(34, 35)),
        grouping_mode=True,
        span=SourceSpan(0, 36),
    )


def test_parse_attribute() -> None:
    assert parse_expr_or_stmt("a = b") == Attribute(
        Identifier("a", span=SourceSpan(0, 1)),
        Identifier("b", span=SourceSpan(4, 5)),
        span=SourceSpan(0, 5),
    )


def test_parse_block() -> None:
    assert parse_module("locals {\na = b\n}") == Module(
        [
            Block(
                Identifier("locals", span=SourceSpan(0, 6)),
                [],
                [
                    Attribute(
                        Identifier("a", span=SourceSpan(9, 10)),
                        Identifier("b", span=SourceSpan(13, 14)),
                        span=SourceSpan(9, 14),
                    )
                ],
                span=SourceSpan(0, 16),
            ),
        ],
        span=SourceSpan(0, 16),
    )

    assert parse_module("""resource "a" {\na = b\n}""") == Module(
        [
            Block(
                Identifier("resource", span=SourceSpan(0, 8)),
                [Literal(String("a"), span=SourceSpan(9, 12))],
                [
                    Attribute(
                        Identifier("a", span=SourceSpan(15, 16)),
                        Identifier("b", span=SourceSpan(19, 20)),
                        span=SourceSpan(15, 20),
                    )
                ],
                span=SourceSpan(0, 22),
            )
        ],
        span=SourceSpan(0, 22),
    )

    assert parse_module("""resource a "b" {\na = b\n}""") == Module(
        [
            Block(
                Identifier("resource", span=SourceSpan(0, 8)),
                [
                    Identifier("a", span=SourceSpan(9, 10)),
                    Literal(String("b"), span=SourceSpan(11, 14)),
                ],
                [
                    Attribute(
                        Identifier("a", span=SourceSpan(17, 18)),
                        Identifier("b", span=SourceSpan(21, 22)),
                        span=SourceSpan(17, 22),
                    )
                ],
                span=SourceSpan(0, 24),
            )
        ],
        span=SourceSpan(0, 24),
    )

    assert parse_module("""locals {\na = 1\nb = 2\n}""") == Module(
        [
            Block(
                Identifier("locals", span=SourceSpan(0, 6)),
                [],
                [
                    Attribute(
                        Identifier("a", span=SourceSpan(9, 10)),
                        Literal(Integer(1), span=SourceSpan(13, 14)),
                        span=SourceSpan(9, 14),
                    ),
                    Attribute(
                        Identifier("b", span=SourceSpan(15, 16)),
                        Literal(Integer(2), span=SourceSpan(19, 20)),
                        span=SourceSpan(15, 20),
                    ),
                ],
                span=SourceSpan(0, 22),
            )
        ],
        span=SourceSpan(0, 22),
    )


def test_parse_multiple_blocks() -> None:
    assert parse_module(
        textwrap.dedent("""
        block1 {
            value = "foo"
        }
        block2 arg1 {
            value = 42
        }
        block3 "arg2" arg3 {
            value = bar()
        }
        """).strip()
    ) == Module(
        span=SourceSpan(0, 100),
        body=[
            Block(
                span=SourceSpan(0, 29),
                type=Identifier(span=SourceSpan(0, 6), name="block1"),
                labels=[],
                body=[
                    Attribute(
                        span=SourceSpan(13, 26),
                        key=Identifier(span=SourceSpan(13, 18), name="value"),
                        value=Literal(span=SourceSpan(21, 26), value=String("foo")),
                    )
                ],
            ),
            Block(
                span=SourceSpan(29, 60),
                type=Identifier(span=SourceSpan(29, 35), name="block2"),
                labels=[Identifier(span=SourceSpan(36, 40), name="arg1")],
                body=[
                    Attribute(
                        span=SourceSpan(47, 57),
                        key=Identifier(span=SourceSpan(47, 52), name="value"),
                        value=Literal(span=SourceSpan(55, 57), value=Integer(42)),
                    )
                ],
            ),
            Block(
                span=SourceSpan(60, 100),
                type=Identifier(span=SourceSpan(60, 66), name="block3"),
                labels=[
                    Literal(span=SourceSpan(67, 73), value=String("arg2")),
                    Identifier(span=SourceSpan(74, 78), name="arg3"),
                ],
                body=[
                    Attribute(
                        span=SourceSpan(85, 98),
                        key=Identifier(span=SourceSpan(85, 90), name="value"),
                        value=FunctionCall(
                            span=SourceSpan(93, 98),
                            ident=Identifier(span=SourceSpan(93, 96), name="bar"),
                            args=[],
                            var_args=False,
                        ),
                    )
                ],
            ),
        ],
    )
