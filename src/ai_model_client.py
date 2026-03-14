from typing import Any

from openai import OpenAI

from src.schema.client_schema import BaseClient, PropertiesModelaAi
from src.schema.json_schema import Schema


class ModelInterface:
    def __init__(self):
        self._config: BaseClient | None = None
        self._client: OpenAI | None = None

    @property
    def config(self) -> BaseClient:
        if self._config is None:
            raise ValueError("Конфигурация не установлена. Сначала задайте .config")
        return self._config

    @config.setter
    def config(self, conf: BaseClient):
        if conf is None:
            raise ValueError("Нельзя установить пустой конфиг")
        self._config = conf
        self._client = None

    @property
    def client(self) -> OpenAI:
        if self._client is None:
            self._client = OpenAI(
                api_key=self.config.api_key.get_secret_value(),
                base_url=self.config.base_url.encoded_string(),
            )
        return self._client

    def call_with_functions(
        self, user_query: str, json_schema: Schema, properties: PropertiesModelaAi
    ) -> dict[str, Any]:
        return {}


# def call_with_functions(
#     self,
#     user_query: str,
#     function_schemas: list[dict[str, Any]],
#     temperature: float = 0.1,
#     max_tokens: int = 500,
# ) -> dict[str, Any]:
#     # 🔥 заменяем маркеры в запросе

#     tools: list[ChatCompletionToolParam] = [
#         ChatCompletionToolParam(type="function", function=f) for f in function_schemas
#     ]

#     response = self.client.chat.completions.create(
#         model=self.model,
#         messages=[
#             {"role": "system", "content": self.role},
#             {"role": "user", "content": user_query},
#         ],
#         tools=tools,
#         tool_choice="auto",
#         temperature=temperature,
#         max_tokens=max_tokens,
#     )

#     message = response.choices[0].message
#     result: dict[str, Any] = {
#         "user_query": user_query,
#         "model": self.model,
#         "timestamp": response.created,
#         "message": {
#             "content": message.content,
#             "tool_calls": None,
#             "function_call": None,
#         },
#     }

#     tool_calls = message.tool_calls or []
#     parsed_calls = []
#     for tool_call in tool_calls:
#         if tool_call.type == "function":
#             try:
#                 args = json.loads(tool_call.function.arguments)
#             except json.JSONDecodeError:
#                 args = tool_call.function.arguments

#             parsed_calls.append(
#                 {
#                     "id": tool_call.id,
#                     "type": tool_call.type,
#                     "function": {
#                         "name": tool_call.function.name,
#                         "arguments": args,
#                     },
#                 }
#             )

#     if parsed_calls:
#         result["message"]["tool_calls"] = parsed_calls
#         result["message"]["function_call"] = parsed_calls[0]["function"]

#     return result
