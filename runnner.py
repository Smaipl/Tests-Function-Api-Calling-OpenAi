import argparse
import json
import os
import re
import traceback

import yaml
from src.function_register import FunctionRegistry
from src.reporter import CIReporter, LocalReporter

from src.openrouter_client import OpenRouterClient


def substitute_placeholders(text: str) -> str:
    """
    Заменяет маркеры вида <#secret.KEY> на значения из переменных окружения.
    Если переменной нет, оставляет маркер как есть.
    """
    pattern = r"<#secret\.([A-Z0-9_]+)>"

    def replacer(match):
        key = match.group(1)
        return os.getenv(key, match.group(0))

    return re.sub(pattern, replacer, text)


def run_tests_for_function(args, test_cases):
    results = {"details": []}
    client = OpenRouterClient()

    # Регистрируем функцию
    func_reg: FunctionInfo = FunctionRegistry.register(args.function, args.schema)

    schemas = func_reg.schema

    for i, test_case in enumerate(test_cases, 1):
        # Подставляем секреты в запрос
        query = substitute_placeholders(test_case["query"])

        print(f"\n🔍 Тест {i}/{len(test_cases)}: '{query}'")

        test_result = {
            "test_index": i,
            "query": query,
            "description": test_case.get("description", ""),
        }

        try:
            response = client.call_with_functions(
                user_query=query, function_schemas=schemas
            )
            test_result["response"] = response

            message = response.get("message", {})
            tool_calls = message.get("tool_calls") or []
            function_call = message.get("function_call")

            execution_chain = []

            if tool_calls:
                for idx, tc in enumerate(tool_calls, 1):
                    func_name = tc["function"]["name"]
                    func_args = tc["function"]["arguments"]
                    print(f"➡️ Вызов {idx}: {func_name}({func_args})")
                    try:
                        execution_result = FunctionRegistry.execute(
                            func_name, func_args
                        )
                        execution_chain.append(
                            {"function": func_name, "result": execution_result}
                        )
                        print(f"⚙️ Результат {func_name}: {execution_result}")
                    except Exception as e:
                        execution_chain.append(
                            {"function": func_name, "result": f"Ошибка выполнения: {e}"}
                        )
                        print(f"❌ Ошибка выполнения {func_name}: {e}")

            elif function_call:
                func_name = function_call["name"]
                func_args = function_call["arguments"]
                print(f"➡️ Вызов: {func_name}({func_args})")
                try:
                    execution_result = FunctionRegistry.execute(func_name, func_args)
                    execution_chain.append(
                        {"function": func_name, "result": execution_result}
                    )
                    print(f"⚙️ Результат {func_name}: {execution_result}")
                except Exception as e:
                    execution_chain.append(
                        {"function": func_name, "result": f"Ошибка выполнения: {e}"}
                    )
                    print(f"❌ Ошибка выполнения {func_name}: {e}")

            test_result["execution_chain"] = execution_chain
            results["details"].append(test_result)

        except Exception as e:
            test_result["status"] = "error"
            test_result["error"] = str(e)
            test_result["traceback"] = traceback.format_exc()
            print(f"🔥 Исключение ({type(e).__name__}): {e}")
            print(test_result["traceback"])
            results["details"].append(test_result)

    return results


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--function", required=True, help="Путь к файлу функции (.py)")
    parser.add_argument("--schema", required=True, help="Путь к файлу схемы (.json)")
    parser.add_argument("--suite", required=True, help="Путь к suite (JSON или YAML)")
    args = parser.parse_args()

    if not os.path.exists(args.suite):
        raise FileNotFoundError(f"Файл тестов '{args.suite}' не найден")

    # Определяем формат по расширению
    if args.suite.endswith(".yaml") or args.suite.endswith(".yml"):
        with open(args.suite, encoding="utf-8") as f:
            test_cases = yaml.safe_load(f)
    else:
        with open(args.suite, encoding="utf-8") as f:
            test_cases = json.load(f)

    results = run_tests_for_function(args, test_cases)

    if os.getenv("GITHUB_ACTIONS") == "true":
        CIReporter().report(results, "test_results.json")
    else:
        LocalReporter().report(results)


if __name__ == "__main__":
    main()
