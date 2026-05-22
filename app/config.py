from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    groq_api_key: str = ""
    groq_model: str = "llama-3.1-8b-instant"
    app_env: str = "development"
    database_path: Path = Path("data/greenpack.sqlite3")
    erp_feed_path: Path = Path("data/mock_erp_feed.csv")
    rag_corpus_path: Path = Path("data/rag_corpus/policy_docs.json")

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


@lru_cache
def get_settings() -> Settings:
    return Settings()
