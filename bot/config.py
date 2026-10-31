from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    telegram_bot_token: str = Field(..., alias="TELEGRAM_BOT_TOKEN")
    supabase_url: str = Field(..., alias="SUPABASE_URL")
    supabase_service_role_key: str = Field(..., alias="SUPABASE_SERVICE_ROLE_KEY")
    webapp_url: str = Field("https://example.com", alias="WEBAPP_URL")
    admin_telegram_ids: str = Field("", alias="ADMIN_TELEGRAM_IDS")

    @property
    def admin_ids(self) -> List[int]:
        if not self.admin_telegram_ids.strip():
            return []
        return [
            int(x.strip())
            for x in self.admin_telegram_ids.split(",")
            if x.strip().isdigit()
        ]


settings = Settings()
