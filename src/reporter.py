import json
import os

from rich.console import Console
from rich.table import Table


class LocalReporter:
    """Красивый вывод для локального запуска"""

    def report(self, results):
        console = Console()
        table = Table(title="Результаты тестов")

        table.add_column("Тест", justify="right")
        table.add_column("Функция")
        table.add_column("Запрос")
        table.add_column("Результат")

        for i, detail in enumerate(results.get("details", []), 1):
            chain = detail.get("execution_chain", [])
            if chain:
                func = chain[0]["function"]
                result = chain[0]["result"]
                query = detail.get("query", "")
                table.add_row(
                    str(i), func, query[:40] + ("..." if len(query) > 40 else ""), str(result)
                )

        console.print(table)


class CIReporter:
    """Строгий вывод для CI/CD (GitHub Actions)"""

    def report(self, results, output_path="test_results.json"):
        # Сохраняем JSON
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

        # Выводим в summary (GitHub Actions)
        summary_path = os.getenv("GITHUB_STEP_SUMMARY")
        if summary_path:
            with open(summary_path, "a", encoding="utf-8") as f:
                f.write("### Результаты тестов\n\n")
                for i, detail in enumerate(results.get("details", []), 1):
                    f.write(f"#### Тест {i}\n")
                    f.write(f"- Запрос: {detail.get('query', '')}\n")
                    for step in detail.get("execution_chain", []):
                        f.write(f"- Функция: {step['function']}\n")
                        f.write(f"- Результат: {step['result']}\n\n")
