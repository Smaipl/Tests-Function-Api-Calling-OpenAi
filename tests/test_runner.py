import argparse
import json
import os
import traceback

from src.function_register import import_all_functions, registry
from src.openrouter_client import OpenRouterClient


def save_test_results(results, function_name: str):
    path = f"test_results/tests_{function_name}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    return path


def run_tests_for_function(args, test_cases):
    project_root = os.path.dirname(os.path.dirname(__file__))  # корень проекта
    import_all_functions(project_root)

    client = OpenRouterClient()
    results = {"passed": 0, "failed": 0, "errors": 0, "details": []}

    # собираем схемы для всех функций
    schemas = []
    for func in args.function:
        try:
            schemas.append(registry.get_schema(func))
            print(f"📥 Импортирована схема функции: {func}")
        except KeyError:
            print(f"❌ Функция '{func}' не найдена в реестре")

    for i, test_case in enumerate(test_cases, 1):
        query_preview = (
            test_case["query"][:50] + "..."
            if len(test_case["query"]) > 50
            else test_case["query"]
        )
        print(f"\n🔍 Тест {i}/{len(test_cases)}: '{query_preview}'")

        test_result = {
            "test_index": i,
            "query": test_case["query"],
            "description": test_case.get("description", ""),
            "expected_function": test_case.get("expected_function"),
            "expected_arguments": test_case.get("expected_arguments", {}),
        }

        try:
            # Вызов модели с несколькими схемами
            response = client.call_with_functions(
                user_query=test_case["query"], function_schemas=schemas
            )
            test_result["response"] = response

            if "error" in response:
                test_result["status"] = "error"
                test_result["error"] = response["error"]
                results["errors"] += 1
                print(f"❌ Ошибка API: {response['error']}")
            else:
                message = response.get("message", {})
                tool_calls = message.get("tool_calls")
                function_call = message.get("function_call")  # fallback

                if not tool_calls and not function_call:
                    test_result["status"] = "failed"
                    test_result["reason"] = "Функция не вызвана"
                    results["failed"] += 1
                    print("❌ Функция не вызвана")
                    results["details"].append(test_result)
                    continue

                # Обработка цепочки вызовов
                actual_chain = []
                execution_chain = []

                if tool_calls and len(tool_calls) > 0:
                    for idx, tc in enumerate(tool_calls, 1):
                        func_name = tc["function"]["name"]
                        func_args = tc["function"]["arguments"]

                        print(f"➡️ Вызов {idx}: {func_name}({func_args})")
                        actual_chain.append({"function": func_name, "arguments": func_args})

                        try:
                            execution_result = registry.execute(func_name, func_args)
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
                    actual_chain.append({"function": func_name, "arguments": func_args})
                    try:
                        execution_result = registry.execute(func_name, func_args)
                        execution_chain.append(
                            {"function": func_name, "result": execution_result}
                        )
                        print(f"⚙️ Результат {func_name}: {execution_result}")
                    except Exception as e:
                        execution_chain.append(
                            {"function": func_name, "result": f"Ошибка выполнения: {e}"}
                        )
                        print(f"❌ Ошибка выполнения {func_name}: {e}")

                test_result["actual_chain"] = actual_chain
                test_result["execution_chain"] = execution_chain

                # Проверка ожидаемой первой функции
                expected_func = test_case.get("expected_function")
                if expected_func and (
                    len(actual_chain) == 0 or actual_chain[0]["function"] != expected_func
                ):
                    test_result["status"] = "failed"
                    test_result["reason"] = (
                        f"Ожидалась функция '{expected_func}', вызвана '{actual_chain[0]['function'] if actual_chain else 'ничего'}'"
                    )
                    results["failed"] += 1
                    print(
                        f"❌ Ожидалась '{expected_func}', вызвана '{actual_chain[0]['function'] if actual_chain else 'ничего'}'"
                    )
                else:
                    test_result["status"] = "passed"
                    results["passed"] += 1
                    print(f"✅ Первый вызов совпал: {expected_func}")

                # Проверка next_function (если задана в suite)
                expected_next = test_case.get("next_function")
                if expected_next:
                    if (
                        len(actual_chain) < 2
                        or actual_chain[1]["function"] != expected_next["name"]
                    ):
                        test_result["status"] = "failed"
                        test_result["reason"] = (
                            f"Ожидалась последовательность: {expected_next['name']}, "
                            f"но вызвано {actual_chain[1]['function'] if len(actual_chain) > 1 else 'ничего'}"
                        )
                        results["failed"] += 1
                        print("❌ Второй вызов не совпал")
                    else:
                        print(f"✅ Второй вызов совпал: {expected_next['name']}")

            results["details"].append(test_result)

        except Exception as e:
            test_result["status"] = "error"
            test_result["error"] = str(e)
            test_result["traceback"] = traceback.format_exc()
            results["errors"] += 1
            print(f"🔥 Исключение ({type(e).__name__}): {e}")
            print(test_result["traceback"])
            results["details"].append(test_result)

    return results


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--function", nargs="+", help="Имена функций для тестирования")
    parser.add_argument("--tests", required=True, help="Путь к suite JSON")
    args = parser.parse_args()

    tests_path = args.tests
    if not os.path.exists(tests_path):
        alt_path = os.path.join("tests", "suites", args.tests)
        if os.path.exists(alt_path):
            tests_path = alt_path
        else:
            raise FileNotFoundError(f"Файл тестов '{args.tests}' не найден")

    with open(tests_path, encoding="utf-8") as f:
        test_cases = json.load(f)

    results = run_tests_for_function(args, test_cases)

    if results:
        tests_file = save_test_results(results, "_".join(args.function))
        print(f"\n💾 Результаты тестов сохранены в: {tests_file}")


if __name__ == "__main__":
    main()
