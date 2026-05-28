"""Orchestrates pulls from Intervals.icu and persists raw JSON to data/raw/."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

from src.api.intervals_client import IntervalsClient
from src.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class FetchResult:
    activities_path: Path
    wellness_path: Path
    ftp_history_path: Path
    counts: dict[str, int]


class IntervalsDataFetcher:
    def __init__(self, client: IntervalsClient, raw_dir: Path) -> None:
        self.client = client
        self.raw_dir = raw_dir
        self.raw_dir.mkdir(parents=True, exist_ok=True)

    def fetch_all(
        self,
        oldest: date | str | None = None,
        newest: date | str | None = None,
    ) -> FetchResult:
        logger.info("Fetching activities…")
        activities = self.client.list_activities(oldest=oldest, newest=newest)
        logger.info("Got %d activities", len(activities))

        logger.info("Fetching wellness (CTL/ATL)…")
        wellness = self.client.list_wellness(oldest=oldest, newest=newest)
        logger.info("Got %d wellness rows", len(wellness))

        logger.info("Deriving FTP history from activities…")
        ftp_history = self.client.extract_ftp_history(activities)
        logger.info("Detected %d FTP changes", len(ftp_history))

        activities_path = self._write_json("activities.json", activities)
        wellness_path = self._write_json("wellness.json", wellness)
        ftp_history_path = self._write_json("ftp_history.json", ftp_history)

        return FetchResult(
            activities_path=activities_path,
            wellness_path=wellness_path,
            ftp_history_path=ftp_history_path,
            counts={
                "activities": len(activities),
                "wellness": len(wellness),
                "ftp_changes": len(ftp_history),
            },
        )

    def _write_json(self, filename: str, payload: Any) -> Path:
        path = self.raw_dir / filename
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2))
        logger.info("Wrote %s", path)
        return path
