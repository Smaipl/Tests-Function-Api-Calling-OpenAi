import inspect

import allure
import pytest
from conftest import NAME, get_mock_function

from src.exceptions.custom_exceptions import InvalidFunctionSignature
from src.schema.json_schema import Schema
from src.schema.py_schema import FunctionSchema


@allure.epic("Синхронизация Кода и Схемы")
@allure.feature("Сигнатура функции")
@allure.story("Валидация аргументов и параметров")
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
    sig = inspect.signature(function)
    allure.dynamic.title(
        f"Негативный тест сигнатуры: {len(sig.parameters)} арг. в {schema_name}"
    )

    allure.dynamic.parameter("file_name", file_name)
    allure.dynamic.parameter("actual_args", list(sig.parameters.keys()))

    with allure.step("1. Загрузка и валидация базовой JSON схемы"):
        json_data = get_json_schema(file_name, schema_name)
        schema_obj = Schema.model_validate(json_data)
        source = getattr(function, "__source__", "")

    with allure.step(
        "2. Запуск валидации FunctionSchema (ожидаем InvalidFunctionSignature)"
    ):
        with pytest.raises(ExceptionGroup) as excinfo:
            FunctionSchema(
                arguments=sig.parameters, json_schema=schema_obj, source_code=source
            )

    with allure.step(
        "3. Проверка наличия InvalidFunctionSignature в группе исключений"
    ):
        error_details = str(excinfo.value)
        allure.attach(
            error_details,
            name="ExceptionGroup Traceback",
            attachment_type=allure.attachment_type.TEXT,
        )
        assert excinfo.group_contains(InvalidFunctionSignature)


@allure.epic("Синхронизация Кода и Схемы")
@allure.feature("Сигнатура функции")
@allure.story("Успешная синхронизация аргументов")
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
    sig = inspect.signature(function)
    allure.dynamic.title(f"Позитивный тест сигнатуры: {schema_name}")

    with allure.step("1. Подготовка данных и схемы"):
        json_data = get_json_schema(file_name, schema_name)
        schema_obj = Schema.model_validate(json_data)
        source = getattr(function, "__source__", "")

    with allure.step("2. Валидация FunctionSchema (ожидаем успех)"):
        FunctionSchema(
            arguments=sig.parameters, json_schema=schema_obj, source_code=source
        )

    with allure.step("3. Финальные проверки параметров"):
        assert (
            "arguments" in sig.parameters
        ), "Аргумент 'arguments' должен присутствовать"
        assert len(sig.parameters) == 1, "Должен быть ровно 1 аргумент"
