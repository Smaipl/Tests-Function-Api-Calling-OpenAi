from typing import Any

from pydantic import BaseModel, ConfigDict, Field, PrivateAttr, model_validator

from src.exceptions.custom_exceptions import (
    EmptyRequiredFields,
    TypeMismatchJsonToPython,
    UnregisterField,
)
from src.utils.interfaces import DEFAULT_REQUIRED_FIELDS, TYPE_MAPPING


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
    enum: list[Any] = Field(default_factory=list)
    default: Any = None

    model_config = ConfigDict(populate_by_name=True, extra="allow")


class Parameters(BaseModel):
    parameter_type: str = Field(alias="type")
    properties: dict[str, Property]
    required: list[str] = Field(default_factory=list)
    _required_fields = PrivateAttr(default=DEFAULT_REQUIRED_FIELDS)

    model_config = ConfigDict(populate_by_name=True, extra="allow")


class Schema(BaseModel):
    name: str
    description: str
    parameters: Parameters

    model_config = ConfigDict(extra="allow")

    @model_validator(mode="after")
    def validate_all_extra_fields(self):
        errors = get_extra_field_errors(self)

        for key, prop in self.parameters.properties.items():
            missing = [
                f
                for f in self.parameters._required_fields
                if f not in prop.model_fields_set
            ]

            if missing:
                errors.append(
                    EmptyRequiredFields(
                        message=f"В ключе '{key}' пропущены обязательные поля",
                        fields=missing,
                    )
                )

            if prop.property_type:
                typemismatch = TYPE_MAPPING.get(prop.property_type, "unknown")
                if typemismatch == "unknown":
                    errors.append(
                        TypeMismatchJsonToPython(
                            f"В ключе '{key}' есть несоответствие типов",
                            prop.property_type,
                        )
                    )

        if errors:
            raise ExceptionGroup("Ошибки валидации и типизации:", errors)

        return self
