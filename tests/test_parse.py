import textwrap

import pytest
from lark import UnexpectedToken
from pyhcl2 import (
    Array,
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
    Object,
    Parenthesis,
    UnaryExpression,
    UnaryOperator,
    parse_expr,
    parse_expr_or_attribute,
    parse_module,
)


def test_parse_literal_null() -> None:
    assert parse_expr("null") == Literal(None, start_pos=0, end_pos=4)


def test_parse_literal_string() -> None:
    assert parse_expr('"Hello World"') == Literal(
        "Hello World", start_pos=0, end_pos=13
    )


def test_parse_literal_bool() -> None:
    assert parse_expr("true") == Literal(True, start_pos=0, end_pos=4)
    assert parse_expr("false") == Literal(False, start_pos=0, end_pos=5)


def test_parse_literal_number() -> None:
    assert parse_expr("42") == Literal(42, start_pos=0, end_pos=2)
    assert parse_expr("42.0") == Literal(42.0, start_pos=0, end_pos=4)
    assert parse_expr("42.42") == Literal(42.42, start_pos=0, end_pos=5)


def test_parse_identifier() -> None:
    assert parse_expr("foo") == Identifier("foo", start_pos=0, end_pos=3)
    assert parse_expr("bar") == Identifier("bar", start_pos=0, end_pos=3)


def test_parse_unary_expr() -> None:
    assert parse_expr("-a") == UnaryExpression(
        UnaryOperator("-", start_pos=0, end_pos=1),
        Identifier("a", start_pos=1, end_pos=2),
        start_pos=0,
        end_pos=2,
    )
    assert parse_expr("!a") == UnaryExpression(
        UnaryOperator("!", start_pos=0, end_pos=1),
        Identifier("a", start_pos=1, end_pos=2),
        start_pos=0,
        end_pos=2,
    )


def test_parse_binary_expr() -> None:
    assert parse_expr("a == b") == BinaryExpression(
        BinaryOperator("==", start_pos=2, end_pos=4),
        Identifier("a", start_pos=0, end_pos=1),
        Identifier("b", start_pos=5, end_pos=6),
        start_pos=0,
        end_pos=6,
    )
    assert parse_expr("a != b") == BinaryExpression(
        BinaryOperator("!=", start_pos=2, end_pos=4),
        Identifier("a", start_pos=0, end_pos=1),
        Identifier("b", start_pos=5, end_pos=6),
        start_pos=0,
        end_pos=6,
    )
    assert parse_expr("a < b") == BinaryExpression(
        BinaryOperator("<", start_pos=2, end_pos=3),
        Identifier("a", start_pos=0, end_pos=1),
        Identifier("b", start_pos=4, end_pos=5),
        start_pos=0,
        end_pos=5,
    )
    assert parse_expr("a > b") == BinaryExpression(
        BinaryOperator(">", start_pos=2, end_pos=3),
        Identifier("a", start_pos=0, end_pos=1),
        Identifier("b", start_pos=4, end_pos=5),
        start_pos=0,
        end_pos=5,
    )
    assert parse_expr("a <= b") == BinaryExpression(
        BinaryOperator("<=", start_pos=2, end_pos=4),
        Identifier("a", start_pos=0, end_pos=1),
        Identifier("b", start_pos=5, end_pos=6),
        start_pos=0,
        end_pos=6,
    )
    assert parse_expr("a >= b") == BinaryExpression(
        BinaryOperator(">=", start_pos=2, end_pos=4),
        Identifier("a", start_pos=0, end_pos=1),
        Identifier("b", start_pos=5, end_pos=6),
        start_pos=0,
        end_pos=6,
    )
    assert parse_expr("a - b") == BinaryExpression(
        BinaryOperator("-", start_pos=2, end_pos=3),
        Identifier("a", start_pos=0, end_pos=1),
        Identifier("b", start_pos=4, end_pos=5),
        start_pos=0,
        end_pos=5,
    )
    assert parse_expr("a * b") == BinaryExpression(
        BinaryOperator("*", start_pos=2, end_pos=3),
        Identifier("a", start_pos=0, end_pos=1),
        Identifier("b", start_pos=4, end_pos=5),
        start_pos=0,
        end_pos=5,
    )
    assert parse_expr("a / b") == BinaryExpression(
        BinaryOperator("/", start_pos=2, end_pos=3),
        Identifier("a", start_pos=0, end_pos=1),
        Identifier("b", start_pos=4, end_pos=5),
        start_pos=0,
        end_pos=5,
    )
    assert parse_expr("a % b") == BinaryExpression(
        BinaryOperator("%", start_pos=2, end_pos=3),
        Identifier("a", start_pos=0, end_pos=1),
        Identifier("b", start_pos=4, end_pos=5),
        start_pos=0,
        end_pos=5,
    )
    assert parse_expr("a && b") == BinaryExpression(
        BinaryOperator("&&", start_pos=2, end_pos=4),
        Identifier("a", start_pos=0, end_pos=1),
        Identifier("b", start_pos=5, end_pos=6),
        start_pos=0,
        end_pos=6,
    )
    assert parse_expr("a || b") == BinaryExpression(
        BinaryOperator("||", start_pos=2, end_pos=4),
        Identifier("a", start_pos=0, end_pos=1),
        Identifier("b", start_pos=5, end_pos=6),
        start_pos=0,
        end_pos=6,
    )
    assert parse_expr("a + b") == BinaryExpression(
        BinaryOperator("+", start_pos=2, end_pos=3),
        Identifier("a", start_pos=0, end_pos=1),
        Identifier("b", start_pos=4, end_pos=5),
        start_pos=0,
        end_pos=5,
    )


def test_parse_binary_precedence() -> None:
    assert parse_expr("a + b * c") == BinaryExpression(
        BinaryOperator("+", start_pos=2, end_pos=3),
        Identifier("a", start_pos=0, end_pos=1),
        BinaryExpression(
            BinaryOperator("*", start_pos=6, end_pos=7),
            Identifier("b", start_pos=4, end_pos=5),
            Identifier("c", start_pos=8, end_pos=9),
            start_pos=4,
            end_pos=9,
        ),
        start_pos=0,
        end_pos=9,
    )
    assert parse_expr("a * b + c") == BinaryExpression(
        BinaryOperator("+", start_pos=6, end_pos=7),
        BinaryExpression(
            BinaryOperator("*", start_pos=2, end_pos=3),
            Identifier("a", start_pos=0, end_pos=1),
            Identifier("b", start_pos=4, end_pos=5),
            start_pos=0,
            end_pos=5,
        ),
        Identifier("c", start_pos=8, end_pos=9),
        start_pos=0,
        end_pos=9,
    )
    assert parse_expr("a < b + c") == BinaryExpression(
        BinaryOperator("<", start_pos=2, end_pos=3),
        Identifier("a", start_pos=0, end_pos=1),
        BinaryExpression(
            BinaryOperator("+", start_pos=6, end_pos=7),
            Identifier("b", start_pos=4, end_pos=5),
            Identifier("c", start_pos=8, end_pos=9),
            start_pos=4,
            end_pos=9,
        ),
        start_pos=0,
        end_pos=9,
    )
    assert parse_expr("a + b < c") == BinaryExpression(
        BinaryOperator("<", start_pos=6, end_pos=7),
        BinaryExpression(
            BinaryOperator("+", start_pos=2, end_pos=3),
            Identifier("a", start_pos=0, end_pos=1),
            Identifier("b", start_pos=4, end_pos=5),
            start_pos=0,
            end_pos=5,
        ),
        Identifier("c", start_pos=8, end_pos=9),
        start_pos=0,
        end_pos=9,
    )
    assert parse_expr("a == b >= c") == BinaryExpression(
        BinaryOperator("==", start_pos=2, end_pos=4),
        Identifier("a", start_pos=0, end_pos=1),
        BinaryExpression(
            BinaryOperator(">=", start_pos=7, end_pos=9),
            Identifier("b", start_pos=5, end_pos=6),
            Identifier("c", start_pos=10, end_pos=11),
            start_pos=5,
            end_pos=11,
        ),
        start_pos=0,
        end_pos=11,
    )
    assert parse_expr("a >= b == c") == BinaryExpression(
        BinaryOperator("==", start_pos=7, end_pos=9),
        BinaryExpression(
            BinaryOperator(">=", start_pos=2, end_pos=4),
            Identifier("a", start_pos=0, end_pos=1),
            Identifier("b", start_pos=5, end_pos=6),
            start_pos=0,
            end_pos=6,
        ),
        Identifier("c", start_pos=10, end_pos=11),
        start_pos=0,
        end_pos=11,
    )
    assert parse_expr("a == b && c") == BinaryExpression(
        BinaryOperator("&&", start_pos=7, end_pos=9),
        BinaryExpression(
            BinaryOperator("==", start_pos=2, end_pos=4),
            Identifier("a", start_pos=0, end_pos=1),
            Identifier("b", start_pos=5, end_pos=6),
            start_pos=0,
            end_pos=6,
        ),
        Identifier("c", start_pos=10, end_pos=11),
        start_pos=0,
        end_pos=11,
    )
    assert parse_expr("a && b == c") == BinaryExpression(
        BinaryOperator("&&", start_pos=2, end_pos=4),
        Identifier("a", start_pos=0, end_pos=1),
        BinaryExpression(
            BinaryOperator("==", start_pos=7, end_pos=9),
            Identifier("b", start_pos=5, end_pos=6),
            Identifier("c", start_pos=10, end_pos=11),
            start_pos=5,
            end_pos=11,
        ),
        start_pos=0,
        end_pos=11,
    )
    assert parse_expr("a || b && c") == BinaryExpression(
        BinaryOperator("||", start_pos=2, end_pos=4),
        Identifier("a", start_pos=0, end_pos=1),
        BinaryExpression(
            BinaryOperator("&&", start_pos=7, end_pos=9),
            Identifier("b", start_pos=5, end_pos=6),
            Identifier("c", start_pos=10, end_pos=11),
            start_pos=5,
            end_pos=11,
        ),
        start_pos=0,
        end_pos=11,
    )
    assert parse_expr("a && b || c") == BinaryExpression(
        BinaryOperator("||", start_pos=7, end_pos=9),
        BinaryExpression(
            BinaryOperator("&&", start_pos=2, end_pos=4),
            Identifier("a", start_pos=0, end_pos=1),
            Identifier("b", start_pos=5, end_pos=6),
            start_pos=0,
            end_pos=6,
        ),
        Identifier("c", start_pos=10, end_pos=11),
        start_pos=0,
        end_pos=11,
    )


def test_parse_conditional() -> None:
    assert parse_expr("a ? b : c") == Conditional(
        Identifier("a", start_pos=0, end_pos=1),
        Identifier("b", start_pos=4, end_pos=5),
        Identifier("c", start_pos=8, end_pos=9),
        start_pos=0,
        end_pos=9,
    )


def test_parse_paren() -> None:
    assert parse_expr("(a)") == Parenthesis(
        Identifier("a", start_pos=1, end_pos=2), start_pos=0, end_pos=3
    )


def test_parse_array() -> None:
    assert parse_expr("[1, 2, 3]") == Array(
        [
            Literal(1, start_pos=1, end_pos=2),
            Literal(2, start_pos=4, end_pos=5),
            Literal(3, start_pos=7, end_pos=8),
        ],
        start_pos=0,
        end_pos=9,
    )
    assert parse_expr("[1, 2, 3, 4]") == Array(
        [
            Literal(1, start_pos=1, end_pos=2),
            Literal(2, start_pos=4, end_pos=5),
            Literal(3, start_pos=7, end_pos=8),
            Literal(4, start_pos=10, end_pos=11),
        ],
        start_pos=0,
        end_pos=12,
    )


def test_parse_array_complex() -> None:
    assert parse_expr("[(for), foo, baz]") == Array(
        [
            Parenthesis(
                Identifier("for", start_pos=2, end_pos=5), start_pos=1, end_pos=6
            ),
            Identifier("foo", start_pos=8, end_pos=11),
            Identifier("baz", start_pos=13, end_pos=16),
        ],
        start_pos=0,
        end_pos=17,
    )
    with pytest.raises(UnexpectedToken):
        parse_expr("[for, foo, baz]")


def test_parse_object() -> None:
    assert parse_expr('{ foo = "bar" }') == Object(
        {
            Identifier("foo", start_pos=2, end_pos=5): Literal(
                "bar", start_pos=8, end_pos=13
            )
        },
        start_pos=0,
        end_pos=15,
    )
    assert parse_expr("{ foo: bar }") == Object(
        {
            Identifier("foo", start_pos=2, end_pos=5): Identifier(
                "bar", start_pos=7, end_pos=10
            )
        },
        start_pos=0,
        end_pos=12,
    )


def test_parse_object_complex() -> None:
    assert parse_expr("{ (foo) = bar }") == Object(
        {
            Parenthesis(
                Identifier("foo", start_pos=3, end_pos=6), start_pos=2, end_pos=7
            ): Identifier("bar", start_pos=10, end_pos=13)
        },
        start_pos=0,
        end_pos=15,
    )
    assert parse_expr('{ foo = "bar", baz = 42 }') == Object(
        {
            Identifier("foo", start_pos=2, end_pos=5): Literal(
                "bar", start_pos=8, end_pos=13
            ),
            Identifier("baz", start_pos=15, end_pos=18): Literal(
                42, start_pos=21, end_pos=23
            ),
        },
        start_pos=0,
        end_pos=25,
    )

    with pytest.raises(UnexpectedToken):
        parse_expr("{ for = 1, baz = 2 }")

    assert parse_expr('{ "for" = 1, baz = 2}') == Object(
        {
            Literal("for", start_pos=2, end_pos=7): Literal(
                1, start_pos=10, end_pos=11
            ),
            Identifier("baz", start_pos=13, end_pos=16): Literal(
                2, start_pos=19, end_pos=20
            ),
        },
        start_pos=0,
        end_pos=21,
    )
    assert parse_expr("{ baz = 2, for = 1}") == Object(
        {
            Identifier("baz", start_pos=2, end_pos=5): Literal(
                2, start_pos=8, end_pos=9
            ),
            Identifier("for", start_pos=11, end_pos=14): Literal(
                1, start_pos=17, end_pos=18
            ),
        },
        start_pos=0,
        end_pos=19,
    )
    assert parse_expr("{ (for) = 1, baz = 2}") == Object(
        {
            Parenthesis(
                Identifier("for", start_pos=3, end_pos=6), start_pos=2, end_pos=7
            ): Literal(1, start_pos=10, end_pos=11),
            Identifier("baz", start_pos=13, end_pos=16): Literal(
                2, start_pos=19, end_pos=20
            ),
        },
        start_pos=0,
        end_pos=21,
    )


def test_parse_function_call() -> None:
    assert parse_expr("foo()") == FunctionCall(
        Identifier("foo", start_pos=0, end_pos=3), [], start_pos=0, end_pos=5
    )
    assert parse_expr("foo(1, 2, 3)") == FunctionCall(
        Identifier("foo", start_pos=0, end_pos=3),
        [
            Literal(1, start_pos=4, end_pos=5),
            Literal(2, start_pos=7, end_pos=8),
            Literal(3, start_pos=10, end_pos=11),
        ],
        start_pos=0,
        end_pos=12,
    )
    assert parse_expr("foo(1, 2, 3...)") == FunctionCall(
        Identifier("foo", start_pos=0, end_pos=3),
        [
            Literal(1, start_pos=4, end_pos=5),
            Literal(2, start_pos=7, end_pos=8),
            Literal(3, start_pos=10, end_pos=11),
        ],
        var_args=True,
        start_pos=0,
        end_pos=15,
    )


def test_parse_get_attr() -> None:
    assert parse_expr("foo.bar") == GetAttr(
        Identifier("foo", start_pos=0, end_pos=3),
        GetAttrKey(Identifier("bar", start_pos=4, end_pos=7), start_pos=3, end_pos=7),
        start_pos=0,
        end_pos=7,
    )


def test_parse_get_index() -> None:
    assert parse_expr("foo[0]") == GetIndex(
        Identifier("foo", start_pos=0, end_pos=3),
        GetIndexKey(Literal(0, start_pos=4, end_pos=5), start_pos=3, end_pos=6),
        start_pos=0,
        end_pos=6,
    )
    assert parse_expr("foo[bar]") == GetIndex(
        Identifier("foo", start_pos=0, end_pos=3),
        GetIndexKey(Identifier("bar", start_pos=4, end_pos=7), start_pos=3, end_pos=8),
        start_pos=0,
        end_pos=8,
    )


def test_parse_get_attr_splat() -> None:
    assert parse_expr("foo.*") == AttrSplat(
        Identifier("foo", start_pos=0, end_pos=3), [], start_pos=0, end_pos=5
    )
    assert parse_expr("foo.*.bar") == AttrSplat(
        Identifier("foo", start_pos=0, end_pos=3),
        [GetAttrKey(Identifier("bar", start_pos=6, end_pos=9), start_pos=5, end_pos=9)],
        start_pos=0,
        end_pos=9,
    )


def test_parse_index_splat() -> None:
    assert parse_expr("foo[*]") == IndexSplat(
        Identifier("foo", start_pos=0, end_pos=3), [], start_pos=0, end_pos=6
    )
    assert parse_expr("foo[*].bar") == IndexSplat(
        Identifier("foo", start_pos=0, end_pos=3),
        [
            GetAttrKey(
                Identifier("bar", start_pos=7, end_pos=10), start_pos=6, end_pos=10
            )
        ],
        start_pos=0,
        end_pos=10,
    )
    assert parse_expr("foo[*][3]") == IndexSplat(
        Identifier("foo", start_pos=0, end_pos=3),
        [GetIndexKey(Literal(3, start_pos=7, end_pos=8), start_pos=6, end_pos=9)],
        start_pos=0,
        end_pos=9,
    )
    assert parse_expr("foo[*].bar[3]") == IndexSplat(
        Identifier("foo", start_pos=0, end_pos=3),
        [
            GetAttrKey(
                Identifier("bar", start_pos=7, end_pos=10), start_pos=6, end_pos=10
            ),
            GetIndexKey(Literal(3, start_pos=11, end_pos=12), start_pos=10, end_pos=13),
        ],
        start_pos=0,
        end_pos=13,
    )


def test_parse_for_tuple_expr() -> None:
    assert parse_expr("[for a in b: a]") == ForTupleExpression(
        key_ident=None,
        value_ident=Identifier("a", start_pos=5, end_pos=6),
        collection=Identifier("b", start_pos=10, end_pos=11),
        value=Identifier("a", start_pos=13, end_pos=14),
        condition=None,
        start_pos=0,
        end_pos=15,
    )
    assert parse_expr("[for a, b in c: a]") == ForTupleExpression(
        key_ident=Identifier("a", start_pos=5, end_pos=6),
        value_ident=Identifier("b", start_pos=8, end_pos=9),
        collection=Identifier("c", start_pos=13, end_pos=14),
        value=Identifier("a", start_pos=16, end_pos=17),
        condition=None,
        start_pos=0,
        end_pos=18,
    )
    assert parse_expr("[for a in b: a if a]") == ForTupleExpression(
        key_ident=None,
        value_ident=Identifier("a", start_pos=5, end_pos=6),
        collection=Identifier("b", start_pos=10, end_pos=11),
        value=Identifier("a", start_pos=13, end_pos=14),
        condition=Identifier("a", start_pos=18, end_pos=19),
        start_pos=0,
        end_pos=20,
    )
    assert parse_expr("[for a, b in c: a if a]") == ForTupleExpression(
        key_ident=Identifier("a", start_pos=5, end_pos=6),
        value_ident=Identifier("b", start_pos=8, end_pos=9),
        collection=Identifier("c", start_pos=13, end_pos=14),
        value=Identifier("a", start_pos=16, end_pos=17),
        condition=Identifier("a", start_pos=21, end_pos=22),
        start_pos=0,
        end_pos=23,
    )


def test_parse_for_object_expr() -> None:
    assert parse_expr("{for a, b in c: a => b}") == ForObjectExpression(
        key_ident=Identifier("a", start_pos=5, end_pos=6),
        value_ident=Identifier("b", start_pos=8, end_pos=9),
        collection=Identifier("c", start_pos=13, end_pos=14),
        key=Identifier("a", start_pos=16, end_pos=17),
        value=Identifier("b", start_pos=21, end_pos=22),
        condition=None,
        grouping_mode=False,
        start_pos=0,
        end_pos=23,
    )

    assert parse_expr("{for a in b: a => a}") == ForObjectExpression(
        key_ident=None,
        value_ident=Identifier("a", start_pos=5, end_pos=6),
        collection=Identifier("b", start_pos=10, end_pos=11),
        key=Identifier("a", start_pos=13, end_pos=14),
        value=Identifier("a", start_pos=18, end_pos=19),
        condition=None,
        grouping_mode=False,
        start_pos=0,
        end_pos=20,
    )

    assert parse_expr("{for a in b: a => a if a}") == ForObjectExpression(
        key_ident=None,
        value_ident=Identifier("a", start_pos=5, end_pos=6),
        collection=Identifier("b", start_pos=10, end_pos=11),
        key=Identifier("a", start_pos=13, end_pos=14),
        value=Identifier("a", start_pos=18, end_pos=19),
        condition=Identifier("a", start_pos=23, end_pos=24),
        grouping_mode=False,
        start_pos=0,
        end_pos=25,
    )

    assert parse_expr("{for i, v in array : v => i...}") == ForObjectExpression(
        key_ident=Identifier("i", start_pos=5, end_pos=6),
        value_ident=Identifier("v", start_pos=8, end_pos=9),
        collection=Identifier("array", start_pos=13, end_pos=18),
        key=Identifier("v", start_pos=21, end_pos=22),
        value=Identifier("i", start_pos=26, end_pos=27),
        condition=None,
        grouping_mode=True,
        start_pos=0,
        end_pos=31,
    )

    assert parse_expr("{for i, v in array : v => i... if i}") == ForObjectExpression(
        key_ident=Identifier("i", start_pos=5, end_pos=6),
        value_ident=Identifier("v", start_pos=8, end_pos=9),
        collection=Identifier("array", start_pos=13, end_pos=18),
        key=Identifier("v", start_pos=21, end_pos=22),
        value=Identifier("i", start_pos=26, end_pos=27),
        condition=Identifier("i", start_pos=34, end_pos=35),
        grouping_mode=True,
        start_pos=0,
        end_pos=36,
    )


def test_parse_attribute() -> None:
    assert parse_expr_or_attribute("a = b") == Attribute(
        Identifier("a", start_pos=0, end_pos=1),
        Identifier("b", start_pos=4, end_pos=5),
        start_pos=0,
        end_pos=5,
    )


def test_parse_block() -> None:
    assert parse_module("locals {\na = b\n}") == Module(
        [
            Block(
                Identifier("locals", start_pos=0, end_pos=6),
                [],
                [
                    Attribute(
                        Identifier("a", start_pos=9, end_pos=10),
                        Identifier("b", start_pos=13, end_pos=14),
                        start_pos=9,
                        end_pos=14,
                    )
                ],
                start_pos=0,
                end_pos=16,
            ),
        ],
        start_pos=0,
        end_pos=16,
    )

    assert parse_module("""resource "a" {\na = b\n}""") == Module(
        [
            Block(
                Identifier("resource", start_pos=0, end_pos=8),
                [Literal("a", start_pos=9, end_pos=12)],
                [
                    Attribute(
                        Identifier("a", start_pos=15, end_pos=16),
                        Identifier("b", start_pos=19, end_pos=20),
                        start_pos=15,
                        end_pos=20,
                    )
                ],
                start_pos=0,
                end_pos=22,
            )
        ],
        start_pos=0,
        end_pos=22,
    )

    assert parse_module("""resource a "b" {\na = b\n}""") == Module(
        [
            Block(
                Identifier("resource", start_pos=0, end_pos=8),
                [
                    Identifier("a", start_pos=9, end_pos=10),
                    Literal("b", start_pos=11, end_pos=14),
                ],
                [
                    Attribute(
                        Identifier("a", start_pos=17, end_pos=18),
                        Identifier("b", start_pos=21, end_pos=22),
                        start_pos=17,
                        end_pos=22,
                    )
                ],
                start_pos=0,
                end_pos=24,
            )
        ],
        start_pos=0,
        end_pos=24,
    )

    assert parse_module("""locals {\na = 1\nb = 2\n}""") == Module(
        [
            Block(
                Identifier("locals", start_pos=0, end_pos=6),
                [],
                [
                    Attribute(
                        Identifier("a", start_pos=9, end_pos=10),
                        Literal(1, start_pos=13, end_pos=14),
                        start_pos=9,
                        end_pos=14,
                    ),
                    Attribute(
                        Identifier("b", start_pos=15, end_pos=16),
                        Literal(2, start_pos=19, end_pos=20),
                        start_pos=15,
                        end_pos=20,
                    ),
                ],
                start_pos=0,
                end_pos=22,
            )
        ],
        start_pos=0,
        end_pos=22,
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
        start_pos=0,
        end_pos=100,
        body=[
            Block(
                start_pos=0,
                end_pos=29,
                type=Identifier(start_pos=0, end_pos=6, name="block1"),
                labels=[],
                body=[
                    Attribute(
                        start_pos=13,
                        end_pos=26,
                        key=Identifier(start_pos=13, end_pos=18, name="value"),
                        value=Literal(start_pos=21, end_pos=26, value="foo"),
                    )
                ],
            ),
            Block(
                start_pos=29,
                end_pos=60,
                type=Identifier(start_pos=29, end_pos=35, name="block2"),
                labels=[Identifier(start_pos=36, end_pos=40, name="arg1")],
                body=[
                    Attribute(
                        start_pos=47,
                        end_pos=57,
                        key=Identifier(start_pos=47, end_pos=52, name="value"),
                        value=Literal(start_pos=55, end_pos=57, value=42),
                    )
                ],
            ),
            Block(
                start_pos=60,
                end_pos=100,
                type=Identifier(start_pos=60, end_pos=66, name="block3"),
                labels=[
                    Literal(start_pos=67, end_pos=73, value="arg2"),
                    Identifier(start_pos=74, end_pos=78, name="arg3"),
                ],
                body=[
                    Attribute(
                        start_pos=85,
                        end_pos=98,
                        key=Identifier(start_pos=85, end_pos=90, name="value"),
                        value=FunctionCall(
                            start_pos=93,
                            end_pos=98,
                            ident=Identifier(start_pos=93, end_pos=96, name="bar"),
                            args=[],
                            var_args=False,
                        ),
                    )
                ],
            ),
        ],
    )
