import inspect
import json
import textwrap
from pathlib import Path

import allure
import pytest

from src.exceptions.custom_exceptions import FunctionNameMismatch
from src.schema.json_schema import Schema
from src.schema.py_schema import FunctionSchema

FOLDER = Path("src/mock")


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
    "file_name, schema_name",
    [
        ("FunctionNameMismatch.json", "mismatch_function_name"),
    ],
)
def test_function_name_mismatch(file_name, schema_name, get_json_schema):
    allure.dynamic.title(f"Негативный тест имени: {schema_name}")

    # 1. Загружаем схему
    json_data = get_json_schema(file_name, schema_name)
    schema_obj = Schema.model_validate(json_data)

    def correct_function_name(arguments):
        pass

    raw_source = inspect.getsource(correct_function_name)
    source = textwrap.dedent(raw_source)
    sig = inspect.signature(correct_function_name)

    with allure.step("Запуск валидации FunctionSchema и ожидание FunctionNameMismatch"):
        with pytest.raises(ExceptionGroup) as excinfo:
            FunctionSchema(
                arguments=sig.parameters, json_schema=schema_obj, source_code=source
            )

    with allure.step("Проверка наличия FunctionNameMismatch в группе"):
        assert excinfo.group_contains(FunctionNameMismatch)


@allure.epic("Синхронизация Кода и Схемы")
@allure.feature("Имя функции")
@allure.story("Успешная синхронизация имен")
@pytest.mark.parametrize(
    "file_name, schema_name",
    [
        ("FunctionNameMismatch.json", "correct_function_name"),
    ],
)
def test_function_name_sync_success(file_name, schema_name, get_json_schema):
    allure.dynamic.title(f"Позитивный тест имени: {schema_name}")

    json_data = get_json_schema(file_name, schema_name)
    schema_obj = Schema.model_validate(json_data)

    def correct_function_name(arguments):
        pass

    raw_source = inspect.getsource(correct_function_name)
    source = textwrap.dedent(raw_source)
    sig = inspect.signature(correct_function_name)

    with allure.step("Валидация FunctionSchema (ожидаем успех)"):
        # Если имена совпадут, ошибки не будет
        FunctionSchema(
            arguments=sig.parameters, json_schema=schema_obj, source_code=source
        )
