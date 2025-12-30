import json


def weather(arguments: dict) -> str:
    """
    Простая тестовая функция: принимает словарь {"city": <название>}
    и возвращает JSON-строку с погодой.
    """
    city = arguments.get("city", "")

    fake_data = {
        "Минск": {"temperature": -2, "condition": "snow"},
        "Брест": {"temperature": 1, "condition": "cloudy"},
    }

    result = fake_data.get(city, {"temperature": 0, "condition": "unknown"})
    return json.dumps(result, ensure_ascii=False)
