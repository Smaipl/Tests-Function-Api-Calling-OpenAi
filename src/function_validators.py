import inspect
from collections.abc import Callable
from typing import Any


class Validator:
    @staticmethod
    def validate_signature(func: Callable) -> None:
        sig = inspect.signature(func)
        params = list(sig.parameters.values())

        if len(params) != 1:
            raise ValueError(
                f"Функция {func.__name__} должна принимать ровно 1 аргумент, получено {len(params)}"
            )

        # if params[0].annotation is inspect._empty or params[0].annotation is not dict:
        #     raise ValueError(f"Функция {func.__name__} должна принимать аргумент типа dict")
        
        # if sig.return_annotation is inspect._empty or sig.return_annotation is not str:
        #     raise ValueError(f"Функция {func.__name__} должна возвращать значение типа str")

    @staticmethod
    def validate_schema(schema: dict[str, Any], func_name: str) -> None:
        not_support = ["oneOf", "minimum", "default"]
        required_top = ["name", "description", "parameters"]
        for field in required_top:
            if field not in schema:
                raise ValueError(
                    f"Схема для {func_name} не содержит обязательное поле '{field}'"
                )

        if schema["name"] != func_name:
            raise ValueError(
                f"Имя в схеме '{schema['name']}' не соответствует имени функции '{func_name}'"
            )

        params = schema["parameters"]
        if not isinstance(params, dict) or params.get("type") != "object":
            raise ValueError("Поле 'parameters' должно быть объектом с type='object'")

        if "properties" not in params:
            raise ValueError("Схема должна содержать 'parameters.properties'")
        if "required" not in params:
            raise ValueError("Схема должна содержать 'parameters.required'")

        for prop_name, prop_def in params["properties"].items():
            if "type" not in prop_def:
                raise ValueError(f"Свойство '{prop_name}' должно содержать поле 'type'")
            if "description" not in prop_def:
                raise ValueError(f"Свойство '{prop_name}' должно содержать поле 'description'")
            if "enum" in prop_def and not isinstance(prop_def["enum"], list):
                raise ValueError(f"Поле 'enum' в свойстве '{prop_name}' должно быть списком")
            if prop_def in not_support:
                raise ValueError(
                    f"Поле '{prop_def}' в свойстве '{prop_name}' не поддерживается!"
                )
