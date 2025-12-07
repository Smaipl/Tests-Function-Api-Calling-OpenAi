# Tests Function API Calling OpenAI

## 📂 Структура проекта
```commandline
📂 Project Root
├── src/                          # исходный код функций
│   ├── functions/                # отдельные файлы с реализованными функциями
│   │   ├── get_weather_report.py
│   │   ├── trello_list_action.py
│   │   └── ...
│   ├── function_register.py      # реестр функций и механизм регистрации
│   └── openrouter_client.py      # клиент для работы с OpenRouter API
│
├── tests/                        # тестовые сценарии и runner
│   ├── test_runner.py            # основной тест‑раннер
│   └── suites/                   # JSON‑файлы с тестовыми наборами (suites)
│       ├── weather.json
│       ├── trello_list_action.json
│       └── ...
│
├── test_results/                 # результаты выполнения тестов (отчёты и exec)
│   ├── get_weather_report/
│   ├── trello_list_action/
│   └── ...
│
├── .venv/                        # виртуальное окружение
├── .env                          # ключи и токены (не хранить в git)
├── requirements.txt              # зависимости проекта
├── configurates/                 
│   ├── config.py                     # конфигурация (API‑ключи, токены)

```

## ➕ Как добавлять новые функции
1. Создать файл в `src/functions/`
2. Внутри файла:
   - Импортировать `register_function` из `src/function_register`.
   - Реализовать функцию.
   - Зарегистрировать её с JSON‑схемой.

```python
from src.function_register import register_function

def get_weather_report(city: str, date: str = None):
    return {"city": city, "date": date or "today", "temperature": "5°C"}

register_function(
    name="get_weather_report",
    description="Получает прогноз погоды для указанного города",
    parameters={
        "type": "object",
        "properties": {
            "city": {"type": "string"},
            "date": {"type": "string"}
        },
        "required": ["city"]
    },
    func=get_weather_report
)
```
3. После добавления файл автоматически импортируется при запуске test_runner.py.

## 🧪 Как добавлять тестовые suites

1. Создать JSON‑файл в tests/suites/, например:
```commandline
tests/suites/weather.json
```
2. Внутри описать тесты:
```json
[
  {
    "query": "Какая погода завтра в Минске?",
    "expected_function": "get_weather_report",
    "expected_arguments": {"city": "Минск", "date": "2025-12-08"}
  },
  {
    "query": "Погода в Берёзе сегодня",
    "expected_function": "get_weather_report",
    "expected_arguments": {"city": "Берёза"}
  }
]
```
3. Каждый тест содержит:
   - query — текст запроса на естественном языке.
   - expected_function — имя функции.
   - expected_arguments — аргументы, которые модель должна извлечь.

## 🚀 Как запускать тесты
```commandline
python tests/test_runner.py --function <имя_функции> --tests tests/suites/<файл>.json --verbose
```
```commandline
python -m tests.test_runner --function trello_list_action --tests tests/suites/trello_list_action.json --verbose
```


## 📊 Результаты тестов
- Отчёты сохраняются в test_results/<имя_функции>/tests_<timestamp>.json.
- Результаты выполнения функций сохраняются в test_results/<имя_функции>/exec_<timestamp>.json.

## ⚙️ Настройки
- Ключи и токены (например, Trello API, OpenRouter API) задаются в .env или через переменные окружения.
- Файл .gitignore исключает .env, snapshots/, test_results/, test_snapshots/, .venv/ и артефакты IDE.
