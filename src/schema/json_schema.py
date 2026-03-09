import sys
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, PrivateAttr, model_validator

from src.exceptions.custom_exceptions import (
    EmptyRequiredFields,
    TypeMismatchJsonToPython,
    UnregisterField,
)

sys.tracebacklimit = 0


TYPE_MAPPING: dict[str, dict[str, Any]] = {
    "object": {"dict": {}},
    "array": {"list": [], "tuple": ()},
    "string": {"str": ""},
    "number": {"float": 0.0, "int": 0},
    "integer": {"int": 0},
    "boolean": {"bool": False},
    "null": {"None": None},
}


def get_extra_field_errors(obj: BaseModel):
    errors = []

    if obj.model_extra:
        errors.append(
            UnregisterField(
                f"Лишние ключи в {type(obj).__name__}", list(obj.model_extra.keys())
            )
        )

    for field_name in type(obj).model_fields:
        value = getattr(obj, field_name)

        if isinstance(value, BaseModel):
            errors.extend(get_extra_field_errors(value))

        elif isinstance(value, list):
            for item in value:
                if isinstance(item, BaseModel):
                    errors.extend(get_extra_field_errors(item))

        elif isinstance(value, dict):
            for val in value.values():
                if isinstance(val, BaseModel):
                    errors.extend(get_extra_field_errors(val))

    return errors


class Property(BaseModel):
    property_type: str | None = Field(default=None, alias="type")
    description: str | None = None
    enum: list[Any] | None = None
    default: Any | None = None

    model_config = ConfigDict(populate_by_name=True, extra="allow")


class Parameters(BaseModel):
    parameter_type: str = Field(default="", alias="type")
    properties: dict[str, Property]
    required: list[str] = []

    model_config = ConfigDict(populate_by_name=True, extra="allow")


class Schema(BaseModel):
    name: str
    description: str
    parameters: Parameters
    _required_fields = PrivateAttr(default=["property_type", "description", "default"])

    model_config = ConfigDict(extra="allow")

    @model_validator(mode="after")
    def validate_all_extra_fields(self):
        errors = get_extra_field_errors(self)

        for key, prop in self.parameters.properties.items():
            missing = [f for f in self._required_fields if getattr(prop, f) is None]
            if missing:
                errors.append(
                    EmptyRequiredFields(
                        message=f"В ключе '{key}' пропущены обязательные поля",
                        fields=missing,
                    )
                )

            typemismatch = TYPE_MAPPING.get(prop.property_type, "unknown")
            if typemismatch == "unknown":
                errors.append(
                    TypeMismatchJsonToPython(
                        f"В ключе '{key}' есть несоответствие типов",
                        (prop.property_type,),
                    )
                )

        if errors:
            raise ExceptionGroup("Ошибки валидации и типизации:", errors)

        return self
