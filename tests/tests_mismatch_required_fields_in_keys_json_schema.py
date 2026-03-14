import allure
import pytest

from src.exceptions.custom_exceptions import MismatchRequiredFieldsInKey
from src.schema.json_schema import Schema


@allure.epic("Валидация JSON схем")
@allure.feature("Рассинхрон Required и Properties")
@allure.story("Проверка MismatchRequiredFieldsInKey через ExceptionGroup")
@pytest.mark.parametrize(
    "file_name, schema_name",
    [
        ("MismatchRequiredFieldsInKey.json", "empty_properties_test"),
        ("MismatchRequiredFieldsInKey.json", "missing_multiple_definitions"),
        ("MismatchRequiredFieldsInKey.json", "typo_error_test"),
    ],
)
def test_mismatch_required_fields(file_name, schema_name, get_json_schema):
    allure.dynamic.title(f"Тест на рассинхрон: {schema_name}")

    json_data = get_json_schema(file_name, schema_name)

    with allure.step("Валидация и ожидание группы ошибок Mismatch"):
        with pytest.raises(ExceptionGroup) as excinfo:
            Schema.model_validate(json_data)

        assert excinfo.group_contains(MismatchRequiredFieldsInKey)


@allure.epic("Валидация JSON схем")
@allure.feature("Успешная валидация")
@pytest.mark.parametrize(
    "file_name, schema_name",
    [
        ("MismatchRequiredFieldsInKey.json", "get_weather"),
        ("MismatchRequiredFieldsInKey.json", "all_empty_test"),
        ("MismatchRequiredFieldsInKey.json", "valid_full_schema"),
    ],
)
def test_positive_schemas(file_name, schema_name, get_json_schema):
    allure.dynamic.title(f"Позитивный тест: {schema_name}")

    json_data = get_json_schema(file_name, schema_name)

    with allure.step(f"Валидация схемы {schema_name}"):
        schema = Schema.model_validate(json_data)
        assert schema.name == schema_name
