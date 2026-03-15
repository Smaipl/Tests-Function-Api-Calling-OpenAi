import json

import allure
import pytest

from src.exceptions.custom_exceptions import MismatchRequiredFieldsInKey
from src.schema.json_schema import Schema


@allure.epic("Валидация JSON схем")
@allure.feature("Целостность структуры (Required/Properties)")
@allure.story("Обнаружение рассинхрона полей")
@pytest.mark.parametrize(
    "file_name, schema_name",
    [
        ("MismatchRequiredFieldsInKey.json", "empty_properties_test"),
        ("MismatchRequiredFieldsInKey.json", "missing_multiple_definitions"),
        ("MismatchRequiredFieldsInKey.json", "typo_error_test"),
    ],
)
def test_mismatch_required_fields(file_name, schema_name, get_json_schema):
    allure.dynamic.title(f"Критический рассинхрон: {schema_name}")
    allure.dynamic.parameter("schema_source", file_name)

    json_data = get_json_schema(file_name, schema_name)

    allure.attach(
        json.dumps(json_data, indent=2, ensure_ascii=False),
        name=f"JSON Data: {schema_name}",
        attachment_type=allure.attachment_type.JSON,
    )

    with allure.step("Валидация Pydantic-модели и поиск ExceptionGroup"):
        with pytest.raises(ExceptionGroup) as excinfo:
            Schema.model_validate(json_data)

        mismatches = excinfo.value.subgroup(MismatchRequiredFieldsInKey)
        if mismatches:
            allure.attach(
                str(mismatches),
                name="Найденные несоответствия",
                attachment_type=allure.attachment_type.TEXT,
            )

        assert excinfo.group_contains(MismatchRequiredFieldsInKey)


@allure.epic("Валидация JSON схем")
@allure.feature("Успешная валидация")
@allure.story("Корректные схемы без ошибок структуры")
@pytest.mark.parametrize(
    "file_name, schema_name",
    [
        ("MismatchRequiredFieldsInKey.json", "get_weather"),
        ("MismatchRequiredFieldsInKey.json", "all_empty_test"),
        ("MismatchRequiredFieldsInKey.json", "valid_full_schema"),
    ],
)
def test_positive_schemas(file_name, schema_name, get_json_schema):
    allure.dynamic.title(f"Валидная схема: {schema_name}")

    json_data = get_json_schema(file_name, schema_name)

    with allure.step(f"Проверка схемы '{schema_name}' через модель Schema"):
        schema = Schema.model_validate(json_data)

    with allure.step("Проверка соответствия имени"):
        assert (
            schema.name == schema_name
        ), f"Ожидали {schema_name}, получили {schema.name}"
