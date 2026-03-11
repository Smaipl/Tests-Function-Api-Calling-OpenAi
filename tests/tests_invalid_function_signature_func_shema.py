import inspect
import json
import textwrap
import types
from pathlib import Path

import allure
import pytest

from src.exceptions.custom_exceptions import InvalidFunctionSignature
from src.schema.json_schema import Schema
from src.schema.py_schema import FunctionSchema

FOLDER = Path("src/mock")
NAME = "function_name"


def get_mock_function(*args):
    args_str = ", ".join(map(str, args))
    source = f"def {NAME}({args_str}): pass"

    func_module: inspect.CodeType = compile(source, "<string>", "exec")
    func_code: inspect.CodeType = [
        c for c in func_module.co_consts if isinstance(c, types.CodeType)
    ][0]

    func = types.FunctionType(func_code, globals(), NAME)
    func.__source__ = source

    return func


@pytest.fixture
def get_json_schema():
    def _loader(file_name: str, schema_name: str):
        file_path = FOLDER / file_name

        with allure.step(f"Чтение файла {file_name}"):
            with open(file_path, encoding="utf-8") as f:
                raw_json = json.load(f)

        with allure.step(f"Поиск схемы '{schema_name}'"):
            try:
                schema = next(j for j in raw_json if j["name"] == schema_name)
                # Прикрепляем JSON прямо к отчету Allure
                allure.attach(
                    json.dumps(schema, indent=2, ensure_ascii=False),
                    name=f"Schema: {schema_name}",
                    attachment_type=allure.attachment_type.JSON,
                )
                return schema
            except StopIteration:
                pytest.fail(f"Схема с именем '{schema_name}' не найдена в {file_name}")

    return _loader


@allure.epic("Синхронизация Кода и Схемы")
@allure.feature("Имя функции")
@allure.story("Проверка соответствия имени функции в Python и JSON-схеме")
@pytest.mark.parametrize(
    "file_name, schema_name, function",
    [
        ("InvalidFunctionSignature.json", NAME, get_mock_function()),
        ("InvalidFunctionSignature.json", NAME, get_mock_function("no_arguments")),
        (
            "InvalidFunctionSignature.json",
            NAME,
            get_mock_function("no_arguments", "arguments"),
        ),
        (
            "InvalidFunctionSignature.json",
            NAME,
            get_mock_function("no_arguments", "arg"),
        ),
        (
            "InvalidFunctionSignature.json",
            NAME,
            get_mock_function("no_arguments", "arguments", "asd"),
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

    source = textwrap.dedent(function.__source__)

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
        ("InvalidFunctionSignature.json", NAME, get_mock_function("arguments")),
    ],
)
def test_function_coorect_arguments(file_name, schema_name, function, get_json_schema):
    allure.dynamic.title(f"Позитивный тест имени: {schema_name}")
    # 1. Загружаем схему
    json_data = get_json_schema(file_name, schema_name)
    schema_obj = Schema.model_validate(json_data)

    source = textwrap.dedent(function.__source__)
    sig = inspect.signature(function)

    FunctionSchema(arguments=sig.parameters, json_schema=schema_obj, source_code=source)

    assert "arguments" == sig.parameters.get("arguments").name
    assert 1 == len(sig.parameters)
