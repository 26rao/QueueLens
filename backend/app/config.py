from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    APP_ENV: str = "development"
    DATABASE_URL: str = "sqlite:///./queuelens.db"
    LLM_ENABLED: bool = False
    LLM_API_KEY: str = ""
    LLM_BASE_URL: str = ""
    LLM_MODEL: str = ""
    CORS_ORIGINS: List[str] = ["*"]
    PLANNING_HORIZON: int = 480

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
