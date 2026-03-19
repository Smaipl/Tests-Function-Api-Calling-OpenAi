# def substitute_placeholders(text: str) -> str:
#     """
#     Заменяет маркеры вида secret.KEY на значения из переменных окружения.
#     Если переменной нет, оставляет маркер как есть.
#     """
#     pattern = r"secret\.([A-Z0-9_]+)"

#     def replacer(match):
#         key = match.group(1)
#         return os.getenv(key, match.group(0))

#     return re.sub(pattern, replacer, text)

import inspect
from typing import Annotated, Any, Literal

from openai.types.chat import ChatCompletionSystemMessageParam
from pydantic import (
    AfterValidator,
    BaseModel,
    ConfigDict,
    Field,
    HttpUrl,
    PrivateAttr,
    SecretStr,
    model_validator,
)

from src.schema.settings import api_keys_storage

StrUrl = Annotated[HttpUrl, AfterValidator(lambda v: str(v))]


class ModelConfig(BaseModel):
    model_id: str = Field(alias="name")
    semaphore: int = Field(ge=1)
    max_tokens: int = Field(ge=1)
    temperature: float = Field(ge=0.0, le=2.0)

    _properties: dict[str, Any] = PrivateAttr(default_factory=dict)

    model_config = ConfigDict(extra="allow", populate_by_name=True)

    @model_validator(mode="after")
    def filter_extra_params(self) -> "ModelConfig":
        try:
            from openai.resources.chat.completions import AsyncCompletions

            sig = inspect.signature(AsyncCompletions.create)
        except (ImportError, AttributeError):
            return self

        if self.model_extra:
            self._properties = {
                k: v for k, v in self.model_extra.items() if k in sig.parameters
            }
        return self

    def get_params(self) -> dict[str, Any]:
        params = self.model_dump(exclude={"semaphore", "model_id"}, exclude_none=True)
        params.update(self._properties)
        return params


class RouterConfig(BaseModel):
    config_name: str = Field(alias="name")
    base_url: StrUrl
    model_settings: ModelConfig = Field(alias="models")
    system_prompt: str = Field(alias="role")

    timeout: int = Field(default=60, ge=1)
    tool_choice: Literal["none", "auto", "required"] = "auto"
    max_retries: int = Field(default=3, ge=1)
    retry_delay: float = Field(default=1.3, ge=0.5)
    api_key: SecretStr | None = None

    model_config = ConfigDict(populate_by_name=True)

    @property
    def system_message(self) -> ChatCompletionSystemMessageParam:
        return ChatCompletionSystemMessageParam(
            role="system", content=self.system_prompt
        )

    def model_post_init(self, __context: Any) -> None:
        if not self.api_key:
            self.api_key = api_keys_storage.get_key_for(self.config_name)

            if not self.api_key:
                raise ValueError(
                    f"API key for {self.config_name} not found in ENV/Secrets"
                )


class ClientModel(BaseModel):
    router: RouterConfig
    queries: list[str] = Field(default_factory=list)

    _request_token: int = PrivateAttr(default=0)
    _response_token: int = PrivateAttr(default=0)
    _total_token: int = PrivateAttr(default=0)

    model_config = ConfigDict(arbitrary_types_allowed=True)

    @model_validator(mode="before")
    @classmethod
    def prepare_all_data(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data

        if "queries" in data and isinstance(data["queries"], list):
            data["queries"] = [
                (q.get("query") if isinstance(q, dict) else q)
                for q in data["queries"]
                if q
            ]
        return data

    @property
    def usage_report(self) -> str:
        """Красивый отчет о расходе токенов"""
        return (
            f"\n📊 ИТОГО ПОТРАЧЕНО:\n"
            f"   - Входящие: {self._request_token}\n"
            f"   - Исходящие: {self._response_token}\n"
            f"   - Всего:     {self._total_token}"
        )
