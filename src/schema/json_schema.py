from collections.abc import Sequence
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, PrivateAttr, model_validator

from src.exceptions.custom_exceptions import (
    EmptyRequiredFields,
    MismatchRequiredFieldsInKey,
    TypeMismatchJsonToPython,
    UnregisterField,
)
from src.utils.interfaces import DEFAULT_REQUIRED_FIELDS_PROPERTIES, TYPE_MAPPING


def get_mismatch_required_in_ptop_keys(
    required: Sequence[str], keys: Sequence[str]
) -> set[str] | None:
    return set(required) - set(keys)


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
    description: str | None = Field(default=None, min_length=1, max_length=600)
    enum: list[Any] | None = Field(default=None)
    default: Any = None

    model_config = ConfigDict(populate_by_name=True, extra="allow")


class Parameters(BaseModel):
    parameter_type: Literal["object"] = Field(alias="type")
    properties: dict[str, Property]
    required: list[str] = Field(default_factory=list)
    _required_fields_in_prop: list[str] = PrivateAttr(
        default_factory=lambda: list(
            set(DEFAULT_REQUIRED_FIELDS_PROPERTIES) & set(Property.model_fields.keys())
        )
    )

    model_config = ConfigDict(populate_by_name=True, extra="allow")


class Schema(BaseModel):
    name: str
    description: str = Field(min_length=1, max_length=1024)
    parameters: Parameters

    model_config = ConfigDict(extra="allow")

    @model_validator(mode="after")
    def validate_all_extra_fields(self):
        errors = get_extra_field_errors(self)

        keysmismatch = get_mismatch_required_in_ptop_keys(
            self.parameters.required, self.parameters.properties.keys()
        )

        if keysmismatch:
            errors.append(
                MismatchRequiredFieldsInKey(
                    message="Лишние аргументы которых нет в properties['keys']",
                    fields=keysmismatch,
                )
            )

        for key, prop in self.parameters.properties.items():
            missing = (
                set(self.parameters._required_fields_in_prop) - prop.model_fields_set
            )

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
