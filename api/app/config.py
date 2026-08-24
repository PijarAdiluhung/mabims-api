from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

APP_VERSION = "1.0.0"

DEFAULT_ORIGIN_SUFFIXES = ["malangmengaji.com"]


def _csv_env(name: str, default: str) -> list[str]:
    raw = os.environ.get(name, default)
    return [item.strip() for item in raw.split(",") if item.strip()]


@dataclass(frozen=True)
class Settings:
    data_dir: Path = field(default_factory=lambda: Path(__file__).resolve().parent.parent / "data")
    docs_url: str = "https://mabims.pixostudio.id"
    allowed_origins: list[str] = field(default_factory=lambda: _csv_env("ALLOWED_ORIGINS", ""))
    origin_suffixes: list[str] = field(
        default_factory=lambda: _csv_env("ALLOWED_ORIGIN_SUFFIXES", ",".join(DEFAULT_ORIGIN_SUFFIXES))
    )
    rate_limit: str = os.environ.get("RATE_LIMIT", "240/minute")
    enable_fallback: bool = os.environ.get("MABIMS_DISABLE_FALLBACK", "") != "1"
    aladhan_base_url: str = os.environ.get("ALADHAN_BASE_URL", "https://api.aladhan.com/v1")
