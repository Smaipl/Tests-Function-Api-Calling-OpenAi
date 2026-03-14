import inspect
import json
import textwrap
import types
from pathlib import Path

import allure
import pytest

NAME = "function_name"


def get_mock_function(name: str, body: str, *args):
    args_str = ", ".join(map(str, args))

    clean_body = textwrap.dedent(body).strip()
    indented_body = textwrap.indent(clean_body, "    ")
    source = f"def {name}({args_str}):\n{indented_body}"

    func_module: inspect.CodeType = compile(source, "<string>", "exec")
    func_code: inspect.CodeType = [
        c for c in func_module.co_consts if isinstance(c, types.CodeType)
    ][0]

    func = types.FunctionType(func_code, globals(), name)
    func.__source__ = source

    return func


@pytest.fixture
def get_json_schema():
    def _loader(file_name: str, schema_name: str):
        folder = Path("src/mock")

        file_path = folder / file_name

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
