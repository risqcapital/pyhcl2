import textwrap

import pytest
from pyagnostics.exceptions import DiagnosticError

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
    parse_module_with_source,
)
from tests.helpers import (
    parse_expr_or_stmt_with_id,
    parse_expr_with_id,
    parse_module_with_id,
    span,
)
from pyhcl2.values import Boolean, Float, Integer, Null, String

def test_parse_literal_null() -> None:
    assert parse_expr_with_id("null") == Literal(Null(), span=span(0, 4))


def test_parse_literal_string() -> None:
    assert parse_expr_with_id('"Hello World"') == Literal(
        String("Hello World"), span=span(0, 13)
    )


def test_parse_literal_heredoc() -> None:
    expr = parse_expr_with_id("<<EOF\nhello\nEOF")
    assert isinstance(expr, Literal)
    assert expr.value.raw() == "hello"


def test_parse_literal_bool() -> None:
    assert parse_expr_with_id("true") == Literal(Boolean(True), span=span(0, 4))
    assert parse_expr_with_id("false") == Literal(Boolean(False), span=span(0, 5))


def test_parse_literal_number() -> None:
    assert parse_expr_with_id("42") == Literal(Integer(42), span=span(0, 2))
    assert parse_expr_with_id("42.0") == Literal(Float(42.0), span=span(0, 4))
    assert parse_expr_with_id("42.42") == Literal(Float(42.42), span=span(0, 5))


def test_parse_module_with_source_returns_module() -> None:
    parsed = parse_module_with_source("a = 1", name="example.hcl")
    assert isinstance(parsed.module, Module)


def test_parse_module_with_source_attaches_source_on_error() -> None:
    with pytest.raises(DiagnosticError) as excinfo:
        parse_module_with_source("{", name="broken.hcl")

    diag = excinfo.value
    assert diag.labels
    source_id = diag.labels[0].span.source_id
    resolved = diag.get_source(source_id)
    assert resolved is not None
    source_code, _highlighter = resolved
    assert source_code.name == "broken.hcl"


def test_parse_identifier() -> None:
    assert parse_expr_with_id("foo") == Identifier("foo", span=span(0, 3))
    assert parse_expr_with_id("bar") == Identifier("bar", span=span(0, 3))


def test_parse_unary_expr() -> None:
    assert parse_expr_with_id("-a") == UnaryExpression(
        UnaryOperator("-", span=span(0, 1)),
        Identifier("a", span=span(1, 2)),
        span=span(0, 2),
    )
    assert parse_expr_with_id("!a") == UnaryExpression(
        UnaryOperator("!", span=span(0, 1)),
        Identifier("a", span=span(1, 2)),
        span=span(0, 2),
    )


def test_parse_binary_expr() -> None:
    assert parse_expr_with_id("a == b") == BinaryExpression(
        BinaryOperator("==", span=span(2, 4)),
        Identifier("a", span=span(0, 1)),
        Identifier("b", span=span(5, 6)),
        span=span(0, 6),
    )
    assert parse_expr_with_id("a != b") == BinaryExpression(
        BinaryOperator("!=", span=span(2, 4)),
        Identifier("a", span=span(0, 1)),
        Identifier("b", span=span(5, 6)),
        span=span(0, 6),
    )
    assert parse_expr_with_id("a < b") == BinaryExpression(
        BinaryOperator("<", span=span(2, 3)),
        Identifier("a", span=span(0, 1)),
        Identifier("b", span=span(4, 5)),
        span=span(0, 5),
    )
    assert parse_expr_with_id("a > b") == BinaryExpression(
        BinaryOperator(">", span=span(2, 3)),
        Identifier("a", span=span(0, 1)),
        Identifier("b", span=span(4, 5)),
        span=span(0, 5),
    )
    assert parse_expr_with_id("a <= b") == BinaryExpression(
        BinaryOperator("<=", span=span(2, 4)),
        Identifier("a", span=span(0, 1)),
        Identifier("b", span=span(5, 6)),
        span=span(0, 6),
    )
    assert parse_expr_with_id("a >= b") == BinaryExpression(
        BinaryOperator(">=", span=span(2, 4)),
        Identifier("a", span=span(0, 1)),
        Identifier("b", span=span(5, 6)),
        span=span(0, 6),
    )
    assert parse_expr_with_id("a - b") == BinaryExpression(
        BinaryOperator("-", span=span(2, 3)),
        Identifier("a", span=span(0, 1)),
        Identifier("b", span=span(4, 5)),
        span=span(0, 5),
    )
    assert parse_expr_with_id("a * b") == BinaryExpression(
        BinaryOperator("*", span=span(2, 3)),
        Identifier("a", span=span(0, 1)),
        Identifier("b", span=span(4, 5)),
        span=span(0, 5),
    )
    assert parse_expr_with_id("a / b") == BinaryExpression(
        BinaryOperator("/", span=span(2, 3)),
        Identifier("a", span=span(0, 1)),
        Identifier("b", span=span(4, 5)),
        span=span(0, 5),
    )
    assert parse_expr_with_id("a % b") == BinaryExpression(
        BinaryOperator("%", span=span(2, 3)),
        Identifier("a", span=span(0, 1)),
        Identifier("b", span=span(4, 5)),
        span=span(0, 5),
    )
    assert parse_expr_with_id("a && b") == BinaryExpression(
        BinaryOperator("&&", span=span(2, 4)),
        Identifier("a", span=span(0, 1)),
        Identifier("b", span=span(5, 6)),
        span=span(0, 6),
    )
    assert parse_expr_with_id("a || b") == BinaryExpression(
        BinaryOperator("||", span=span(2, 4)),
        Identifier("a", span=span(0, 1)),
        Identifier("b", span=span(5, 6)),
        span=span(0, 6),
    )
    assert parse_expr_with_id("a + b") == BinaryExpression(
        BinaryOperator("+", span=span(2, 3)),
        Identifier("a", span=span(0, 1)),
        Identifier("b", span=span(4, 5)),
        span=span(0, 5),
    )


def test_parse_binary_precedence() -> None:
    assert parse_expr_with_id("a + b * c") == BinaryExpression(
        BinaryOperator("+", span=span(2, 3)),
        Identifier("a", span=span(0, 1)),
        BinaryExpression(
            BinaryOperator("*", span=span(6, 7)),
            Identifier("b", span=span(4, 5)),
            Identifier("c", span=span(8, 9)),
            span=span(4, 9),
        ),
        span=span(0, 9),
    )
    assert parse_expr_with_id("a * b + c") == BinaryExpression(
        BinaryOperator("+", span=span(6, 7)),
        BinaryExpression(
            BinaryOperator("*", span=span(2, 3)),
            Identifier("a", span=span(0, 1)),
            Identifier("b", span=span(4, 5)),
            span=span(0, 5),
        ),
        Identifier("c", span=span(8, 9)),
        span=span(0, 9),
    )
    assert parse_expr_with_id("a < b + c") == BinaryExpression(
        BinaryOperator("<", span=span(2, 3)),
        Identifier("a", span=span(0, 1)),
        BinaryExpression(
            BinaryOperator("+", span=span(6, 7)),
            Identifier("b", span=span(4, 5)),
            Identifier("c", span=span(8, 9)),
            span=span(4, 9),
        ),
        span=span(0, 9),
    )
    assert parse_expr_with_id("a + b < c") == BinaryExpression(
        BinaryOperator("<", span=span(6, 7)),
        BinaryExpression(
            BinaryOperator("+", span=span(2, 3)),
            Identifier("a", span=span(0, 1)),
            Identifier("b", span=span(4, 5)),
            span=span(0, 5),
        ),
        Identifier("c", span=span(8, 9)),
        span=span(0, 9),
    )
    assert parse_expr_with_id("a == b >= c") == BinaryExpression(
        BinaryOperator("==", span=span(2, 4)),
        Identifier("a", span=span(0, 1)),
        BinaryExpression(
            BinaryOperator(">=", span=span(7, 9)),
            Identifier("b", span=span(5, 6)),
            Identifier("c", span=span(10, 11)),
            span=span(5, 11),
        ),
        span=span(0, 11),
    )
    assert parse_expr_with_id("a >= b == c") == BinaryExpression(
        BinaryOperator("==", span=span(7, 9)),
        BinaryExpression(
            BinaryOperator(">=", span=span(2, 4)),
            Identifier("a", span=span(0, 1)),
            Identifier("b", span=span(5, 6)),
            span=span(0, 6),
        ),
        Identifier("c", span=span(10, 11)),
        span=span(0, 11),
    )
    assert parse_expr_with_id("a == b && c") == BinaryExpression(
        BinaryOperator("&&", span=span(7, 9)),
        BinaryExpression(
            BinaryOperator("==", span=span(2, 4)),
            Identifier("a", span=span(0, 1)),
            Identifier("b", span=span(5, 6)),
            span=span(0, 6),
        ),
        Identifier("c", span=span(10, 11)),
        span=span(0, 11),
    )
    assert parse_expr_with_id("a && b == c") == BinaryExpression(
        BinaryOperator("&&", span=span(2, 4)),
        Identifier("a", span=span(0, 1)),
        BinaryExpression(
            BinaryOperator("==", span=span(7, 9)),
            Identifier("b", span=span(5, 6)),
            Identifier("c", span=span(10, 11)),
            span=span(5, 11),
        ),
        span=span(0, 11),
    )
    assert parse_expr_with_id("a || b && c") == BinaryExpression(
        BinaryOperator("||", span=span(2, 4)),
        Identifier("a", span=span(0, 1)),
        BinaryExpression(
            BinaryOperator("&&", span=span(7, 9)),
            Identifier("b", span=span(5, 6)),
            Identifier("c", span=span(10, 11)),
            span=span(5, 11),
        ),
        span=span(0, 11),
    )
    assert parse_expr_with_id("a && b || c") == BinaryExpression(
        BinaryOperator("||", span=span(7, 9)),
        BinaryExpression(
            BinaryOperator("&&", span=span(2, 4)),
            Identifier("a", span=span(0, 1)),
            Identifier("b", span=span(5, 6)),
            span=span(0, 6),
        ),
        Identifier("c", span=span(10, 11)),
        span=span(0, 11),
    )


def test_parse_conditional() -> None:
    assert parse_expr_with_id("a ? b : c") == Conditional(
        Identifier("a", span=span(0, 1)),
        Identifier("b", span=span(4, 5)),
        Identifier("c", span=span(8, 9)),
        span=span(0, 9),
    )


def test_parse_paren() -> None:
    assert parse_expr_with_id("(a)") == Parenthesis(
        Identifier("a", span=span(1, 2)), span=span(0, 3)
    )


def test_parse_array() -> None:
    assert parse_expr_with_id("[1, 2, 3]") == ArrayExpression(
        [
            Literal(Integer(1), span=span(1, 2)),
            Literal(Integer(2), span=span(4, 5)),
            Literal(Integer(3), span=span(7, 8)),
        ],
        span=span(0, 9),
    )
    assert parse_expr_with_id("[1, 2, 3, 4]") == ArrayExpression(
        [
            Literal(Integer(1), span=span(1, 2)),
            Literal(Integer(2), span=span(4, 5)),
            Literal(Integer(3), span=span(7, 8)),
            Literal(Integer(4), span=span(10, 11)),
        ],
        span=span(0, 12),
    )


def test_parse_array_complex() -> None:
    assert parse_expr_with_id("[(for), foo, baz]") == ArrayExpression(
        [
            Parenthesis(Identifier("for", span=span(2, 5)), span=span(1, 6)),
            Identifier("foo", span=span(8, 11)),
            Identifier("baz", span=span(13, 16)),
        ],
        span=span(0, 17),
    )
    with pytest.raises(DiagnosticError):
        parse_expr_with_id("[for, foo, baz]")


def test_parse_object() -> None:
    assert parse_expr_with_id('{ foo = "bar" }') == ObjectExpression(
        {Identifier("foo", span=span(2, 5)): Literal(String("bar"), span=span(8, 13))},
        span=span(0, 15),
    )
    assert parse_expr_with_id("{ foo: bar }") == ObjectExpression(
        {Identifier("foo", span=span(2, 5)): Identifier("bar", span=span(7, 10))},
        span=span(0, 12),
    )


def test_parse_object_complex() -> None:
    assert parse_expr_with_id("{ (foo) = bar }") == ObjectExpression(
        {
            Parenthesis(
                Identifier("foo", span=span(3, 6)), span=span(2, 7)
            ): Identifier("bar", span=span(10, 13))
        },
        span=span(0, 15),
    )
    assert parse_expr_with_id('{ foo = "bar", baz = 42 }') == ObjectExpression(
        {
            Identifier("foo", span=span(2, 5)): Literal(
                String("bar"), span=span(8, 13)
            ),
            Identifier("baz", span=span(15, 18)): Literal(
                Integer(42), span=span(21, 23)
            ),
        },
        span=span(0, 25),
    )

    with pytest.raises(DiagnosticError):
        parse_expr_with_id("{ for = 1, baz = 2 }")

    assert parse_expr_with_id('{ "for" = 1, baz = 2}') == ObjectExpression(
        {
            Literal(String("for"), span=span(2, 7)): Literal(
                Integer(1), span=span(10, 11)
            ),
            Identifier("baz", span=span(13, 16)): Literal(
                Integer(2), span=span(19, 20)
            ),
        },
        span=span(0, 21),
    )
    assert parse_expr_with_id("{ baz = 2, for = 1}") == ObjectExpression(
        {
            Identifier("baz", span=span(2, 5)): Literal(Integer(2), span=span(8, 9)),
            Identifier("for", span=span(11, 14)): Literal(
                Integer(1), span=span(17, 18)
            ),
        },
        span=span(0, 19),
    )
    assert parse_expr_with_id("{ (for) = 1, baz = 2}") == ObjectExpression(
        {
            Parenthesis(Identifier("for", span=span(3, 6)), span=span(2, 7)): Literal(
                Integer(1), span=span(10, 11)
            ),
            Identifier("baz", span=span(13, 16)): Literal(
                Integer(2), span=span(19, 20)
            ),
        },
        span=span(0, 21),
    )


def test_parse_function_call() -> None:
    assert parse_expr_with_id("foo()") == FunctionCall(
        Identifier("foo", span=span(0, 3)), [], span=span(0, 5)
    )
    assert parse_expr_with_id("foo(1, 2, 3)") == FunctionCall(
        Identifier("foo", span=span(0, 3)),
        [
            Literal(Integer(1), span=span(4, 5)),
            Literal(Integer(2), span=span(7, 8)),
            Literal(Integer(3), span=span(10, 11)),
        ],
        span=span(0, 12),
    )
    assert parse_expr_with_id("foo(1, 2, 3...)") == FunctionCall(
        Identifier("foo", span=span(0, 3)),
        [
            Literal(Integer(1), span=span(4, 5)),
            Literal(Integer(2), span=span(7, 8)),
            Literal(Integer(3), span=span(10, 11)),
        ],
        var_args=True,
        span=span(0, 15),
    )


def test_parse_get_attr() -> None:
    assert parse_expr_with_id("foo.bar") == GetAttr(
        Identifier("foo", span=span(0, 3)),
        GetAttrKey(Identifier("bar", span=span(4, 7)), span=span(3, 7)),
        span=span(0, 7),
    )


def test_parse_get_index() -> None:
    assert parse_expr_with_id("foo[0]") == GetIndex(
        Identifier("foo", span=span(0, 3)),
        GetIndexKey(Literal(Integer(0), span=span(4, 5)), span=span(3, 6)),
        span=span(0, 6),
    )
    assert parse_expr_with_id("foo[bar]") == GetIndex(
        Identifier("foo", span=span(0, 3)),
        GetIndexKey(Identifier("bar", span=span(4, 7)), span=span(3, 8)),
        span=span(0, 8),
    )


def test_parse_get_attr_splat() -> None:
    assert parse_expr_with_id("foo.*") == AttrSplat(
        Identifier("foo", span=span(0, 3)), [], span=span(0, 5)
    )
    assert parse_expr_with_id("foo.*.bar") == AttrSplat(
        Identifier("foo", span=span(0, 3)),
        [GetAttrKey(Identifier("bar", span=span(6, 9)), span=span(5, 9))],
        span=span(0, 9),
    )


def test_parse_index_splat() -> None:
    assert parse_expr_with_id("foo[*]") == IndexSplat(
        Identifier("foo", span=span(0, 3)), [], span=span(0, 6)
    )
    assert parse_expr_with_id("foo[*].bar") == IndexSplat(
        Identifier("foo", span=span(0, 3)),
        [GetAttrKey(Identifier("bar", span=span(7, 10)), span=span(6, 10))],
        span=span(0, 10),
    )
    assert parse_expr_with_id("foo[*][3]") == IndexSplat(
        Identifier("foo", span=span(0, 3)),
        [GetIndexKey(Literal(Integer(3), span=span(7, 8)), span=span(6, 9))],
        span=span(0, 9),
    )
    assert parse_expr_with_id("foo[*].bar[3]") == IndexSplat(
        Identifier("foo", span=span(0, 3)),
        [
            GetAttrKey(Identifier("bar", span=span(7, 10)), span=span(6, 10)),
            GetIndexKey(Literal(Integer(3), span=span(11, 12)), span=span(10, 13)),
        ],
        span=span(0, 13),
    )


def test_parse_for_tuple_expr() -> None:
    assert parse_expr_with_id("[for a in b: a]") == ForTupleExpression(
        key_ident=None,
        value_ident=Identifier("a", span=span(5, 6)),
        collection=Identifier("b", span=span(10, 11)),
        value=Identifier("a", span=span(13, 14)),
        condition=None,
        span=span(0, 15),
    )
    assert parse_expr_with_id("[for a, b in c: a]") == ForTupleExpression(
        key_ident=Identifier("a", span=span(5, 6)),
        value_ident=Identifier("b", span=span(8, 9)),
        collection=Identifier("c", span=span(13, 14)),
        value=Identifier("a", span=span(16, 17)),
        condition=None,
        span=span(0, 18),
    )
    assert parse_expr_with_id("[for a in b: a if a]") == ForTupleExpression(
        key_ident=None,
        value_ident=Identifier("a", span=span(5, 6)),
        collection=Identifier("b", span=span(10, 11)),
        value=Identifier("a", span=span(13, 14)),
        condition=Identifier("a", span=span(18, 19)),
        span=span(0, 20),
    )
    assert parse_expr_with_id("[for a, b in c: a if a]") == ForTupleExpression(
        key_ident=Identifier("a", span=span(5, 6)),
        value_ident=Identifier("b", span=span(8, 9)),
        collection=Identifier("c", span=span(13, 14)),
        value=Identifier("a", span=span(16, 17)),
        condition=Identifier("a", span=span(21, 22)),
        span=span(0, 23),
    )


def test_parse_for_object_expr() -> None:
    assert parse_expr_with_id("{for a, b in c: a => b}") == ForObjectExpression(
        key_ident=Identifier("a", span=span(5, 6)),
        value_ident=Identifier("b", span=span(8, 9)),
        collection=Identifier("c", span=span(13, 14)),
        key=Identifier("a", span=span(16, 17)),
        value=Identifier("b", span=span(21, 22)),
        condition=None,
        grouping_mode=False,
        span=span(0, 23),
    )

    assert parse_expr_with_id("{for a in b: a => a}") == ForObjectExpression(
        key_ident=None,
        value_ident=Identifier("a", span=span(5, 6)),
        collection=Identifier("b", span=span(10, 11)),
        key=Identifier("a", span=span(13, 14)),
        value=Identifier("a", span=span(18, 19)),
        condition=None,
        grouping_mode=False,
        span=span(0, 20),
    )

    assert parse_expr_with_id("{for a in b: a => a if a}") == ForObjectExpression(
        key_ident=None,
        value_ident=Identifier("a", span=span(5, 6)),
        collection=Identifier("b", span=span(10, 11)),
        key=Identifier("a", span=span(13, 14)),
        value=Identifier("a", span=span(18, 19)),
        condition=Identifier("a", span=span(23, 24)),
        grouping_mode=False,
        span=span(0, 25),
    )

    assert parse_expr_with_id("{for i, v in array : v => i...}") == ForObjectExpression(
        key_ident=Identifier("i", span=span(5, 6)),
        value_ident=Identifier("v", span=span(8, 9)),
        collection=Identifier("array", span=span(13, 18)),
        key=Identifier("v", span=span(21, 22)),
        value=Identifier("i", span=span(26, 27)),
        condition=None,
        grouping_mode=True,
        span=span(0, 31),
    )

    assert parse_expr_with_id(
        "{for i, v in array : v => i... if i}"
    ) == ForObjectExpression(
        key_ident=Identifier("i", span=span(5, 6)),
        value_ident=Identifier("v", span=span(8, 9)),
        collection=Identifier("array", span=span(13, 18)),
        key=Identifier("v", span=span(21, 22)),
        value=Identifier("i", span=span(26, 27)),
        condition=Identifier("i", span=span(34, 35)),
        grouping_mode=True,
        span=span(0, 36),
    )


def test_parse_attribute() -> None:
    assert parse_expr_or_stmt_with_id("a = b") == Attribute(
        Identifier("a", span=span(0, 1)),
        Identifier("b", span=span(4, 5)),
        span=span(0, 5),
    )


def test_parse_block() -> None:
    assert parse_module_with_id("locals {\na = b\n}") == Module(
        [
            Block(
                Identifier("locals", span=span(0, 6)),
                [],
                [
                    Attribute(
                        Identifier("a", span=span(9, 10)),
                        Identifier("b", span=span(13, 14)),
                        span=span(9, 14),
                    )
                ],
                span=span(0, 16),
            ),
        ],
        span=span(0, 16),
    )

    assert parse_module_with_id("""resource "a" {\na = b\n}""") == Module(
        [
            Block(
                Identifier("resource", span=span(0, 8)),
                [Literal(String("a"), span=span(9, 12))],
                [
                    Attribute(
                        Identifier("a", span=span(15, 16)),
                        Identifier("b", span=span(19, 20)),
                        span=span(15, 20),
                    )
                ],
                span=span(0, 22),
            )
        ],
        span=span(0, 22),
    )

    assert parse_module_with_id("""resource a "b" {\na = b\n}""") == Module(
        [
            Block(
                Identifier("resource", span=span(0, 8)),
                [
                    Identifier("a", span=span(9, 10)),
                    Literal(String("b"), span=span(11, 14)),
                ],
                [
                    Attribute(
                        Identifier("a", span=span(17, 18)),
                        Identifier("b", span=span(21, 22)),
                        span=span(17, 22),
                    )
                ],
                span=span(0, 24),
            )
        ],
        span=span(0, 24),
    )

    assert parse_module_with_id("""locals {\na = 1\nb = 2\n}""") == Module(
        [
            Block(
                Identifier("locals", span=span(0, 6)),
                [],
                [
                    Attribute(
                        Identifier("a", span=span(9, 10)),
                        Literal(Integer(1), span=span(13, 14)),
                        span=span(9, 14),
                    ),
                    Attribute(
                        Identifier("b", span=span(15, 16)),
                        Literal(Integer(2), span=span(19, 20)),
                        span=span(15, 20),
                    ),
                ],
                span=span(0, 22),
            )
        ],
        span=span(0, 22),
    )


def test_parse_multiple_blocks() -> None:
    assert parse_module_with_id(
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
        span=span(0, 100),
        body=[
            Block(
                span=span(0, 29),
                type=Identifier(span=span(0, 6), name="block1"),
                labels=[],
                body=[
                    Attribute(
                        span=span(13, 26),
                        key=Identifier(span=span(13, 18), name="value"),
                        value=Literal(span=span(21, 26), value=String("foo")),
                    )
                ],
            ),
            Block(
                span=span(29, 60),
                type=Identifier(span=span(29, 35), name="block2"),
                labels=[Identifier(span=span(36, 40), name="arg1")],
                body=[
                    Attribute(
                        span=span(47, 57),
                        key=Identifier(span=span(47, 52), name="value"),
                        value=Literal(span=span(55, 57), value=Integer(42)),
                    )
                ],
            ),
            Block(
                span=span(60, 100),
                type=Identifier(span=span(60, 66), name="block3"),
                labels=[
                    Literal(span=span(67, 73), value=String("arg2")),
                    Identifier(span=span(74, 78), name="arg3"),
                ],
                body=[
                    Attribute(
                        span=span(85, 98),
                        key=Identifier(span=span(85, 90), name="value"),
                        value=FunctionCall(
                            span=span(93, 98),
                            ident=Identifier(span=span(93, 96), name="bar"),
                            args=[],
                            var_args=False,
                        ),
                    )
                ],
            ),
        ],
    )
