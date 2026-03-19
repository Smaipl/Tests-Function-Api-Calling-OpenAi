import asyncio
import inspect
import json
import os
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

import allure
import pytest
import yaml
from openai import AsyncOpenAI

from src.ai_model_client import ModelInterface
from src.schema.client_schema import ClientModel
from src.schema.json_schema import Schema
from src.schema.py_schema import FunctionSchema


def load_yaml_conf(file_path):
    with open(file_path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def get_function_from_py(py_file: Path, func_name: str):
    spec = spec_from_file_location(func_name, py_file.absolute())
    if spec is None or spec.loader is None:
        pytest.fail(f"❌ Не удалось загрузить модуль из {py_file}")
    mod = module_from_spec(spec)
    spec.loader.exec_module(mod)
    if not hasattr(mod, func_name):
        pytest.fail(f"❌ Функция '{func_name}' не найдена в файле!")
    return getattr(mod, func_name)


@allure.epic("Валидация функций")
@allure.feature("Синхронизация")
@allure.story("Анализ кода и JSON схемы")
@allure.severity(allure.severity_level.CRITICAL)
def test_local_function_sync():
    func_path = os.environ.get("INPUT_FUNC_PATH")
    schema_path = os.environ.get("INPUT_SCHEMA_PATH")

    if not func_path or not schema_path:
        pytest.fail("Проверьте переменные INPUT_FUNC_PATH и INPUT_SCHEMA_PATH")

    py_file = Path(func_path)
    json_file = Path(schema_path)
    func_name = py_file.stem

    with allure.step(f"Загрузка JSON схемы: {json_file.name}"):
        with open(json_file, encoding="utf-8") as f:
            data = json.load(f)
            schema_dict = (
                data[func_name]
                if isinstance(data, dict) and func_name in data
                else data
            )
            schema = Schema.model_validate(schema_dict)
            allure.attach(
                json.dumps(schema_dict, indent=2),
                "Schema JSON",
                allure.attachment_type.JSON,
            )

    with allure.step(f"Инспекция Python функции: {func_name}"):
        func = get_function_from_py(py_file, func_name)
        source_code = inspect.getsource(func)
        sig = inspect.signature(func)
        allure.attach(source_code, "Source Code", allure.attachment_type.TEXT)

    with allure.step("Проверка соответствия аргументов коду"):
        try:
            FunctionSchema.model_validate(
                {
                    "arguments": sig.parameters,
                    "json_schema": schema,
                    "source_code": source_code,
                }
            )
            allure.dynamic.description("Синхронизация кода и схемы подтверждена ✅")
        except Exception as e:
            allure.attach(str(e), "Validation Error", allure.attachment_type.TEXT)
            raise


@pytest.mark.asyncio
@allure.epic("Валидация функций")
@allure.feature("Инференс")
@allure.story("Вызов OpenAI API")
@allure.severity(allure.severity_level.NORMAL)
async def test_ai_inference():
    conf_path = os.environ.get("INPUT_CONFIG_PATH")
    schema_path = os.environ.get("INPUT_SCHEMA_PATH")

    with open(schema_path, encoding="utf-8") as f:
        s_data = json.load(f)
        s_dict = list(s_data.values())[0] if isinstance(s_data, dict) else s_data
        schema = Schema.model_validate(s_dict)

    raw_conf = load_yaml_conf(conf_path)
    root_config = ClientModel.model_validate(raw_conf)

    router = root_config.aggregator
    model_settings = router.model_settings
    sem = asyncio.Semaphore(model_settings.semaphore)

    allure.dynamic.parameter("Model", model_settings.model_id)

    async with AsyncOpenAI(
        api_key=router.api_key.get_secret_value(),
        base_url=str(router.base_url),
        timeout=router.timeout,
        max_retries=router.max_retries,
    ) as ai:

        async def sem_task(q):
            async with sem:
                return await ModelInterface.call_with_functions(
                    ai, root_config, router, model_settings, q, schema
                )

        with allure.step(f"Запуск {len(root_config.queries)} запросов к AI"):
            tasks = [sem_task(query) for query in root_config.queries]
            results = await asyncio.gather(*tasks, return_exceptions=True)

    with allure.step("Анализ результатов и расхода токенов"):
        allure.attach(
            root_config.usage_report, "Usage Stats", allure.attachment_type.TEXT
        )

        allure.dynamic.parameter("Total Tokens", root_config._total_token)
        allure.dynamic.parameter("Prompt Tokens", root_config._request_token)

        errors = []
        for i, res in enumerate(results):
            name = f"Query {i + 1}: {root_config.queries[i][:30]}..."
            if isinstance(res, Exception):
                errors.append(res)
                allure.attach(
                    str(res),
                    name=f"❌ {name}",
                    attachment_type=allure.attachment_type.TEXT,
                )
            else:
                content = (
                    res.model_dump_json(indent=2)
                    if hasattr(res, "model_dump_json")
                    else str(res)
                )
                allure.attach(
                    content,
                    name=f"✅ {name}",
                    attachment_type=allure.attachment_type.JSON,
                )

        if errors:
            pytest.fail(f"Тест провален: {len(errors)} запросов завершились ошибкой")
