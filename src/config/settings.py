from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    DATABASE_URL: str
    API_KEY: str
    REVIEW_TRIGGER_LIMIT: int = 20
    MAX_GOLDEN_SAMPLES: int = 15
    REVIEW_BATCH_SIZE: int = 20
    MAX_PROMPT_RETRIES: int = 2
    MIN_REGRESSION_ACCURACY: float = 1.0
    INITIAL_PROMPT: str
    OPTIMIZE_PROMPT: str
    STUDENT_LLM_MODEL_NAME: str = Field(
        default="gemini-2.0-flash-lite",
        validation_alias="STUDENT_LLM_MODEL_NAME",
    )
    PROFESSOR_LLM_MODEL_NAME: str = Field(
        default="llama-3.3-70b-versatile",
        validation_alias="PROFESSOR_LLM_MODEL_NAME",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
