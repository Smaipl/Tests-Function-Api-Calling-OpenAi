import httpx

response = httpx.get(
    "https://api.proxyapi.ru/openrouter/v1/models",
    headers={"Authorization": "Bearer <КЛЮЧ-PROXYAPI>"},
)

models = response.json()
for model in models["data"]:
    print(f"ID: {model['id']}")
    print(f"Название: {model['name']}")
    print(f"Стоимость ввода: ${model['pricing']['prompt']}")
    print(f"Стоимость вывода: ${model['pricing']['completion']}")
    print("---")
