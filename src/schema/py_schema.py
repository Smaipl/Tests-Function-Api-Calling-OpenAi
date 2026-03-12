import ast
from dataclasses import dataclass
from inspect import Parameter
from types import MappingProxyType
from typing import Any

from pydantic import BaseModel, ConfigDict, PrivateAttr, TypeAdapter, model_validator

from src.exceptions.custom_exceptions import (
    DefaultValueMismatch,
    FunctionNameMismatch,
    InvalidFunctionSignature,
    SchemaSyncError,
)
from src.schema.json_schema import Schema
from src.utils.interfaces import TYPE_MAPPING


def normalize_value(val: Any, target_type_str: str) -> Any:
    """
    Приводит значение из кода к типу из JSON-схемы для честного сравнения.
    """

    target_type = TYPE_MAPPING.get(target_type_str)
    if target_type is None:
        return val

    try:
        return TypeAdapter(target_type).validate_python(val)
    except Exception:
        return val


@dataclass(slots=True)
class InfoArg:
    stroke: int = 0
    key: str = ""
    val: Any = None


class FunctionSchema(BaseModel):
    arguments: MappingProxyType[str, Parameter] = MappingProxyType({})
    json_schema: Schema
    source_code: str = ""
    _args_map: list[InfoArg] = PrivateAttr(default_factory=list)
    _all_call_obj: list[str] = PrivateAttr(default_factory=list)

    model_config = ConfigDict(extra="ignore", arbitrary_types_allowed=True)

    @model_validator(mode="after")
    def find_debug_calls(self) -> "FunctionSchema":
        if not self.source_code:
            return self

        try:
            tree = ast.parse(self.source_code)
        except Exception as e:
            raise ValueError(f"Ошибка парсинга кода: {e}")  # noqa: B904

        found_args = []

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                self._all_call_obj.append(node.name)
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr == "get"
                and isinstance(node.func.value, ast.Name)
                and node.func.value.id == "arguments"
            ):
                key_val = ""
                if len(node.args) > 0 and isinstance(node.args[0], ast.Constant):
                    key_val = node.args[0].value

                default_val = None
                if len(node.args) > 1 and isinstance(node.args[1], ast.Constant):
                    default_val = node.args[1].value
                else:
                    for kw in node.keywords:
                        if kw.arg == "default" and isinstance(kw.value, ast.Constant):
                            default_val = kw.value.value

                card = InfoArg(stroke=node.lineno, key=key_val, val=default_val)
                found_args.append(card)
                print(f"Найдено: {card}")

        self._args_map = found_args

        return self

    @model_validator(mode="after")
    def validate_func_schema(self) -> "FunctionSchema":
        errors: list = []

        if self.json_schema.name not in self._all_call_obj:
            errors.append(
                FunctionNameMismatch(
                    message=f"Функция {self.json_schema.name} не найдена в исходном коде",
                    fields={
                        "expected": self.json_schema.name,
                        "available": self._all_call_obj,
                    },
                )
            )

        if len(self.arguments) != 1 or "arguments" not in self.arguments:
            errors.append(
                InvalidFunctionSignature(
                    message="Функция должна принимать ровно один аргумент: 'arguments'",
                    fields=list(self.arguments.keys()),
                )
            )

        properties = self.json_schema.parameters.properties

        for info in self._args_map:
            prop = properties.get(info.key)

            if prop is None:
                errors.append(
                    SchemaSyncError(
                        message="Аргумент  не описан в JSON-схеме",
                        fields={
                            "line": info.stroke,
                            "key": info.key,
                        },
                    )
                )
                continue

            schema_default = prop.default
            code_default = info.val

            normalized_code_val = normalize_value(code_default, prop.property_type)
            normalized_schema_val = normalize_value(schema_default, prop.property_type)

            if normalized_code_val != normalized_schema_val:
                errors.append(
                    DefaultValueMismatch(
                        message=f"Несовпадение default для '{info.key}': ",
                        fields={
                            "line": info.stroke,
                            "key": info.key,
                            "values": {
                                "in_python_code": normalized_code_val,
                                "in_json_schema": schema_default,
                            },
                        },
                    )
                )

        if errors:
            raise ExceptionGroup("Ошибки валидации и синхронизации", errors)

        return self
