import allure
import pytest

from src.exceptions.custom_exceptions import (
    TypeMismatchJsonToPython,
)
from src.schema.json_schema import Schema


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
        schema_obj = Schema.model_validate(json_data)

    with allure.step("Проверка, что объект Schema создан"):
        assert schema_obj.name is not None
