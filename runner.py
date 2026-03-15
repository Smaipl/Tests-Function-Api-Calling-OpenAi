import inspect
import json
import os
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

import allure
import pytest

# Твои модули схем
from src.schema.json_schema import Schema
from src.schema.py_schema import FunctionSchema


@allure.epic("Валидация функций пользователя")
@allure.feature("Проверка синхронизации")
@allure.story("Анализ кода и JSON схемы")
@allure.severity(allure.severity_level.CRITICAL)
def test_function_sync():
    # 1. Получаем пути из переменных окружения (их передаст action.yml)
    func_path = os.environ.get("INPUT_FUNC_PATH")
    schema_path = os.environ.get("INPUT_SCHEMA_PATH")

    if not func_path or not schema_path:
        pytest.fail("Не переданы пути к файлам (INPUT_FUNC_PATH / INPUT_SCHEMA_PATH)")

    py_file = Path(func_path)
    json_file = Path(schema_path)
    func_name = py_file.stem

    allure.attach.file(
        py_file, name="Python File", attachment_type=allure.attachment_type.TEXT
    )
    allure.attach.file(
        json_file, name="Schema File", attachment_type=allure.attachment_type.JSON
    )

    # 2. Валидация схемы
    with allure.step(f"Загрузка схемы из {json_file.name}"):
        with open(json_file, encoding="utf-8") as f:
            schema_data = json.load(f)
            if isinstance(schema_data, dict) and func_name in schema_data:
                schema_dict = schema_data[func_name]
            else:
                schema_dict = schema_data

            schema = Schema.model_validate(schema_dict)
            allure.attach(
                json.dumps(schema_dict, indent=2),
                name="JSON Schema Content",
                attachment_type=allure.attachment_type.JSON,
            )

    # 3. Загрузка и анализ кода
    with allure.step(f"Загрузка функции {func_name} из {py_file.name}"):
        spec = spec_from_file_location(func_name, py_file.absolute())
        if spec is None or spec.loader is None:
            pytest.fail(f"Не удалось загрузить модуль из {py_file}")

        mod = module_from_spec(spec)
        spec.loader.exec_module(mod)

        if not hasattr(mod, func_name):
            pytest.fail(f"Функция '{func_name}' не найдена в файле {py_file.name}")

        func = getattr(mod, func_name)
        source_code = inspect.getsource(func)
        allure.attach(
            source_code,
            name="Python Source Code",
            attachment_type=allure.attachment_type.TEXT,
        )

    # 4. Основная проверка
    with allure.step("Проверка синхронизации аргументов"):
        try:
            FunctionSchema.model_validate(
                {
                    "arguments": inspect.signature(func).parameters,
                    "json_schema": schema,
                    "source_code": source_code,
                }
            )
        except Exception as e:
            allure.attach(
                str(e),
                name="Ошибка валидации",
                attachment_type=allure.attachment_type.TEXT,
            )
            raise  # pytest подхватит ошибку и отметит тест как FAILED

    allure.dynamic.label("status", "passed")
