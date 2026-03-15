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

# Убедись, что эти модули доступны в твоем проекте (src/schema/...)
from src.schema.json_schema import Schema
from src.schema.py_schema import FunctionSchema


def main():
    parser = argparse.ArgumentParser(description="Validator for AI Functions")

    # ИМЕНА АРГУМЕНТОВ ИЗМЕНЕНЫ НА func_path и schema_path (как в action.yml)
    parser.add_argument(
        "--func_path", required=True, help="Path to the Python function file"
    )
    parser.add_argument(
        "--schema_path", required=True, help="Path to the JSON schema file"
    )

    args = parser.parse_args()

    py_file = Path(args.func_path)
    json_file = Path(args.schema_path)

    if not py_file.exists():
        print(f"::error::Python file not found: {py_file}")
        sys.exit(1)

    if not json_file.exists():
        print(f"::error::Schema file not found: {json_file}")
        sys.exit(1)

    func_name = py_file.stem

    # Путь для результатов Allure (относительно текущей директории запуска)
    # Лучше использовать абсолютный путь или убедиться, что cwd правильный
    default_path = Path("./allure-results-functions")
    default_path.mkdir(exist_ok=True, parents=True)

    lifecycle = AllureLifecycle()
    lifecycle.add_reporter(AllureFileLogger(str(default_path)))

    test_uuid = str(uuid.uuid4())
    result = TestResult(
        uuid=test_uuid,
        fullName=f"validate_{func_name}",
        name=f"Проверка синхронизации: {func_name}",
    )
    result.start = int(time.time() * 1000)

    result.labels.extend(
        [
            Label(name=LabelType.EPIC, value="Валидация функций пользователя"),
            Label(name=LabelType.FEATURE, value=f"Функция: {func_name}"),
            Label(name=LabelType.STORY, value="Анализ синхронизации кода и схемы"),
        ]
    )

    source_code = ""
    schema_dict = {}

    try:
        # 1. Чтение и валидация схемы
        with open(json_file, encoding="utf-8") as f:
            schema_data = json.load(f)
            # Поддержка двух форматов: { "func_name": {...} } или просто {...}
            if isinstance(schema_data, dict) and func_name in schema_data:
                schema_dict = schema_data[func_name]
            else:
                schema_dict = schema_data

            schema = Schema.model_validate(schema_dict)

        # 2. Загрузка и анализ Python кода
        spec = spec_from_file_location(func_name, py_file.absolute())
        if spec is None or spec.loader is None:
            raise ImportError(f"Не удалось загрузить модуль из {py_file}")

        mod = module_from_spec(spec)
        spec.loader.exec_module(mod)

        if not hasattr(mod, func_name):
            raise AttributeError(
                f"Функция '{func_name}' не найдена в файле {py_file.name}"
            )

        func = getattr(mod, func_name)
        source_code = inspect.getsource(func)

        # 3. Основная проверка (твоя логика в FunctionSchema)
        FunctionSchema.model_validate(
            {
                "arguments": inspect.signature(func).parameters,
                "json_schema": schema,
                "source_code": source_code,
            }
        )

        result.status = Status.PASSED
        print(f"✅ {func_name}: Синхронизация успешна")

    except Exception as e:
        error_type = type(e).__name__
        result.status = Status.FAILED
        result.statusDetails = StatusDetails(message=f"[{error_type}] {str(e)}")
        result.labels.append(Label(name=LabelType.STORY, value=f"Ошибка: {error_type}"))

        # Прикрепляем данные к отчету только если они были успешно прочитаны до ошибки
        if schema_dict:
            lifecycle.attach_data(
                test_uuid,
                json.dumps(schema_dict, indent=2, ensure_ascii=False),
                "JSON Schema",
                AttachmentType.JSON,
            )
        if source_code:
            lifecycle.attach_data(
                test_uuid, source_code, "Python Source Code", AttachmentType.TEXT
            )

        print(f"::error file={py_file}::[{error_type}] {e}")
        # Не делаем sys.exit(1) здесь, так как нам нужно записать результат теста в Allure
        # Выход будет выполнен в блоке finally если статус FAILED

    finally:
        result.stop = int(time.time() * 1000)
        lifecycle.write_test_result(result)

        if result.status == Status.FAILED:
            sys.exit(1)


if __name__ == "__main__":
    main()
