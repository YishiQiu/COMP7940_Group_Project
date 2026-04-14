from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Telegram Stock Query Assistant"
    app_env: str = "development"
    app_port: int = 8000
    log_level: str = "INFO"

    telegram_bot_token: str = ""
    telegram_webhook_secret_token: str = ""
    public_base_url: str = ""
    set_telegram_webhook_on_startup: bool = False

    llm_api_key: str = ""
    llm_model: str = ""
    llm_base_url: str = ""
    llm_provider_name: str = "MiMo Coding Plane"

    openai_api_key: str = ""
    openai_model: str = "gpt-4.1-mini"

    database_url: str = "sqlite:///./local.db"

    stock_api_base_url: str = "https://query1.finance.yahoo.com"
    twelve_data_api_key: str = ""
    twelve_data_base_url: str = "https://api.twelvedata.com"
    request_timeout_seconds: int = 20
    allowed_hosts: str = "*"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def webhook_url(self) -> str:
        base = self.public_base_url.rstrip("/")
        return f"{base}/webhook/telegram" if base else ""

    @property
    def effective_llm_api_key(self) -> str:
        return self.llm_api_key or self.openai_api_key

    @property
    def effective_llm_model(self) -> str:
        return self.llm_model or self.openai_model


@lru_cache
def get_settings() -> Settings:
    return Settings()
