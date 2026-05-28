"""Centralised config loaded from .env."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"

load_dotenv(PROJECT_ROOT / ".env")


@dataclass(frozen=True)
class IntervalsConfig:
    athlete_id: str
    api_key: str
    base_url: str = "https://intervals.icu/api/v1"

    @classmethod
    def from_env(cls) -> "IntervalsConfig":
        athlete_id = os.getenv("INTERVALS_ATHLETE_ID", "").strip()
        api_key = os.getenv("INTERVALS_API_KEY", "").strip()
        if not athlete_id or not api_key:
            raise RuntimeError(
                "Missing INTERVALS_ATHLETE_ID or INTERVALS_API_KEY. "
                "Copy .env.example to .env and fill in the values."
            )
        return cls(athlete_id=athlete_id, api_key=api_key)
