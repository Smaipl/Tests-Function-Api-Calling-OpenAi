import argparse
import inspect
import json
import sys
import time
import uuid
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

from allure_commons.lifecycle import AllureLifecycle
from allure_commons.logger import AllureFileLogger
from allure_commons.model2 import Label, Status, StatusDetails, TestResult
from allure_commons.types import AttachmentType, LabelType

from src.schema.json_schema import Schema
from src.schema.py_schema import FunctionSchema


def main():
    parser = argparse.ArgumentParser()
    # Только те два аргумента, что приходят из action.yml
    parser.add_argument("--func_path", required=True)
    parser.add_argument("--schema_path", required=True)
    args = parser.parse_args()

    py_file = Path(args.func_path)
    json_file = Path(args.schema_path)
    func_name = py_file.stem

    # Твой путь по умолчанию
    default_path = "./allure-results-functions"
    Path(default_path).mkdir(exist_ok=True, parents=True)

    lifecycle = AllureLifecycle()
    lifecycle.add_reporter(AllureFileLogger(default_path))

    test_uuid = str(uuid.uuid4())
    result = TestResult(
        uuid=test_uuid, fullName=f"validate_{func_name}", name=f"Проверка: {func_name}"
    )
    result.start = int(time.time() * 1000)

    result.labels.extend(
        [
            Label(name=LabelType.EPIC, value="Валидация функций пользователя"),
            Label(name=LabelType.FEATURE, value=f"Функция: {func_name}"),
            Label(name=LabelType.STORY, value="Анализ синхронизации"),
        ]
    )

    try:
        with open(json_file, encoding="utf-8") as f:
            schema_data = json.load(f)
            schema_dict = (
                schema_data.get(func_name, schema_data)
                if isinstance(schema_data, dict)
                else schema_data
            )
            schema = Schema.model_validate(schema_dict)

        spec = spec_from_file_location(func_name, py_file.absolute())
        mod = module_from_spec(spec)
        spec.loader.exec_module(mod)
        func = getattr(mod, func_name)
        source_code = inspect.getsource(func)

        FunctionSchema.model_validate(
            {
                "arguments": inspect.signature(func).parameters,
                "json_schema": schema,
                "source_code": source_code,
            }
        )

        result.status = Status.PASSED
        print(f"✅ {func_name}: OK")

    except Exception as e:
        error_type = type(e).__name__
        result.status = Status.FAILED
        result.statusDetails = StatusDetails(message=f"[{error_type}] {str(e)}")
        result.labels.append(Label(name=LabelType.STORY, value=f"Ошибка: {error_type}"))

        lifecycle.attach_data(
            test_uuid,
            json.dumps(schema_dict if "schema_dict" in locals() else {}, indent=2),
            "JSON Schema",
            AttachmentType.JSON,
        )
        if "source_code" in locals():
            lifecycle.attach_data(
                test_uuid, source_code, "Python Source", AttachmentType.TEXT
            )

        print(f"::error file={py_file}::[{error_type}] {e}")

    finally:
        result.stop = int(time.time() * 1000)
        lifecycle.write_test_result(result)
        if result.status == Status.FAILED:
            sys.exit(1)


if __name__ == "__main__":
    main()
