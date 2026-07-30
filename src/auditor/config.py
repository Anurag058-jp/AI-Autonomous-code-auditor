import os
import sys
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


APP_DATA_DIR = Path(os.environ.get("LOCALAPPDATA", Path.home())) / "ZeroCostAICodeAuditor"
ENV_FILES = (".env", APP_DATA_DIR / ".env")


class Settings(BaseSettings):
    # A development .env remains supported; installed builds also load a
    # per-user configuration file outside Program Files.
    model_config = SettingsConfigDict(env_file=ENV_FILES, extra="ignore")
    groq_api_key: str | None = None
    gemini_api_key: str | None = None
    mistral_api_key: str | None = None
    audit_llm_provider: str = "groq"
    audit_llm_model: str = "llama-3.3-70b-versatile"
    audit_embedding_model: str = "BAAI/bge-small-en-v1.5"
    audit_data_dir: Path = APP_DATA_DIR if getattr(sys, "frozen", False) else Path(".audit")

    @property
    def data_dir(self) -> Path:
        self.audit_data_dir.mkdir(parents=True, exist_ok=True)
        return self.audit_data_dir


settings = Settings()
