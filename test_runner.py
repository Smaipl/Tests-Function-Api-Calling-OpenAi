import argparse
import json
import os
import traceback

import yaml 

from src.function_register import FunctionRegistry
from src.openrouter_client import OpenRouterClient
from src.reporter import LocalReporter, CIReporter


def run_tests_for_function(args, test_cases):
    results = {"details": []}

    # Регистрируем функцию
    FunctionRegistry.register_from_file(args.function, args.schema)

    client = OpenRouterClient()

    # Берём имя функции из схемы
    with open(args.schema, encoding="utf-8") as f:
        schema_name = json.load(f)["name"]

    schemas = [FunctionRegistry.get_schema(schema_name)]


    client = OpenRouterClient()


    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🔍 Тест {i}/{len(test_cases)}: '{test_case['query']}'")

        test_result = {
            "test_index": i,
            "query": test_case["query"],
            "description": test_case.get("description", ""),
        }

        try:
            response = client.call_with_functions(
                user_query=test_case["query"], function_schemas=schemas
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
                        execution_result = FunctionRegistry.execute(func_name, func_args)
                        execution_chain.append({"function": func_name, "result": execution_result})
                        print(f"⚙️ Результат {func_name}: {execution_result}")
                    except Exception as e:
                        execution_chain.append({"function": func_name, "result": f"Ошибка выполнения: {e}"})
                        print(f"❌ Ошибка выполнения {func_name}: {e}")

            elif function_call:
                func_name = function_call["name"]
                func_args = function_call["arguments"]
                print(f"➡️ Вызов: {func_name}({func_args})")
                try:
                    execution_result = FunctionRegistry.execute(func_name, func_args)
                    execution_chain.append({"function": func_name, "result": execution_result})
                    print(f"⚙️ Результат {func_name}: {execution_result}")
                except Exception as e:
                    execution_chain.append({"function": func_name, "result": f"Ошибка выполнения: {e}"})
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
    parser.add_argument("--tests", required=True, help="Путь к suite (JSON или YAML)")
    args = parser.parse_args()

    if not os.path.exists(args.tests):
        raise FileNotFoundError(f"Файл тестов '{args.tests}' не найден")

    # Определяем формат по расширению
    if args.tests.endswith(".yaml") or args.tests.endswith(".yml"):
        with open(args.tests, encoding="utf-8") as f:
            test_cases = yaml.safe_load(f)
    else:
        with open(args.tests, encoding="utf-8") as f:
            test_cases = json.load(f)

    results = run_tests_for_function(args, test_cases)

    if os.getenv("GITHUB_ACTIONS") == "true":
        CIReporter().report(results, "test_results.json")
    else:
        LocalReporter().report(results)



if __name__ == "__main__":
    main()
