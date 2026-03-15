from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    telegram_bot_token: str
    core_url: str
    internal_api_key: str
    manager_chat_id: int

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()