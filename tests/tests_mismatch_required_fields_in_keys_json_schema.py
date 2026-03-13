import json
from pathlib import Path

import allure
import pytest

from src.exceptions.custom_exceptions import MismatchRequiredFieldsInKey
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
@allure.feature("Рассинхрон Required и Properties")
@allure.story("Проверка MismatchRequiredFieldsInKey через ExceptionGroup")
@pytest.mark.parametrize(
    "file_name, schema_name",
    [
        ("MismatchRequiredFieldsInKey.json", "empty_properties_test"),
        ("MismatchRequiredFieldsInKey.json", "missing_multiple_definitions"),
        ("MismatchRequiredFieldsInKey.json", "typo_error_test"),
        # ("MismatchRequiredFieldsInKey.json", "get_weather"),
        # ("MismatchRequiredFieldsInKey.json", "all_empty_test"),
        # ("MismatchRequiredFieldsInKey.json", "valid_full_schema"),
    ],
)
def test_mismatch_required_fields(file_name, schema_name, get_json_schema):
    allure.dynamic.title(f"Тест на рассинхрон: {schema_name}")

    json_data = get_json_schema(file_name, schema_name)

    with allure.step("Валидация и ожидание группы ошибок Mismatch"):
        with pytest.raises(ExceptionGroup) as excinfo:
            Schema.model_validate(json_data)

        # Проверяем, что внутри группы именно наше исключение
        assert any(
            isinstance(e, MismatchRequiredFieldsInKey) for e in excinfo.value.exceptions
        ), f"Ожидалось MismatchRequiredFieldsInKey, но получено: {excinfo.value.exceptions}"


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
        # Эти схемы должны проходить без ошибок
        schema = Schema.model_validate(json_data)
        assert schema.name == schema_name
