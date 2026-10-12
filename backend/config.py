"""Runtime configuration (environment variables prefixed with CURIO_)."""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="CURIO_", env_file=BACKEND_DIR / ".env", extra="ignore")

    harness_mode: Literal["auto", "rules", "llm"] = "auto"

    llm_base_url: str = "https://api.openai.com/v1"
    llm_api_key: str = ""
    llm_model: str = "gpt-4o-mini"
    llm_timeout_s: float = 25.0
    llm_temperature: float = 0.2

    database_url: str = f"sqlite:///{BACKEND_DIR / 'curio.db'}"
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"

    # Mastery model (spec §11): mastery_new = mastery_old + learning_rate * evidence
    learning_rate: float = 0.2

    # Proposal: pathways must be teacher-reviewed before the AI uses them. Off by default
    # so the demo works out of the box; turn on for pilots.
    require_reviewed_content: bool = False
    # Data minimisation (PDPC children's data guidance): learning records older than this
    # are deleted by POST /api/privacy/purge.
    retention_days: int = 365

    demo_student_id: str = "demo_student"
    seed_class_size: int = 24

    @property
    def llm_enabled(self) -> bool:
        if self.harness_mode == "rules":
            return False
        return bool(self.llm_api_key)

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
