import json

import allure
import pytest
from pydantic import ValidationError

from src.exceptions.custom_exceptions import EmptyRequiredFields
from src.schema.json_schema import Schema


@allure.epic("Валидация JSON схем")
@allure.feature("Обязательные поля свойств")
@allure.story("Проверка кастомных исключений (EmptyRequiredFields)")
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
    allure.dynamic.title(f"Логическая ошибка: {schema_name}")
    allure.dynamic.description(
        "Тест проверяет, что модель выбрасывает ExceptionGroup при отсутствии обязательных полей в свойствах."
    )

    json_data = get_json_schema(file_name, schema_name)

    allure.attach(
        json.dumps(json_data, indent=2, ensure_ascii=False),
        name="Входной JSON",
        attachment_type=allure.attachment_type.JSON,
    )

    with allure.step("Валидация схемы и перехват группы исключений"):
        with pytest.raises(ExceptionGroup) as excinfo:
            Schema.model_validate(json_data)

    with allure.step("Проверка наличия EmptyRequiredFields в ExceptionGroup"):
        # Вытаскиваем детали для отчета
        details = str(excinfo.value.subgroup(EmptyRequiredFields))
        allure.attach(
            details,
            name="Детали найденных пустых полей",
            attachment_type=allure.attachment_type.TEXT,
        )
        assert excinfo.group_contains(EmptyRequiredFields)


@allure.epic("Валидация JSON схем")
@allure.feature("Структура Pydantic")
@allure.story("Базовая валидация типов (ValidationError)")
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
    allure.dynamic.title(f"Нарушение схемы Pydantic: {schema_name}")

    json_data = get_json_schema(file_name, schema_name)

    with allure.step("Ожидание стандартного ValidationError от Pydantic"):
        with pytest.raises(ValidationError) as excinfo:
            Schema.model_validate(json_data)

        allure.attach(
            str(excinfo.value),
            name="Pydantic Error Details",
            attachment_type=allure.attachment_type.TEXT,
        )


@allure.epic("Валидация JSON схем")
@allure.feature("Успешная валидация")
@allure.story("Полные и корректные схемы")
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
    allure.dynamic.title(f"Успех: {schema_name}")

    json_data = get_json_schema(file_name, schema_name)

    with allure.step("Валидация корректной схемы (ожидаем успех)"):
        schema = Schema.model_validate(json_data)

    with allure.step(f"Проверка соответствия имени '{result}'"):
        assert result == schema.name
