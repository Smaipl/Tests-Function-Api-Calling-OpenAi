import inspect

import allure
import pytest
from conftest import NAME, get_mock_function

from src.exceptions.custom_exceptions import InvalidFunctionSignature
from src.schema.json_schema import Schema
from src.schema.py_schema import FunctionSchema


@allure.epic("Синхронизация Кода и Схемы")
@allure.feature("Имя функции")
@allure.story("Проверка соответствия имени функции в Python и JSON-схеме")
@pytest.mark.parametrize(
    "file_name, schema_name, function",
    [
        ("InvalidFunctionSignature.json", NAME, get_mock_function(NAME, "pass")),
        (
            "InvalidFunctionSignature.json",
            NAME,
            get_mock_function(NAME, "pass", "no_arguments"),
        ),
        (
            "InvalidFunctionSignature.json",
            NAME,
            get_mock_function(NAME, "pass", "no_arguments", "arguments"),
        ),
        (
            "InvalidFunctionSignature.json",
            NAME,
            get_mock_function(NAME, "pass", "no_arguments", "arg"),
        ),
        (
            "InvalidFunctionSignature.json",
            NAME,
            get_mock_function(NAME, "pass", "no_arguments", "arguments", "asd"),
        ),
    ],
)
def test_function_incorrect_arguments(
    file_name,
    schema_name,
    function,
    get_json_schema,
):
    allure.dynamic.title(f"Негативный тест имени: {schema_name}")

    # 1. Загружаем схему
    json_data = get_json_schema(file_name, schema_name)
    schema_obj = Schema.model_validate(json_data)

    source = getattr(function, "__source__", "")

    sig = inspect.signature(function)

    with allure.step(
        "Запуск валидации FunctionSchema и ожидание InvalidFunctionSignature"
    ):
        with pytest.raises(ExceptionGroup) as excinfo:
            FunctionSchema(
                arguments=sig.parameters, json_schema=schema_obj, source_code=source
            )

    with allure.step("Проверка наличия InvalidFunctionSignature в группе"):
        assert excinfo.group_contains(InvalidFunctionSignature)


@allure.epic("Синхронизация Кода и Схемы")
@allure.feature("Имя функции")
@allure.story("Успешная синхронизация имен")
@pytest.mark.parametrize(
    "file_name, schema_name, function",
    [
        (
            "InvalidFunctionSignature.json",
            NAME,
            get_mock_function(NAME, "pass", "arguments"),
        ),
    ],
)
def test_function_coorect_arguments(file_name, schema_name, function, get_json_schema):
    allure.dynamic.title(f"Позитивный тест имени: {schema_name}")
    json_data = get_json_schema(file_name, schema_name)
    schema_obj = Schema.model_validate(json_data)

    source = getattr(function, "__source__", "")
    sig = inspect.signature(function)

    FunctionSchema(arguments=sig.parameters, json_schema=schema_obj, source_code=source)

    assert "arguments" == sig.parameters.get("arguments").name
    assert 1 == len(sig.parameters)
