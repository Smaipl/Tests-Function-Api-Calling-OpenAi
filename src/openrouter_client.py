import json
from typing import Any

from openai import OpenAI
from openai.types.chat import ChatCompletionToolParam

from configurates.config import OPENROUTER_API_KEY


class OpenRouterClient:
    def __init__(
        self,
        base_url: str = "https://openrouter.ai/api/v1",
        model: str = "openai/gpt-3.5-turbo",
    ):
        self.api_key = OPENROUTER_API_KEY
        self.client = OpenAI(base_url=base_url, api_key=self.api_key)
        self.model = model
        self.role = "Ты ассистент с поддержкой tools."

    def call_with_functions(
        self,
        user_query: str,
        function_schemas: list[dict[str, Any]],
        temperature: float = 0.1,
        max_tokens: int = 500,
    ) -> dict[str, Any]:
        # формируем список инструментов напрямую из dict схем
        tools: list[ChatCompletionToolParam] = [
            ChatCompletionToolParam(type="function", function=f) for f in function_schemas
        ]

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": self.role},
                {"role": "user", "content": user_query},
            ],
            tools=tools,
            tool_choice="auto",
            temperature=temperature,
            max_tokens=max_tokens,
        )

        message = response.choices[0].message
        result: dict[str, Any] = {
            "user_query": user_query,
            "model": self.model,
            "timestamp": response.created,
            "message": {
                "content": message.content,
                "tool_calls": None,
                "function_call": None,
            },
        }

        # безопасная итерация по tool_calls
        tool_calls = message.tool_calls or []
        parsed_calls = []
        for tool_call in tool_calls:
            if tool_call.type == "function":
                try:
                    args = json.loads(tool_call.function.arguments)
                except json.JSONDecodeError:
                    args = tool_call.function.arguments
                parsed_calls.append(
                    {
                        "id": tool_call.id,
                        "type": tool_call.type,
                        "function": {
                            "name": tool_call.function.name,
                            "arguments": args,
                        },
                    }
                )

        if parsed_calls:
            result["message"]["tool_calls"] = parsed_calls
            result["message"]["function_call"] = parsed_calls[0]["function"]

        return result
