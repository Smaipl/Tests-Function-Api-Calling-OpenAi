import json

import allure
import pytest

from src.exceptions.custom_exceptions import (
    TypeMismatchJsonToPython,
)
from src.schema.json_schema import Schema


@allure.epic("Валидация JSON схем")
@allure.feature("Типизация свойств")
@allure.story("Конфликты типов JSON -> Python")
@pytest.mark.parametrize(
    "file_name, schema_name, expected_type",
    [
        ("TypeMismatchJsonToPython.json", "test_type_mismatch_date", "date"),
        ("TypeMismatchJsonToPython.json", "test_type_mismatch_any", "any"),
    ],
)
def test_type_mismatch_error(file_name, schema_name, expected_type, get_json_schema):
    allure.dynamic.title(f"Ошибка типа: неподдерживаемый '{expected_type}'")
    allure.dynamic.parameter("unsupported_type", expected_type)

    json_data = get_json_schema(file_name, schema_name)

    allure.attach(
        json.dumps(json_data, indent=2, ensure_ascii=False),
        name=f"JSON с типом {expected_type}",
        attachment_type=allure.attachment_type.JSON,
    )

    with allure.step(f"Валидация схемы '{schema_name}' и ожидание TypeMismatch"):
        with pytest.raises(ExceptionGroup) as excinfo:
            Schema.model_validate(json_data)

    with allure.step("Проверка наличия TypeMismatchJsonToPython в группе"):
        type_errors = excinfo.value.subgroup(TypeMismatchJsonToPython)
        if type_errors:
            allure.attach(
                str(type_errors),
                name="Детали конфликта типов",
                attachment_type=allure.attachment_type.TEXT,
            )

        assert excinfo.group_contains(TypeMismatchJsonToPython)


@allure.epic("Валидация JSON схем")
@allure.feature("Типизация свойств")
@allure.story("Успешный маппинг стандартных типов")
@pytest.mark.parametrize(
    "file_name, schema_name",
    [
        ("TypeMismatchJsonToPython.json", "test_sync_type_object"),
        ("TypeMismatchJsonToPython.json", "test_sync_type_array"),
        ("TypeMismatchJsonToPython.json", "test_sync_type_number"),
        ("TypeMismatchJsonToPython.json", "test_sync_type_boolean"),
    ],
)
def test_type_sync_success(file_name, schema_name, get_json_schema):
    data_type = schema_name.split("_")[-1]
    allure.dynamic.title(f"Успешный маппинг типа: {data_type.upper()}")

    json_data = get_json_schema(file_name, schema_name)

    with allure.step(f"Проверка маппинга стандартного типа '{data_type}'"):
        schema_obj = Schema.model_validate(json_data)

    with allure.step("Финальная проверка целостности объекта"):
        assert schema_obj.name == schema_name
        assert schema_obj.parameters is not None
