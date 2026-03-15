import inspect

import allure
import pytest
from conftest import NAME, get_mock_function

from src.exceptions.custom_exceptions import FunctionNameMismatch
from src.schema.json_schema import Schema
from src.schema.py_schema import FunctionSchema


@allure.epic("Синхронизация Кода и Схемы")
@allure.feature("Имя функции")
@allure.story("Проверка соответствия имени функции в Python и JSON-схеме")
@pytest.mark.parametrize(
    "file_name, schema_name, function",
    [
        (
            "FunctionNameMismatch.json",
            "mismatch_function_name",
            get_mock_function(NAME, "pass", "arguments"),
        ),
    ],
)
def test_function_name_mismatch(file_name, schema_name, function, get_json_schema):
    allure.dynamic.title(f"Негативный тест имени: {schema_name}")
    allure.dynamic.parameter("schema_name", schema_name)
    allure.dynamic.parameter("file_name", file_name)

    json_data = get_json_schema(file_name, schema_name)
    schema_obj = Schema.model_validate(json_data)

    source = getattr(function, "__source__", "")
    sig = inspect.signature(function)

    with allure.step("Запуск валидации и ожидание ошибки"):
        with pytest.raises(ExceptionGroup) as excinfo:
            FunctionSchema(
                arguments=sig.parameters, json_schema=schema_obj, source_code=source
            )

        mismatches = excinfo.value.subgroup(FunctionNameMismatch)
        if mismatches:
            error_msg = str(mismatches.exceptions[0])
            allure.attach(
                error_msg,
                name="Текст найденной ошибки",
                attachment_type=allure.attachment_type.TEXT,
            )

        assert excinfo.group_contains(FunctionNameMismatch)


@allure.epic("Синхронизация Кода и Схемы")
@allure.feature("Имя функции")
@allure.story("Успешная синхронизация имен")
@pytest.mark.parametrize(
    "file_name, schema_name, function",
    [
        (
            "FunctionNameMismatch.json",
            NAME,
            get_mock_function(NAME, "pass", "arguments"),
        ),
    ],
)
def test_function_name_sync_success(file_name, schema_name, function, get_json_schema):
    allure.dynamic.title(f"Позитивный тест имени: {schema_name}")

    json_data = get_json_schema(file_name, schema_name)
    schema_obj = Schema.model_validate(json_data)

    source = getattr(function, "__source__", "")
    sig = inspect.signature(function)

    with allure.step("Валидация FunctionSchema (ожидаем успех)"):
        FunctionSchema(
            arguments=sig.parameters, json_schema=schema_obj, source_code=source
        )
