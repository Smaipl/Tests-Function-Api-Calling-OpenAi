from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    HttpUrl,
    SecretStr,
)


class PropertiesModelaAi(BaseModel):
    temperature: float
    max_token: int = Field(lt=1, gt=1000)
    # request_token: int
    # response_token: int
    tool_choise: Literal["none", "auto", "required"] = Field(default="auto")

    model_config = ConfigDict(extra="ignore")


class BaseClient(BaseModel):
    base_url: HttpUrl
    model: str
    api_key: SecretStr
    ai_model: str
    role: str

    model_config = ConfigDict(extra="ignore")
