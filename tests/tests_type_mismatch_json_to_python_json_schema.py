import json
from pathlib import Path

import allure
import pytest

from src.exceptions.custom_exceptions import (
    TypeMismatchJsonToPython,
)
from src.schema.json_schema import Schema

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
                allure.attach(
                    json.dumps(schema, indent=2, ensure_ascii=False),
                    name=f"Schema: {schema_name}",
                    attachment_type=allure.attachment_type.JSON,
                )
                return schema
            except StopIteration:
                pytest.fail(f"Схема с именем '{schema_name}' не найдена в {file_name}")

    return _loader


@allure.epic("Валидация JSON схем")
@allure.feature("Типизация свойств")
@allure.story("Проверка неизвестных типов данных")
@pytest.mark.parametrize(
    "file_name, schema_name",
    [
        ("TypeMismatchJsonToPython.json", "test_type_mismatch_date"),
        ("TypeMismatchJsonToPython.json", "test_type_mismatch_any"),
    ],
)
def test_type_mismatch_error(file_name, schema_name, get_json_schema):
    allure.dynamic.title(f"Ошибка типа: {schema_name}")

    json_data = get_json_schema(file_name, schema_name)

    with allure.step("Валидация схемы и ожидание группы ошибок"):
        with pytest.raises(ExceptionGroup) as excinfo:
            Schema.model_validate(json_data)

    with allure.step("Проверка, что в группе есть TypeMismatchJsonToPython"):
        assert excinfo.group_contains(TypeMismatchJsonToPython)


@allure.epic("Валидация JSON схем")
@allure.feature("Типизация свойств")
@allure.story("Успешная синхронизация стандартных типов")
@pytest.mark.parametrize(
    "file_name, schema_name",
    [
        ("TypeMismatchJsonToPython.json", "test_sync_type_object"),
        ("TypeMismatchJsonToPython.json", "test_sync_type_array"),
        ("TypeMismatchJsonToPython.json", "test_sync_type_null"),
        ("TypeMismatchJsonToPython.json", "test_sync_type_number"),
        ("TypeMismatchJsonToPython.json", "test_sync_type_boolean"),
    ],
)
def test_type_sync_success(file_name, schema_name, get_json_schema):
    allure.dynamic.title(f"Успешный маппинг типа: {schema_name}")

    json_data = get_json_schema(file_name, schema_name)

    with allure.step("Валидация корректной схемы"):
        # Если здесь вылетит ошибка — тест упадет (нам это и нужно)
        schema_obj = Schema.model_validate(json_data)

    with allure.step("Проверка, что объект Schema создан"):
        assert schema_obj.name is not None
