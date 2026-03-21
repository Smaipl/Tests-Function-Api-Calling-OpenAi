from unittest.mock import MagicMock

import allure
import openai
import pytest

from src.ai_model_client import ModelInterface
from src.exceptions.custom_exceptions import LLMGenerationError, LLMMismatchError


# Группировка для Allure Awesome Reporter
@allure.epic("OpenAI Integration")
@allure.feature("Model Interface")
class TestModelInterface:

    @pytest.mark.asyncio
    @allure.story("Successful Tool Call")
    async def test_successful_tool_call(self, ai_mock, root_config, schema):
        """Проверка успешного формирования ответа и обновления токенов"""
        mock_res = MagicMock()
        mock_choice = MagicMock()
        mock_message = MagicMock()

        mock_tool_call = MagicMock()
        mock_tool_call.function.name = schema.name
        mock_tool_call.function.arguments = '{"city": "Minsk"}'

        mock_message.tool_calls = [mock_tool_call]
        mock_message.content = None
        mock_choice.message = mock_message
        mock_choice.finish_reason = "tool_calls"
        mock_res.choices = [mock_choice]

        mock_res.usage.prompt_tokens = 10
        mock_res.usage.completion_tokens = 5
        mock_res.usage.total_tokens = 15

        ai_mock.chat.completions.create.return_value = mock_res

        result = await ModelInterface.call_with_functions(
            ai_client=ai_mock,
            client_conf=root_config,
            router_conf=root_config.router,
            model_conf=root_config.router.model_settings,
            query="test",
            json_schema=schema,
        )

        with allure.step("Проверка возвращаемого сообщения"):
            assert result["message"].tool_calls[0].function.name == schema.name

        with allure.step("Проверка обновления токенов"):
            assert result["usage"]["total_tokens"] == 15
            assert root_config._total_token == 15

    @pytest.mark.asyncio
    @allure.story("API Status Errors")
    @pytest.mark.parametrize(
        "status_code, expected_part",
        [(401, "Статус 401"), (429, "Статус 429"), (500, "Статус 500")],
        ids=["Unauthorized", "RateLimit", "ServerError"],
    )
    async def test_api_status_errors(
        self, ai_mock, root_config, schema, status_code, expected_part
    ):
        mock_error_res = MagicMock()
        mock_error_res.status_code = status_code

        ai_mock.chat.completions.create.side_effect = openai.APIStatusError(
            message=f"Ошибка сервера {status_code}",
            response=mock_error_res,
            body={"error": "api_error"},
        )

        with pytest.raises(LLMGenerationError) as exc:
            await ModelInterface.call_with_functions(
                ai_mock,
                root_config,
                root_config.router,
                root_config.router.model_settings,
                "test",
                schema,
            )
        assert expected_part in exc.value.message

    @pytest.mark.asyncio
    @allure.story("Network/Connection Errors")
    async def test_network_errors(self, ai_mock, root_config, schema):
        # Имитируем обрыв сети
        ai_mock.chat.completions.create.side_effect = openai.APIConnectionError(
            message="No internet connection", request=MagicMock()
        )
        with pytest.raises(LLMGenerationError, match="Ошибка сети"):
            await ModelInterface.call_with_functions(
                ai_mock,
                root_config,
                root_config.router,
                root_config.router.model_settings,
                "test",
                schema,
            )

    @pytest.mark.asyncio
    @allure.story("Logical Mismatch")
    async def test_mismatch_errors(self, ai_mock, root_config, schema):
        # Имитируем ответ текстом вместо функции
        mock_res = MagicMock()
        mock_message = MagicMock(content="I am just a bot", tool_calls=None)
        mock_res.choices = [MagicMock(message=mock_message, finish_reason="stop")]

        ai_mock.chat.completions.create.return_value = mock_res

        with pytest.raises(LLMMismatchError, match="Модель ответила текстом"):
            await ModelInterface.call_with_functions(
                ai_mock,
                root_config,
                root_config.router,
                root_config.router.model_settings,
                "test",
                schema,
            )

    @pytest.mark.asyncio
    @allure.story("Empty Response Handling")
    async def test_empty_handling(self, ai_mock, root_config, schema):
        # Кейс с пустыми choices
        mock_res = MagicMock(choices=[], id="test_id")
        ai_mock.chat.completions.create.return_value = mock_res

        with pytest.raises(LLMGenerationError, match="Пустой список choices"):
            await ModelInterface.call_with_functions(
                ai_mock,
                root_config,
                root_config.router,
                root_config.router.model_settings,
                "test",
                schema,
            )
