import inspect
from collections.abc import Callable
from typing import Any


def validate_signature(func: Callable) -> None:
    """Функция должна принимать ровно один аргумент (dict)."""
    sig = inspect.signature(func)
    params = list(sig.parameters.values())
    if len(params) != 1:
        raise ValueError(
            f"Функция {func.__name__} должна принимать ровно 1 аргумент, получено {len(params)}"
        )


def validate_schema(schema: dict[str, Any], func_name: str) -> None:
    """Проверка корректности JSON-схемы."""
    required_fields = ["name", "description", "parameters"]
    for field in required_fields:
        if field not in schema:
            raise ValueError(f"Схема для {func_name} не содержит обязательное поле '{field}'")

    if schema["name"] != func_name:
        raise ValueError(
            f"Имя в схеме '{schema['name']}' не соответствует имени функции '{func_name}'"
        )

    params = schema["parameters"]
    if not isinstance(params, dict) or params.get("type") != "object":
        raise ValueError("Поле 'parameters' должно быть объектом с type='object'")

    if "properties" not in params:
        raise ValueError("Схема должна содержать 'parameters.properties'")

    # Проверяем каждое свойство
    for prop_name, prop_def in params["properties"].items():
        if "type" not in prop_def:
            raise ValueError(f"Свойство '{prop_name}' должно содержать поле 'type'")
        if "description" not in prop_def:
            raise ValueError(f"Свойство '{prop_name}' должно содержать поле 'description'")
        # enum — необязательное, но если есть, проверим тип
        if "enum" in prop_def and not isinstance(prop_def["enum"], list):
            raise ValueError(f"Поле 'enum' в свойстве '{prop_name}' должно быть списком")
