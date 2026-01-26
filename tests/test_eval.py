from __future__ import annotations

import pytest
from pyagnostics.exceptions import DiagnosticError
from pyagnostics.spans import SourceSpan

from pyhcl2.eval import EvaluationScope, Evaluator
from pyhcl2.nodes import Attribute, Block, Expression, Identifier
from pyhcl2.values import Integer, Unknown, Value, VariableReference
from tests.helpers import parse_expr_or_stmt_with_id, parse_expr_with_id, span


def ident(name: str) -> Identifier:
    return Identifier(name, span=span(0, len(name)))


def attr(key: Identifier, value: Expression) -> Attribute:
    return Attribute(key, value, span=SourceSpan.enclose(key.span, value.span))


def block(type_: Identifier, labels: list, body: list) -> Block:
    if body:
        end_span = body[-1].span
    elif labels:
        end_span = labels[-1].span
    else:
        end_span = type_.span
    return Block(type_, labels, body, span=SourceSpan.enclose(type_.span, end_span))


def eval_hcl(expr: str, **kwargs: object) -> object:
    return (
        Evaluator()
        .eval(
            parse_expr_with_id(expr),
            EvaluationScope(variables={k: Value.infer(v) for k, v in kwargs.items()}),
        )
        .raw()
    )


def eval_unknown(expr: str) -> Unknown:
    value = Evaluator().eval(parse_expr_with_id(expr))
    assert isinstance(value, Unknown)
    return value


def ref_keys(refs: set[VariableReference]) -> set[tuple[str | None, ...]]:
    return {ref.key for ref in refs}


def eval_value(expr: str) -> Value:
    return Evaluator().eval(parse_expr_with_id(expr))


def eval_stmt_value(stmt: str) -> Value:
    return Evaluator().eval(parse_expr_or_stmt_with_id(stmt))


def resolve_unknown(value: Value) -> Unknown:
    resolved = value.resolve()
    assert isinstance(resolved, Unknown)
    return resolved


def assert_unknown_refs(
    unknown: Unknown,
    *,
    direct: set[tuple[str | None, ...]],
    indirect: set[tuple[str | None, ...]],
) -> None:
    assert ref_keys(unknown.direct_references) == direct
    assert ref_keys(unknown.indirect_references) == indirect


def test_eval_literal_null() -> None:
    assert eval_hcl("null") is None


def test_eval_literal_string() -> None:
    assert eval_hcl('"Hello World"') == "Hello World"


def test_eval_literal_bool() -> None:
    assert eval_hcl("true") is True
    assert eval_hcl("false") is False


def test_eval_literal_number() -> None:
    assert eval_hcl("42") == 42
    assert eval_hcl("42.0") == 42.0
    assert eval_hcl("42.42") == 42.42


def test_eval_identifier() -> None:
    with pytest.raises(DiagnosticError):
        eval_hcl("foo")

    assert eval_hcl("foo", foo=42) == 42
    assert eval_hcl("foo == true", foo=True) is True


def test_eval_identifier_parent_scope() -> None:
    assert (
        Evaluator()
        .eval(
            parse_expr_with_id("foo"),
            EvaluationScope(parent=EvaluationScope(variables={"foo": Integer(42)})),
        )
        .raw()
        == 42
    )


def test_unknown_direct_identifier() -> None:
    unknown = eval_unknown("foo")
    assert_unknown_refs(unknown, direct={("foo",)}, indirect=set())


def test_unknown_direct_attribute() -> None:
    unknown = eval_unknown("foo.bar")
    assert_unknown_refs(unknown, direct={("foo", "bar")}, indirect={("foo",)})


def test_unknown_direct_index_string() -> None:
    unknown = eval_unknown('foo["bar"]')
    assert_unknown_refs(unknown, direct={("foo", "bar")}, indirect={("foo",)})


def test_unknown_direct_parenthesis() -> None:
    unknown = eval_unknown("(foo)")
    assert_unknown_refs(unknown, direct={("foo",)}, indirect=set())


def test_unknown_attribute_statement() -> None:
    unknown = eval_stmt_value("a = foo")
    assert isinstance(unknown, Unknown)
    assert_unknown_refs(unknown, direct={("foo",)}, indirect=set())


def test_unknown_indirect_binary() -> None:
    unknown = eval_unknown("foo + 1")
    assert_unknown_refs(unknown, direct=set(), indirect={("foo",)})


def test_unknown_indirect_conditional() -> None:
    unknown = eval_unknown("cond ? 1 : 2")
    assert_unknown_refs(unknown, direct=set(), indirect={("cond",)})


def test_unknown_indirect_multiple_sources() -> None:
    unknown = eval_unknown("foo.bar + baz")
    assert_unknown_refs(
        unknown,
        direct=set(),
        indirect={("foo",), ("foo", "bar"), ("baz",)},
    )


def test_unknown_indirect_object_key() -> None:
    unknown = eval_unknown("{ (foo) = 1 }")
    assert_unknown_refs(unknown, direct=set(), indirect={("foo",)})


def test_unknown_array_resolve() -> None:
    value = eval_value("[foo]")
    unknown = resolve_unknown(value)
    assert_unknown_refs(unknown, direct=set(), indirect={("foo",)})


def test_unknown_object_value_resolve() -> None:
    value = eval_value("{ a = foo }")
    unknown = resolve_unknown(value)
    assert_unknown_refs(unknown, direct=set(), indirect={("foo",)})


def test_unknown_index_integer() -> None:
    unknown = eval_unknown("foo[0]")
    assert_unknown_refs(unknown, direct=set(), indirect={("foo",)})


def test_unknown_function_call() -> None:
    evaluator = Evaluator(intrinsic_functions={"id": lambda x: x})
    value = evaluator.eval(parse_expr_with_id("id(foo)"))
    assert isinstance(value, Unknown)
    assert_unknown_refs(value, direct=set(), indirect={("foo",)})


def test_unknown_for_tuple_expression() -> None:
    value = eval_value("[for a in foo: a]")
    unknown = resolve_unknown(value)
    assert_unknown_refs(unknown, direct=set(), indirect={("foo",)})


def test_unknown_for_object_expression() -> None:
    value = eval_value("{ for a in foo: a => a }")
    unknown = resolve_unknown(value)
    assert_unknown_refs(unknown, direct=set(), indirect={("foo",)})


def test_unknown_attr_splat() -> None:
    unknown = eval_unknown("foo.*.bar")
    assert_unknown_refs(
        unknown,
        direct=set(),
        indirect={("foo",), ("foo", "bar")},
    )


def test_unknown_index_splat() -> None:
    unknown = eval_unknown("foo[*].bar")
    assert_unknown_refs(
        unknown,
        direct=set(),
        indirect={("foo",), ("foo", "bar")},
    )


def test_eval_unary_expr() -> None:
    assert eval_hcl("-42") == -42
    assert eval_hcl("!true") is False
    assert eval_hcl("!false") is True


def test_eval_binary_expr() -> None:
    assert eval_hcl("1 == 1") is True
    assert eval_hcl("1 == 2") is False
    assert eval_hcl("1 != 2") is True
    assert eval_hcl("1 != 1") is False
    assert eval_hcl("1 < 2") is True
    assert eval_hcl("2 < 1") is False
    assert eval_hcl("2 > 1") is True
    assert eval_hcl("1 > 2") is False
    assert eval_hcl("1 <= 1") is True
    assert eval_hcl("1 <= 2") is True
    assert eval_hcl("1 >= 1") is True
    assert eval_hcl("2 >= 1") is True
    assert eval_hcl("5 - 3") == 2
    assert eval_hcl("3 + 5") == 8
    assert eval_hcl("2 * 3") == 6
    assert eval_hcl("6 / 3") == 2
    assert eval_hcl("5 % 3") == 2
    assert eval_hcl("true && true") is True
    assert eval_hcl("true && false") is False
    assert eval_hcl("false && true") is False
    assert eval_hcl("false && false") is False
    assert eval_hcl("true || true") is True
    assert eval_hcl("true || false") is True
    assert eval_hcl("false || true") is True
    assert eval_hcl("false || false") is False


def test_eval_binary_precedence() -> None:
    assert eval_hcl("1 + 2 * 3") == 7
    assert eval_hcl("1 * 2 + 3") == 5


def test_eval_conditional() -> None:
    assert eval_hcl("true ? 1 : 2") == 1
    assert eval_hcl("false ? 1 : 2") == 2


def test_eval_parenthesis() -> None:
    assert eval_hcl("(1)") == 1
    assert eval_hcl("(1 + 2) * 3") == 9  # noqa: PLR2004, RUF100


def test_eval_array() -> None:
    assert eval_hcl("[1, 2, 3]") == [1, 2, 3]
    assert eval_hcl("[1, 2, 3, 4]") == [1, 2, 3, 4]


def test_eval_object() -> None:
    assert eval_hcl('{ foo = "bar" }') == {"foo": "bar"}
    assert eval_hcl('{ foo: "bar" }') == {"foo": "bar"}
    assert eval_hcl('{ (foo): "bar"}.baz', foo="baz") == "bar"


def test_eval_function_call() -> None:
    with pytest.raises(DiagnosticError):
        eval_hcl("foo()")


def test_eval_get_attr() -> None:
    assert eval_hcl('{"foo": "bar"}.foo') == "bar"
    assert eval_hcl('{"foo": {"bar": "baz"}}.foo.bar') == "baz"

    with pytest.raises(DiagnosticError):
        eval_hcl('{"foo": {"bar": "baz"}}.foo.baz')

    assert eval_hcl("[1,2,3].1") == 2
    with pytest.raises(DiagnosticError):
        eval_hcl("[1,2,3].3")

    with pytest.raises(DiagnosticError):
        eval_hcl('"abc".0')


def test_eval_get_index() -> None:
    assert eval_hcl('["foo", "bar"][0]') == "foo"
    assert eval_hcl('["foo", "bar"][1]') == "bar"
    with pytest.raises(DiagnosticError):
        eval_hcl('["foo", "bar"][2]')

    with pytest.raises(DiagnosticError):
        eval_hcl('"abc"[0]')


def test_eval_attr_splat() -> None:
    assert eval_hcl("a.*", a=[1, 2, 3]) == [1, 2, 3]
    assert eval_hcl("a.*.b", a=[{"b": 1}, {"b": 2}, {"b": 3}]) == [1, 2, 3]
    assert eval_hcl("a.*.b[0]", a=[{"b": [1]}, {"b": [2]}, {"b": [3]}]) == [1]

    assert eval_hcl('"abc".*') == ["abc"]


def test_eval_index_splat() -> None:
    assert eval_hcl("a[*]", a=[1, 2, 3]) == [1, 2, 3]
    assert eval_hcl("a[*].b", a=[{"b": 1}, {"b": 2}, {"b": 3}]) == [1, 2, 3]
    assert eval_hcl("a[*].b[0]", a=[{"b": [1]}, {"b": [2]}, {"b": [3]}]) == [1, 2, 3]
    assert eval_hcl('"abc"[*]') == ["abc"]


def test_eval_for_tuple_expr() -> None:
    assert eval_hcl("[for a in b: a]", b=[1, 2, 3]) == [1, 2, 3]
    assert eval_hcl("[for a, b in c: a]", c={"a": 1, "b": 2}) == ["a", "b"]
    assert eval_hcl("[for a in b: a if a > 1]", b=[1, 2, 3]) == [2, 3]
    assert eval_hcl("[for a, b in c: a if b > 1]", c={"a": 1, "b": 2}) == ["b"]
    assert eval_hcl("[for i,v in [2,3,4]: i]") == [0, 1, 2]

    with pytest.raises(DiagnosticError):
        eval_hcl('[for a in "abc": a]')


def test_eval_for_object_expr() -> None:
    with pytest.raises(DiagnosticError):
        eval_hcl("{for a, b in c: a => b...}")

    assert eval_hcl("{for a, b in c: a => b}", c={"a": 1, "b": 2}) == {"a": 1, "b": 2}
    assert eval_hcl("{for a, b in c: b => a}", c=["a", "b"]) == {"a": 0, "b": 1}
    assert eval_hcl('{ for a in b: a => a if a != "a"}', b=["a", "b", "c"]) == {
        "b": "b",
        "c": "c",
    }

    with pytest.raises(DiagnosticError):
        eval_hcl('{for a in "abc": a => a}')


def test_eval_attribute() -> None:
    evaluator = Evaluator()
    variables: dict[str, Value] = {}
    assert (
        evaluator.eval(
            parse_expr_or_stmt_with_id("a = 1"), EvaluationScope(variables=variables)
        ).raw()
        == 1
    )
    assert variables == {"a": Integer(1)}


def test_eval_scope_isolated_by_default() -> None:
    evaluator = Evaluator()
    evaluator.eval(parse_expr_or_stmt_with_id("a = 1"))
    with pytest.raises(DiagnosticError):
        evaluator.eval(parse_expr_with_id("a")).raw()


def test_eval_simple_block() -> None:
    evaluator = Evaluator()
    result = evaluator.eval(
        block(
            ident("test"),
            [],
            [
                attr(ident("a"), parse_expr_with_id("1")),
            ],
        )
    ).raw()

    assert result == {"a": 1}


def test_eval_nested_block() -> None:
    evaluator = Evaluator()
    result = evaluator.eval(
        block(
            ident("test"),
            [],
            [
                block(
                    ident("nested"),
                    [],
                    [
                        attr(ident("a"), parse_expr_with_id("1")),
                    ],
                ),
                block(
                    ident("nested"),
                    [],
                    [
                        attr(ident("a"), parse_expr_with_id("2")),
                    ],
                ),
            ],
        )
    )

    assert result.raw() == {"nested": [{"a": 1}, {"a": 2}]}
