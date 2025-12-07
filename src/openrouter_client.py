"""
Обновленный клиент OpenRouter с поддержкой нового формата Tools
"""

import os
import json
import hashlib
from typing import Dict, Any, List, Optional, Union
from openai import OpenAI
from functools import lru_cache

class OpenRouterClient:
    """Клиент для работы с OpenRouter API с поддержкой tools"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://openrouter.ai/api/v1",
        model: str = "openai/gpt-3.5-turbo"
    ):
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY не установлен")

        self.client = OpenAI(
            base_url=base_url,
            api_key=self.api_key
        )
        self.model = model

    def convert_functions_to_tools(self, functions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Конвертирует старый формат functions в новый формат tools

        Старый формат:
        {
            "name": "function_name",
            "description": "...",
            "parameters": {...}
        }

        Новый формат:
        {
            "type": "function",
            "function": {
                "name": "function_name",
                "description": "...",
                "parameters": {...}
            }
        }
        """
        tools = []
        for func in functions:
            tools.append({
                "type": "function",
                "function": func
            })
        return tools

    @lru_cache(maxsize=100)
    def _get_cache_key(self, user_query: str, schemas_str: str) -> str:
        """Генерирует ключ кеша для запроса"""
        content = f"{user_query}::{schemas_str}::{self.model}"
        return hashlib.md5(content.encode()).hexdigest()

    def call_with_functions(
        self,
        user_query: str,
        function_schemas: List[Dict[str, Any]],
        use_cache: bool = True,
        cache_dir: str = "test_snapshots",
        temperature: float = 0.1,
        max_tokens: int = 500
    ) -> Dict[str, Any]:
        """
        Вызывает модель с НОВЫМ форматом tools (вместо устаревших functions)
        """
        # Конвертируем функции в tools
        tools = self.convert_functions_to_tools(function_schemas)

        # Создаем уникальный ключ для кеширования
        schemas_str = json.dumps(function_schemas, sort_keys=True)
        cache_key = self._get_cache_key(user_query, schemas_str)
        cache_file = os.path.join(cache_dir, f"{cache_key}.json")

        # Пытаемся загрузить из кеша
        if use_cache and os.path.exists(cache_file):
            with open(cache_file, 'r', encoding='utf-8') as f:
                print(f"📂 Загружено из кеша: {cache_file}")
                return json.load(f)

        try:
            # Реальный вызов API с новым форматом tools
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "Ты помогающий ассистент. Используй предоставленные инструменты (tools) для выполнения задач."
                    },
                    {
                        "role": "user",
                        "content": user_query
                    }
                ],
                tools=tools,  # ВМЕСТО functions
                tool_choice="auto",  # ВМЕСТО function_call
                temperature=temperature,
                max_tokens=max_tokens
            )

            message = response.choices[0].message

            result = {
                "user_query": user_query,
                "model": self.model,
                "timestamp": response.created,
                "message": {
                    "content": message.content,
                    "tool_calls": None  # ВМЕСТО function_call
                }
            }

            # Обрабатываем новый формат tool_calls
            if hasattr(message, 'tool_calls') and message.tool_calls:
                tool_calls = []
                for tool_call in message.tool_calls:
                    if tool_call.type == "function":
                        tool_calls.append({
                            "id": tool_call.id,
                            "type": tool_call.type,
                            "function": {
                                "name": tool_call.function.name,
                                "arguments": json.loads(tool_call.function.arguments)
                            }
                        })

                result["message"]["tool_calls"] = tool_calls

                # Для обратной совместимости сохраняем и старый формат
                if tool_calls:
                    result["message"]["function_call"] = {
                        "name": tool_calls[0]["function"]["name"],
                        "arguments": tool_calls[0]["function"]["arguments"]
                    }

            # Сохраняем в кеш
            os.makedirs(cache_dir, exist_ok=True)
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
                print(f"💾 Сохранено в кеш: {cache_file}")

            return result

        except Exception as e:
            return {
                "error": str(e),
                "user_query": user_query,
                "functions_called": [func["name"] for func in function_schemas]
            }

    def test_natural_language_understanding(
        self,
        test_cases: List[Dict[str, Any]],
        function_schemas: List[Dict[str, Any]],
        verbose: bool = True
    ) -> Dict[str, Any]:
        """
        Запускает набор тестовых кейсов для проверки понимания естественного языка.
        Обновленная версия для работы с новым форматом tools.
        """
        if verbose:
            print(f"\n🎯 Запуск тестирования с новым форматом tools")

        results = {
            "total": len(test_cases),
            "passed": 0,
            "failed": 0,
            "errors": 0,
            "details": [],
            "function_stats": {}
        }

        for i, test_case in enumerate(test_cases, 1):
            if verbose:
                print(f"\n🔍 Тест {i}/{len(test_cases)}: '{test_case['query']}'")

            try:
                response = self.call_with_functions(
                    user_query=test_case["query"],
                    function_schemas=function_schemas,
                    use_cache=True
                )

                test_result = self._evaluate_test_case(test_case, response)
                test_result["test_index"] = i

                results["details"].append(test_result)

                # Обновляем статистику
                if test_result["status"] == "passed":
                    results["passed"] += 1
                elif test_result["status"] == "failed":
                    results["failed"] += 1
                elif test_result["status"] == "error":
                    results["errors"] += 1

                # Обновляем статистику по функциям
                if response.get("message", {}).get("function_call"):
                    func_name = response["message"]["function_call"]["name"]
                    if func_name not in results["function_stats"]:
                        results["function_stats"][func_name] = {
                            "called": 0,
                            "passed": 0,
                            "failed": 0
                        }
                    results["function_stats"][func_name]["called"] += 1
                    if test_result["status"] == "passed":
                        results["function_stats"][func_name]["passed"] += 1
                    elif test_result["status"] == "failed":
                        results["function_stats"][func_name]["failed"] += 1

            except Exception as e:
                error_result = {
                    "test_index": i,
                    "query": test_case["query"],
                    "status": "error",
                    "error": str(e),
                    "expected_function": test_case.get("expected_function"),
                    "expected_arguments": test_case.get("expected_arguments", {})
                }
                results["details"].append(error_result)
                results["errors"] += 1

        # Вычисляем общую статистику
        results["success_rate"] = results["passed"] / results["total"] * 100 if results["total"] > 0 else 0

        if verbose:
            self._print_test_summary(results)

        return results

    def _evaluate_test_case(
        self,
        test_case: Dict[str, Any],
        response: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Оценивает результат выполнения тестового кейса для нового формата"""
        test_result = {
            "query": test_case["query"],
            "expected_function": test_case.get("expected_function"),
            "expected_arguments": test_case.get("expected_arguments", {}),
            "response": response
        }

        if "error" in response:
            test_result["status"] = "error"
            test_result["error"] = response["error"]
            return test_result

        message = response.get("message", {})

        # Проверяем, есть ли tool_calls (новый формат) или function_call (старый формат для совместимости)
        tool_calls = message.get("tool_calls")
        function_call = message.get("function_call")

        # Используем function_call для обратной совместимости
        if function_call:
            actual_function = function_call["name"]
            actual_arguments = function_call["arguments"]
        elif tool_calls and len(tool_calls) > 0:
            # Берем первый tool_call
            actual_function = tool_calls[0]["function"]["name"]
            actual_arguments = tool_calls[0]["function"]["arguments"]
        else:
            actual_function = None
            actual_arguments = None

        # Проверяем, ожидался ли вызов функции
        expect_no_function = test_case.get("expect_no_function", False)

        if expect_no_function:
            if not actual_function:
                test_result["status"] = "passed"
                test_result["reason"] = "Функция не вызвана, как и ожидалось"
            else:
                test_result["status"] = "failed"
                test_result["reason"] = (
                    f"Ожидалось, что функция не будет вызвана, "
                    f"но вызвана {actual_function}"
                )
            return test_result

        # Проверяем, вызвана ли функция
        if not actual_function:
            test_result["status"] = "failed"
            test_result["reason"] = "Модель не вызвала функцию"
            return test_result

        # Проверяем правильность функции
        expected_function = test_case.get("expected_function")
        if expected_function and actual_function != expected_function:
            test_result["status"] = "failed"
            test_result["reason"] = (
                f"Ожидалась функция '{expected_function}', "
                f"но вызвана '{actual_function}'"
            )
            test_result["actual_function"] = actual_function
            return test_result

        # Проверяем аргументы
        expected_arguments = test_case.get("expected_arguments", {})
        partial_match = test_case.get("partial_match", True)

        validation = self._validate_arguments(
            actual_arguments,
            expected_arguments,
            partial_match=partial_match
        )

        if validation["valid"]:
            test_result["status"] = "passed"
        else:
            test_result["status"] = "failed"
            test_result["reason"] = validation["reason"]

        test_result["actual_function"] = actual_function
        test_result["actual_arguments"] = actual_arguments

        return test_result

    def _validate_arguments(
        self,
        actual: Dict[str, Any],
        expected: Dict[str, Any],
        partial_match: bool = True
    ) -> Dict[str, Any]:
        """Валидирует аргументы, возвращенные моделью"""
        if not actual:
            return {"valid": False, "reason": "Аргументы отсутствуют"}

        if partial_match:
            # Проверяем только указанные в expected поля
            for key, expected_value in expected.items():
                if key not in actual:
                    return {
                        "valid": False,
                        "reason": f"Отсутствует обязательный параметр: '{key}'"
                    }

                actual_value = actual[key]

                # Специальная обработка для списков (строки с запятыми)
                if isinstance(expected_value, str) and ',' in expected_value:
                    expected_items = set(item.strip() for item in expected_value.split(','))
                    if isinstance(actual_value, str):
                        actual_items = set(item.strip() for item in actual_value.split(','))
                    elif isinstance(actual_value, list):
                        actual_items = set(str(item).strip() for item in actual_value)
                    else:
                        actual_items = {str(actual_value)}

                    if not expected_items.issubset(actual_items):
                        return {
                            "valid": False,
                            "reason": (
                                f"Параметр '{key}': ожидались элементы {expected_items}, "
                                f"получено {actual_items}"
                            )
                        }

                elif isinstance(expected_value, list) and isinstance(actual_value, list):
                    # Оба значения - списки
                    if set(expected_value) != set(actual_value):
                        return {
                            "valid": False,
                            "reason": f"Параметр '{key}': ожидалось {expected_value}, получено {actual_value}"
                        }

                elif str(actual_value).lower() != str(expected_value).lower():
                    # Сравниваем как строки, игнорируя регистр
                    return {
                        "valid": False,
                        "reason": f"Параметр '{key}': ожидалось '{expected_value}', получено '{actual_value}'"
                    }
        else:
            # Полное соответствие
            if actual != expected:
                return {
                    "valid": False,
                    "reason": f"Полное несоответствие: ожидалось {expected}, получено {actual}"
                }

        return {"valid": True}

    def _print_test_summary(self, results: Dict[str, Any]):
        """Выводит сводку результатов тестирования"""
        print(f"\n{'='*60}")
        print("📊 СВОДКА РЕЗУЛЬТАТОВ ТЕСТИРОВАНИЯ")
        print(f"{'='*60}")
        print(f"Всего тестов: {results['total']}")
        print(f"✅ Пройдено: {results['passed']}")
        print(f"❌ Провалено: {results['failed']}")
        print(f"⚠️  Ошибок: {results['errors']}")
        print(f"📈 Успешность: {results['success_rate']:.1f}%")

        if results['function_stats']:
            print(f"\n📋 Статистика по функциям:")
            for func_name, stats in results['function_stats'].items():
                success_rate = stats['passed'] / stats['called'] * 100 if stats['called'] > 0 else 0
                print(f"  {func_name}:")
                print(f"    Вызовов: {stats['called']}")
                print(f"    Успешно: {stats['passed']} ({success_rate:.1f}%)")
                print(f"    Провалов: {stats['failed']}")

# Простой тест
if __name__ == "__main__":
    import sys

    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("❌ Установите OPENROUTER_API_KEY")
        sys.exit(1)

    try:
        client = OpenRouterClient(api_key=api_key)
        print("✅ Клиент OpenRouter создан (новый формат tools)")

        # Тестовая схема
        test_schema = {
            "name": "test_function",
            "description": "Тестовая функция",
            "parameters": {
                "type": "object",
                "properties": {
                    "message": {"type": "string", "description": "Сообщение"}
                },
                "required": ["message"]
            }
        }

        # Тестовый запрос
        result = client.call_with_functions(
            user_query="Скажи привет",
            function_schemas=[test_schema],
            use_cache=False
        )

        print("\n📊 Результат теста:")
        print(json.dumps(result, indent=2, ensure_ascii=False))

    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()