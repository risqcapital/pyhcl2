from pydantic import BaseModel, ValidationInfo, field_validator

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
