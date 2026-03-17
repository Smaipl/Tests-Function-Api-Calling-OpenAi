from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class ApiKeys(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="AI_API_KEY",
        extra="allow",
    )

    def get_key_for(self, provider_name: str) -> SecretStr | None:
        attr_name = provider_name.lower().replace("-", "_")
        value = getattr(self, attr_name, None)

        return (
            value
            if isinstance(value, SecretStr)
            else (SecretStr(str(value)) if value else None)
        )


api_keys_storage = ApiKeys()
