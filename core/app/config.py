from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str
    internal_api_key: str
    telegram_bot_token: str
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()