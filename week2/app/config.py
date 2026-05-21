"""Application configuration.

Provides a single `Settings` object that reads from environment variables
(loaded via `python-dotenv` at startup) with sensible defaults. Modules
should call `get_settings()` rather than reading os.environ directly so
configuration stays in one place.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


BASE_DIR = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class Settings:
    app_name: str = "Action Item Extractor"
    base_dir: Path = BASE_DIR
    data_dir: Path = BASE_DIR / "data"
    db_path: Path = BASE_DIR / "data" / "app.db"
    frontend_dir: Path = BASE_DIR / "frontend"
    ollama_model: str = "llama3.1:8b"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings(
        app_name=os.getenv("APP_NAME", "Action Item Extractor"),
        base_dir=BASE_DIR,
        data_dir=Path(os.getenv("DATA_DIR", str(BASE_DIR / "data"))),
        db_path=Path(os.getenv("DB_PATH", str(BASE_DIR / "data" / "app.db"))),
        frontend_dir=Path(os.getenv("FRONTEND_DIR", str(BASE_DIR / "frontend"))),
        ollama_model=os.getenv("OLLAMA_MODEL", "llama3.1:8b"),
    )
