from pydantic import BaseModel, Field, ValidationInfo, field_validator
from pyagnostics.exceptions import DiagnosticErrorGroup

from pyhcl2.models import load_model_from_block
from pyhcl2.nodes import Block
from pyhcl2.parse import parse_expr_or_stmt
from pyhcl2.values import Value


class ExampleModel(BaseModel):
    foo: int

    @field_validator("foo")
    @classmethod
    def require_context(cls, value: int, info: ValidationInfo) -> int:
        assert info.context is not None
        raw = info.context["foo"]
        assert isinstance(raw, Value)
        assert raw.span is not None
        return value


def test_load_model_from_block_passes_context() -> None:
    node = parse_expr_or_stmt('example { foo = 1 }')
    assert isinstance(node, Block)
    model = load_model_from_block(node, ExampleModel)
    assert model.foo == 1


class ExamplePassModel(BaseModel):
    name: str
    value: list[int] = Field(min_length=2)


def test_load_model_from_block_pass_case() -> None:
    node = parse_expr_or_stmt('example { name = "test" value = [1, 2] }')
    assert isinstance(node, Block)
    model = load_model_from_block(node, ExamplePassModel)
    assert model.name == "test"
    assert model.value == [1, 2]


class MissingFieldModel(BaseModel):
    foo: int


def test_load_model_from_block_missing_field_has_span() -> None:
    node = parse_expr_or_stmt('missing_example { }')
    assert isinstance(node, Block)
    try:
        load_model_from_block(node, MissingFieldModel)
    except DiagnosticErrorGroup as exc:
        errors = exc.exceptions
        assert errors
        assert any(
            diag.labels and diag.labels[0].span is not None for diag in errors
        )
    else:
        assert False, "Expected DiagnosticErrorGroup"
