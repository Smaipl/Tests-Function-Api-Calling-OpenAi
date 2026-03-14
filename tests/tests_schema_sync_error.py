import inspect

import allure
import pytest

from src.exceptions.custom_exceptions import SchemaSyncError
from src.schema.json_schema import Schema
from src.schema.py_schema import FunctionSchema
from tests.conftest import NAME, get_mock_function

body_hidden_in_if = """
    if True:
        mode = arguments.get("mode", "fast") 
"""

body_ok = "v1 = arguments.get('prompt', '')"
body_sync_error = "v1 = arguments.get('unknown_key', 'default')"

body_complex = """
    v1, v2, v3, v4 = (
        arguments.get("prompt", ""), 
        arguments.get("limit", 10), 
        arguments.get("is_active", True),
        arguments.get("bla_bla_bla", True)
    )
"""


@allure.story("Отлов рассинхрона аргументов и дефолтов")
@pytest.mark.parametrize(
    "file_name, schema_name, function",
    [
        (
            "SchemaSyncError.json",
            NAME,
            get_mock_function(NAME, body_hidden_in_if, "arguments"),
        ),
        (
            "SchemaSyncError.json",
            NAME,
            get_mock_function(NAME, body_sync_error, "arguments"),
        ),
        (
            "SchemaSyncError.json",
            NAME,
            get_mock_function(NAME, body_complex, "arguments"),
        ),
    ],
)
def test_function_sync_errors(file_name, schema_name, function, get_json_schema):
    allure.dynamic.title(f"Негативный тест: {schema_name}")

    json_data = get_json_schema(file_name, schema_name)
    schema_obj = Schema.model_validate(json_data)

    source = getattr(function, "__source__", "")
    sig = inspect.signature(function)

    with allure.step("Запуск валидации и ожидание ExceptionGroup"):
        with pytest.raises(ExceptionGroup) as excinfo:
            FunctionSchema(
                arguments=sig.parameters, json_schema=schema_obj, source_code=source
            )

        assert excinfo.group_contains(SchemaSyncError)


@allure.story("Успешная синхронизация кода и JSON-схемы")
@pytest.mark.parametrize(
    "file_name, schema_name, function",
    [
        (
            "SchemaSyncError.json",
            "function_name",
            get_mock_function(NAME, body_ok, "arguments"),
        ),
    ],
)
def test_function_sync_success(file_name, schema_name, function, get_json_schema):
    allure.dynamic.title(f"Позитивный тест: {schema_name}")

    json_data = get_json_schema(file_name, schema_name)
    schema_obj = Schema.model_validate(json_data)

    source = getattr(function, "__source__", "")
    sig = inspect.signature(function)

    with allure.step("Валидация FunctionSchema (ожидаем успех)"):
        FunctionSchema(
            arguments=sig.parameters, json_schema=schema_obj, source_code=source
        )
