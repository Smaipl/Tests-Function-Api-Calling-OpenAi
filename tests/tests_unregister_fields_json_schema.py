import allure
import pytest

from src.exceptions.custom_exceptions import UnregisterField
from src.schema.json_schema import Schema


@allure.epic("Валидация JSON схем")
@allure.feature("Лишние поля (UnregisterField)")
@allure.story("Одиночные лишние ключи на разных уровнях вложенности")
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

    json_data = get_json_schema(file_name, schema_name)

    with allure.step("Валидация и проверка ExceptionGroup"):
        with pytest.raises(ExceptionGroup) as excinfo:
            Schema.model_validate(json_data)

        unregister_errors = [
            e for e in excinfo.value.exceptions if isinstance(e, UnregisterField)
        ]
        assert len(unregister_errors) == 1
        assert len(unregister_errors[0].fields) == 1


@allure.epic("Валидация JSON схем")
@allure.feature("Лишние поля (UnregisterField)")
@allure.story("Комбинации лишних ключей на разных уровнях")
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
    allure.dynamic.title(f"Комбо уровней: {schema_name}")

    json_data = get_json_schema(file_name, schema_name)

    with allure.step(f"Ожидание {expected_obj_count} объектов UnregisterField"):
        with pytest.raises(ExceptionGroup) as excinfo:
            Schema.model_validate(json_data)

        unregister_errors = [
            e for e in excinfo.value.exceptions if isinstance(e, UnregisterField)
        ]
        assert len(unregister_errors) == expected_obj_count


@allure.epic("Валидация JSON схем")
@allure.feature("Лишние поля (UnregisterField)")
@allure.story("Массовые лишние ключи (Triple Extra)")
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
    allure.dynamic.title(f"Массовая проверка (9 ключей): {schema_name}")

    json_data = get_json_schema(file_name, schema_name)

    with allure.step("Валидация и подсчет общего количества лишних полей"):
        with pytest.raises(ExceptionGroup) as excinfo:
            Schema.model_validate(json_data)

        unregister_errors = [
            e for e in excinfo.value.exceptions if isinstance(e, UnregisterField)
        ]
        total_found = sum(len(e.fields) for e in unregister_errors)

        assert total_found == expected_total_keys
        allure.attach(str(total_found), name="Total keys found")


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
    allure.dynamic.title(f"Позитивный тест: {schema_name}")

    json_data = get_json_schema(file_name, schema_name)

    with allure.step("Валидация корректной схемы"):
        schema = Schema.model_validate(json_data)

    with allure.step("Проверка соответствия имени"):
        assert result == schema.name
