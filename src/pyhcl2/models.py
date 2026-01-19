from __future__ import annotations

from typing import Any, TypeVar, cast

from pyagnostics.exceptions import DiagnosticError, DiagnosticErrorGroup
from pyagnostics.spans import LabeledSpan
from pydantic import BaseModel, ValidationError
from pydantic_core import ErrorDetails

from pyhcl2.eval import EvaluationScope, Evaluator
from pyhcl2.nodes import Block
from pyhcl2.rich_utils import Inline
from pyhcl2.values import Array, Object, String, Value

Model = TypeVar("Model", bound=BaseModel)


def load_model_from_block(
    block: Block,
    model_cls: type[Model],
    evaluator: Evaluator = Evaluator(),
    scope: EvaluationScope | None = None,
) -> Model:
    scope = scope or EvaluationScope()
    block_value: Object = cast(Object, evaluator.eval(block, scope))
    field_values: dict[str, Any] = {}
    field_context: dict[str, Value] = {}

    for k, v in block_value.items():
        name = k.raw()
        if name in model_cls.model_fields:
            field = model_cls.model_fields[name]

            field_context[name] = v
            if field.annotation is not None and (
                field.annotation is type(v) or field.annotation is Value
            ):
                field_values[name] = v
            else:
                field_values[name] = v.raw()

    try:
        return model_cls.model_validate(field_values, context=field_context)
    except ValidationError as e:
        diagnostics: list[DiagnosticError] = []
        for error in e.errors():
            error = cast(ErrorDetails, error)

            value: Value = block_value
            try:
                for loc in error["loc"]:
                    match loc:
                        case int():
                            assert isinstance(value, Array)
                            value = value[loc]
                        case str():
                            assert isinstance(value, Object)
                            value = value[String(loc)]
            except KeyError:
                pass

            field_key = list(block.key()) + [str(val) for val in error["loc"]]
            field_key_str = ".".join(field_key)

            match error["type"]:
                case "missing":
                    diagnostics.append(
                        DiagnosticError(
                            code="pyhcl2::models::validation_error",
                            message=f"Missing required field {field_key_str}",
                            labels=[
                                LabeledSpan(
                                    value.span, f"{value.type_name} missing field"
                                ),
                            ]
                            if value.span is not None
                            else [],
                        )
                    )
                case _:
                    diagnostics.append(
                        DiagnosticError(
                            code=f"pyhcl2::pydantic_validation_error::{error['type']}",
                            message=error["msg"],
                            labels=[
                                LabeledSpan(value.span, "invalid input"),
                            ]
                            if value.span is not None
                            else [],
                            notes=[Inline("[blue]context:[/blue] ", repr(error["ctx"]))]
                            if "ctx" in error
                            else [],
                        )
                    )

        raise DiagnosticErrorGroup("Failed to validate hcl model", diagnostics)
