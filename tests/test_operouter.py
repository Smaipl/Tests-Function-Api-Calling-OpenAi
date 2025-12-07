import pytest
import json
from src.openrouter_client import OpenRouterClient
from src.schemas import get_card_creation_schema, get_order_schema


class TestOpenRouterFunctionCalling:
	"""Интеграционные тесты с реальным OpenRouter API"""

	@pytest.mark.integration
	def test_natural_language_understanding(self, real_openrouter_client, test_cases):
		"""Тестируем понимание естественного языка моделью"""

		schemas = [get_card_creation_schema(), get_order_schema()]

		results = real_openrouter_client.test_natural_language_understanding(
			test_cases=test_cases,
			function_schemas=schemas
		)

		print(f"\n📊 Результаты тестирования:")
		print(f"Всего тестов: {results['total']}")
		print(f"Пройдено: {results['passed']}")
		print(f"Провалено: {results['failed']}")

		# Выводим детали по неудачным тестам
		for detail in results["details"]:
			if detail["status"] != "passed":
				print(f"\n❌ Провален: '{detail['query']}'")
				if "reason" in detail:
					print(f"   Причина: {detail['reason']}")
				if detail["response"].get("message", {}).get("function_call"):
					print(f"   Вызвана функция: {detail['response']['message']['function_call']['name']}")
					print(f"   Аргументы: {detail['response']['message']['function_call']['arguments']}")

		# Сохраняем результаты для анализа
		with open("test_results.json", "w", encoding="utf-8") as f:
			json.dump(results, f, ensure_ascii=False, indent=2)

		# Требуем высокий процент успеха
		success_rate = results["passed"] / results["total"] * 100
		print(f"\n📈 Процент успеха: {success_rate:.1f}%")

		# В реальном проекте можно установить минимальный порог
		assert success_rate >= 80.0, f"Слишком низкий процент успеха: {success_rate:.1f}%"

	@pytest.mark.integration
	@pytest.mark.parametrize("query, expected_name", [
		("Создай карточку 'Финансы'", "Финансы"),
		("Нужна карточка под названием Маркетинг", "Маркетинг"),
		("Заведи карточку для задачи Разработка", "Разработка"),
		("Сделай карточку: Анализ данных", "Анализ данных"),
	])
	def test_various_phrasings(self, real_openrouter_client, query, expected_name):
		"""Тестируем разные формулировки запросов"""

		schema = get_card_creation_schema()

		response = real_openrouter_client.call_with_functions(
			user_query=query,
			function_schemas=[schema],
			use_cache=True
		)

		assert "error" not in response, f"Ошибка API: {response.get('error')}"

		function_call = response["message"]["function_call"]
		assert function_call is not None, "Модель не вызвала функцию"
		assert function_call["name"] == "create_card"
		assert function_call["arguments"]["name"] == expected_name

	@pytest.mark.integration
	def test_function_selection(self, real_openrouter_client):
		"""Тестируем выбор правильной функции"""

		schemas = [get_card_creation_schema(), get_order_schema()]

		# Запрос, который должен вызвать create_order
		response = real_openrouter_client.call_with_functions(
			user_query="Закажи 3 монитора для офиса",
			function_schemas=schemas,
			use_cache=True
		)

		function_call = response["message"]["function_call"]
		assert function_call["name"] == "create_order"
		assert function_call["arguments"]["product_name"] == "мониторы"
		assert function_call["arguments"]["quantity"] == 3

	@pytest.mark.integration
	def test_cache_mechanism(self, real_openrouter_client, tmp_path):
		"""Тестируем механизм кеширования"""

		schema = get_card_creation_schema()
		cache_dir = tmp_path / "cache"

		# Первый вызов - должен сохранить в кеш
		response1 = real_openrouter_client.call_with_functions(
			user_query="Тест кеширования",
			function_schemas=[schema],
			use_cache=True,
			cache_dir=str(cache_dir)
		)

		# Второй вызов - должен загрузить из кеша
		response2 = real_openrouter_client.call_with_functions(
			user_query="Тест кеширования",
			function_schemas=[schema],
			use_cache=True,
			cache_dir=str(cache_dir)
		)

		# Проверяем, что ответы идентичны
		assert response1 == response2

		# Проверяем, что файл кеша создан
		cache_files = list(cache_dir.glob("*.json"))
		assert len(cache_files) == 1