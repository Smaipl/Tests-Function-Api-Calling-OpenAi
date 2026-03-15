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


@allure.epic("Синхронизация Кода и Схемы")
@allure.feature("Анализ тела функции (AST)")
@allure.story("Отлов рассинхрона аргументов и дефолтов")
@pytest.mark.parametrize(
    "file_name, schema_name, function, case_name",
    [
        (
            "SchemaSyncError.json",
            NAME,
            get_mock_function(NAME, body_hidden_in_if, "arguments"),
            "Hidden in IF",
        ),
        (
            "SchemaSyncError.json",
            NAME,
            get_mock_function(NAME, body_sync_error, "arguments"),
            "Unknown Key",
        ),
        (
            "SchemaSyncError.json",
            NAME,
            get_mock_function(NAME, body_complex, "arguments"),
            "Complex Assignment",
        ),
    ],
)
def test_function_sync_errors(
    file_name, schema_name, function, case_name, get_json_schema
):
    allure.dynamic.title(f"Ошибка синхронизации AST: {case_name}")

    json_data = get_json_schema(file_name, schema_name)
    schema_obj = Schema.model_validate(json_data)
    source = getattr(function, "__source__", "")
    sig = inspect.signature(function)

    allure.attach(
        source,
        name="Source Code under test",
        attachment_type=allure.attachment_type.TEXT,
    )

    with allure.step("Валидация FunctionSchema и поиск SchemaSyncError"):
        with pytest.raises(ExceptionGroup) as excinfo:
            FunctionSchema(
                arguments=sig.parameters, json_schema=schema_obj, source_code=source
            )

        sync_errors = excinfo.value.subgroup(SchemaSyncError)
        if sync_errors:
            allure.attach(
                str(sync_errors),
                name="Детали рассинхрона (AST mismatch)",
                attachment_type=allure.attachment_type.TEXT,
            )

        assert excinfo.group_contains(SchemaSyncError)


@allure.epic("Синхронизация Кода и Схемы")
@allure.feature("Анализ тела функции (AST)")
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
    allure.dynamic.title(f"Успешный AST-матчинг: {schema_name}")

    json_data = get_json_schema(file_name, schema_name)
    schema_obj = Schema.model_validate(json_data)
    source = getattr(function, "__source__", "")
    sig = inspect.signature(function)

    allure.attach(
        source, name="Valid Source Code", attachment_type=allure.attachment_type.TEXT
    )

    with allure.step("Валидация FunctionSchema (ожидаем полное соответствие)"):
        FunctionSchema(
            arguments=sig.parameters, json_schema=schema_obj, source_code=source
        )
