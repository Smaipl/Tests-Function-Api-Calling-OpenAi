import importlib.util
import json
import os
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from src.function_validators import Validator


@dataclass
class FunctionInfo:
    name: str
    func: Callable[[dict[str, Any]], str]
    schema: dict[str, Any]
    module: str = ""


class FunctionRegistry:
    _functions: dict[str, FunctionInfo] = {}

    @staticmethod
    def execute(name: str, args: dict[str, Any]) -> str:
        if name not in FunctionRegistry._functions:
            raise KeyError(f"Функция '{name}' не найдена в реестре")
        return FunctionRegistry._functions[name].func(args)

    @staticmethod
    def get_schema(name: str) -> dict[str, Any]:
        if name not in FunctionRegistry._functions:
            raise KeyError(f"Функция '{name}' не найдена в реестре")
        return FunctionRegistry._functions[name].schema

    @staticmethod
    def register_from_file(py_file: str, schema_file: str):
        """Импортирует модуль из файла и регистрирует функцию по схеме"""
        module_name = os.path.splitext(os.path.basename(py_file))[0]

        spec = importlib.util.spec_from_file_location(module_name, py_file)
        if spec is None or spec.loader is None:
            raise ImportError(f"Не удалось создать spec для {py_file}")
        
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # Загружаем схему
        with open(schema_file, encoding="utf-8") as f:
            schema = json.load(f)

        func_name = schema["name"]
        if not hasattr(module, func_name):
            raise ValueError(f"Функция '{func_name}' не найдена в модуле {py_file}")

        func = getattr(module, func_name)

        # Валидация
        Validator.validate_signature(func)
        Validator.validate_schema(schema, func_name)

        # Регистрируем строго по имени из схемы
        FunctionRegistry._functions[func_name] = FunctionInfo(
            name=func_name,
            func=func,
            schema=schema,
            module=module_name,
        )
        print(f"📥 Зарегистрирована функция: {func_name}")
