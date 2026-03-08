import sys
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, PrivateAttr, model_validator

from src.exceptions.custom_exceptions import (
    EmptyRequiredFields,
    TypeMismatchJsonToPython,
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


class Property(BaseModel):
    schema_type: str | None = Field(default=None, alias="type")
    description: str | None = None
    enum: list[Any] | None = None
    default: Any | None = None

    model_config = ConfigDict(populate_by_name=True, extra="allow")


class Parameters(BaseModel):
    type: str
    properties: dict[str, Property]
    required: list[str] = []
    _required_fields = PrivateAttr(default=["schema_type", "description", "default"])

    model_config = ConfigDict(extra="ignore")

    @model_validator(mode="after")
    def validate_schema(self):
        errors = []

        for key, prop in self.properties.items():
            missing = [f for f in self._required_fields if getattr(prop, f) is None]
            if missing:
                errors.append(
                    EmptyRequiredFields(
                        message=f"В ключе '{key}' пропущены обязательные поля",
                        fields=missing,
                    )
                )

            typemismatch = TYPE_MAPPING.get(prop.schema_type, "unknown")
            if typemismatch == "unknown":
                errors.append(
                    TypeMismatchJsonToPython(
                        f"В ключе '{key}' есть несоответствие типов",
                        (prop.schema_type,),
                    )
                )

        raise ExceptionGroup("Ошибки валидации и типизации", errors)


class Schema(BaseModel):
    name: str
    description: str
    parameters: Parameters
    model_config = ConfigDict(extra="ignore")
