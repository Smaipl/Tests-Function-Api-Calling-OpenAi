import allure
import pytest
from pydantic import ValidationError

from src.exceptions.custom_exceptions import EmptyRequiredFields
from src.schema.json_schema import Schema


@allure.epic("Валидация JSON схем")
@allure.feature("Обязательные поля свойств")
@allure.story("Проверка выброса ExceptionGroup при отсутствии полей")
@pytest.mark.parametrize(
    "file_name, schema_name",
    [
        ("EmptyRequiredFields.json", "test_missing_fields_description"),
        ("EmptyRequiredFields.json", "test_missing_fields_type"),
        ("EmptyRequiredFields.json", "test_missing_two_fields"),
        ("EmptyRequiredFields.json", "test_missing_all_fields"),
    ],
)
def test_missing_required_field(file_name, schema_name, get_json_schema):
    allure.dynamic.title(f"Негативный тест: {schema_name}")

    json_data = get_json_schema(file_name, schema_name)

    with allure.step("Запуск валидации и ожидание ExceptionGroup"):
        with pytest.raises(ExceptionGroup) as excinfo:
            Schema.model_validate(json_data)

    with allure.step("Проверка наличия EmptyRequiredFields в группе"):
        assert excinfo.group_contains(EmptyRequiredFields)


@allure.epic("Валидация JSON схем")
@allure.feature("Структура Pydantic")
@allure.story("Проверка базовых ValidationError")
@pytest.mark.parametrize(
    "file_name, schema_name",
    [
        ("EmptyRequiredFields.json", "test_missing_description_level_1_field"),
        ("EmptyRequiredFields.json", "test_missing_parameters_fields"),
        ("EmptyRequiredFields.json", "test_missing_properties_fields"),
        ("EmptyRequiredFields.json", "test_missing_type_level_2_fields"),
    ],
)
def test_missing_other_fields(file_name, schema_name, get_json_schema):
    allure.dynamic.title(f"Структурная ошибка: {schema_name}")

    json_data = get_json_schema(file_name, schema_name)

    with allure.step("Ожидание ValidationError от Pydantic"):
        with pytest.raises(ValidationError):
            Schema.model_validate(json_data)


@allure.epic("Валидация JSON схем")
@allure.feature("Успешная валидация")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.parametrize(
    "file_name, schema_name, result",
    [
        (
            "EmptyRequiredFields.json",
            "test_all_required_fields",
            "test_all_required_fields",
        ),
        ("EmptyRequiredFields.json", "test_all_fields", "test_all_fields"),
    ],
)
def test_all_fields(file_name, schema_name, result, get_json_schema):
    allure.dynamic.title(f"Позитивный тест: {schema_name}")

    json_data = get_json_schema(file_name, schema_name)

    with allure.step("Валидация корректной схемы"):
        schema = Schema.model_validate(json_data)

    with allure.step("Проверка соответствия имени"):
        assert result == schema.name
