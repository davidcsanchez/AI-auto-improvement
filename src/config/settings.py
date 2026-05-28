from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    DATABASE_URL: str
    API_KEY: str
    REVIEW_TRIGGER_LIMIT: int = 20
    llm_model_name: str = Field(default="gemini-2.0-flash-lite", validation_alias="LLM_MODEL_NAME")


@lru_cache
def get_settings() -> Settings:
    return Settings()
