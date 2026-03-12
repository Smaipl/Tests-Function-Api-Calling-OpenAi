import json
from pathlib import Path

import allure
import pytest
from pydantic import ValidationError

from src.exceptions.custom_exceptions import EmptyRequiredFields
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


@allure.epic("Валидация JSON схем")
@allure.feature("Обязательные поля свойств")
@allure.story("Проверка выброса ExceptionGroup при отсутствии полей")
@pytest.mark.parametrize(
    "file_name, schema_name",
    [
        ("EmptyRequiredFields.json", "test_missing_fields_default"),
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
