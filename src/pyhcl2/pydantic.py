from __future__ import annotations

from typing import Any, TypeVar

from pydantic import BaseModel, ValidationError

from pyhcl2 import Attribute, Block
from pyhcl2.eval import EvaluationScope, Evaluator
from pyhcl2.exceptions import HclExceptionGroup, HCLModelValidationError

Model = TypeVar("Model", bound=BaseModel)


# ruff: noqa: PLR0912
def load_model_from_block(
    block: Block,
    model_cls: type[Model],
    evaluator: Evaluator = Evaluator(),
    scope: EvaluationScope = EvaluationScope(),
) -> Model:
    field_keys = list(model_cls.model_fields.keys())
    field_values: dict[str, Any] = {}

    for stmt in block.body:
        stmt_key = stmt.key_path[0]
        if stmt_key not in field_keys:
            continue

        key: tuple[str, ...]
        if isinstance(stmt, Block):
            key = stmt.key_path
            value = evaluator.eval(stmt, scope.child())
            target_dict = field_values
            for k in key[:-1]:
                target_dict = target_dict.setdefault(k, {})
            target_dict.setdefault(key[-1], []).append(value)

        elif isinstance(stmt, Attribute):
            key = (stmt.key.name,)
            value = evaluator.eval(stmt, scope.child())
            target_dict = field_values
            for k in key[:-1]:
                target_dict = target_dict.setdefault(k, {})
            target_dict[key[-1]] = value
        else:
            raise TypeError(f"Unsupported statement type {stmt}")

    try:
        model = model_cls.parse_obj(field_values)
    except ValidationError as e:
        exceptions: list[Exception] = []

        for error in e.errors():
            field_key = list(block.key()) + [str(val) for val in error["loc"]]
            field_key_str = ".".join(field_key)
            match error["type"]:
                case "missing":
                    exceptions.append(
                        HCLModelValidationError(
                            f"Missing required field {field_key_str}"
                        )
                    )
                case "too_long":
                    exceptions.append(
                        HCLModelValidationError(
                            f"{field_key_str} should be at most {error['ctx']['max_length']} item but was {error['ctx']['actual_length']}"
                        )
                    )
                case _:
                    exceptions.append(
                        HCLModelValidationError(f"Unhandled pydantic error: {error}")
                    )
        raise HclExceptionGroup("Failed to validate hcl model", exceptions)
    else:
        return model
