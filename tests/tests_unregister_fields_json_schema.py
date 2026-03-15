import json

import allure
import pytest

from src.exceptions.custom_exceptions import UnregisterField
from src.schema.json_schema import Schema


@allure.epic("Валидация JSON схем")
@allure.feature("Лишние поля (UnregisterField)")
@allure.story("Одиночные лишние ключи")
@pytest.mark.parametrize(
    "file_name, schema_name",
    [
        ("UnregisterField.json", "test_extra_root_field"),
        ("UnregisterField.json", "test_extra_parameters_field"),
        ("UnregisterField.json", "test_extra_property_field"),
    ],
)
def test_single_extra_field_on_different_levels(
    file_name, schema_name, get_json_schema
):
    allure.dynamic.title(f"Одиночный лишний ключ: {schema_name}")
    allure.dynamic.description(
        "Проверка одного лишнего ключа на конкретном уровне вложенности."
    )

    json_data = get_json_schema(file_name, schema_name)
    allure.attach(
        json.dumps(json_data, indent=2), "Тестируемый JSON", allure.attachment_type.JSON
    )

    with allure.step("Валидация и поиск UnregisterField"):
        with pytest.raises(ExceptionGroup) as excinfo:
            Schema.model_validate(json_data)

        unregister_errors = [
            e for e in excinfo.value.exceptions if isinstance(e, UnregisterField)
        ]

        found_field = unregister_errors[0].fields[0]
        allure.attach(
            f"Найдено лишнее поле: {found_field}",
            name="Результат поиска",
            attachment_type=allure.attachment_type.TEXT,
        )

        assert len(unregister_errors) == 1
        assert len(unregister_errors[0].fields) == 1


@allure.epic("Валидация JSON схем")
@allure.feature("Лишние поля (UnregisterField)")
@allure.story("Комбинации лишних ключей")
@pytest.mark.parametrize(
    "file_name, schema_name, expected_obj_count",
    [
        ("UnregisterField.json", "test_extra_root_and_parameters", 2),
        ("UnregisterField.json", "test_extra_root_and_property", 2),
        ("UnregisterField.json", "test_extra_parameters_and_property", 2),
        ("UnregisterField.json", "test_extra_fields_on_all_levels", 3),
    ],
)
def test_combined_extra_fields_on_levels(
    file_name, schema_name, expected_obj_count, get_json_schema
):
    allure.dynamic.title(f"Комбо-проверка ({expected_obj_count} уровня): {schema_name}")

    json_data = get_json_schema(file_name, schema_name)

    with allure.step(f"Ожидание ошибок на {expected_obj_count} уровнях"):
        with pytest.raises(ExceptionGroup) as excinfo:
            Schema.model_validate(json_data)

        unregister_errors = [
            e for e in excinfo.value.exceptions if isinstance(e, UnregisterField)
        ]

        all_fields = {
            f"Level {i + 1}": e.fields for i, e in enumerate(unregister_errors)
        }
        allure.attach(
            json.dumps(all_fields, indent=2),
            name="Список всех лишних полей",
            attachment_type=allure.attachment_type.JSON,
        )

        assert len(unregister_errors) == expected_obj_count


@allure.epic("Валидация JSON схем")
@allure.feature("Лишние поля (UnregisterField)")
@allure.story("Массовые лишние ключи")
@pytest.mark.parametrize(
    "file_name, schema_name, expected_total_keys",
    [
        ("UnregisterField.json", "test_three_extra_at_root", 3),
        ("UnregisterField.json", "test_three_extra_in_parameters", 3),
        ("UnregisterField.json", "test_three_extra_in_property", 3),
        ("UnregisterField.json", "test_triple_extra_on_all_levels", 9),
    ],
)
def test_triple_extra_fields(
    file_name, schema_name, expected_total_keys, get_json_schema
):
    allure.dynamic.title(f"Массовый тест: поиск {expected_total_keys} ключей")

    json_data = get_json_schema(file_name, schema_name)

    with allure.step("Валидация и агрегация всех лишних полей"):
        with pytest.raises(ExceptionGroup) as excinfo:
            Schema.model_validate(json_data)

        unregister_errors = [
            e for e in excinfo.value.exceptions if isinstance(e, UnregisterField)
        ]
        total_found = sum(len(e.fields) for e in unregister_errors)

        all_names = [field for e in unregister_errors for field in e.fields]
        allure.attach(
            ", ".join(all_names),
            name="Найденные ключи",
            attachment_type=allure.attachment_type.TEXT,
        )

        assert total_found == expected_total_keys
        allure.dynamic.parameter("total_keys_found", total_found)


@allure.epic("Валидация JSON схем")
@allure.feature("Успешная валидация")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.parametrize(
    "file_name, schema_name, result",
    [
        (
            "UnregisterField.json",
            "test_all_required_fields",
            "test_all_required_fields",
        ),
        ("UnregisterField.json", "test_all_fields", "test_all_fields"),
    ],
)
def test_all_fields(file_name, schema_name, result, get_json_schema):
    allure.dynamic.title(f"Чистая схема: {schema_name}")

    json_data = get_json_schema(file_name, schema_name)

    with allure.step("Валидация (лишних полей быть не должно)"):
        schema = Schema.model_validate(json_data)

    with allure.step("Проверка целостности данных"):
        assert result == schema.name
