"""Intervals.icu REST API client.

Auth: HTTP Basic with username 'API_KEY' and password = your API key.
Docs: https://intervals.icu/api-docs.html
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any, Iterable

import requests
from requests.auth import HTTPBasicAuth
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from src.utils.logger import get_logger

logger = get_logger(__name__)

_RETRYABLE = (
    requests.ConnectionError,
    requests.Timeout,
    requests.HTTPError,
)


class IntervalsClient:
    """Thin wrapper around Intervals.icu endpoints we need for training analysis."""

    def __init__(
        self,
        athlete_id: str,
        api_key: str,
        base_url: str = "https://intervals.icu/api/v1",
        timeout: int = 30,
    ) -> None:
        self.athlete_id = athlete_id
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._session = requests.Session()
        self._session.auth = HTTPBasicAuth("API_KEY", api_key)
        self._session.headers.update({"Accept": "application/json"})

    @retry(
        retry=retry_if_exception_type(_RETRYABLE),
        stop=stop_after_attempt(4),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    def _get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        url = f"{self.base_url}{path}"
        logger.debug("GET %s params=%s", url, params)
        resp = self._session.get(url, params=params, timeout=self.timeout)
        resp.raise_for_status()
        return resp.json()

    def get_athlete(self) -> dict[str, Any]:
        return self._get(f"/athlete/{self.athlete_id}")

    def list_activities(
        self,
        oldest: date | str | None = None,
        newest: date | str | None = None,
    ) -> list[dict[str, Any]]:
        """List activities in a date range. Defaults to last 5 years."""
        if oldest is None:
            oldest = date.today() - timedelta(days=365 * 5)
        if newest is None:
            newest = date.today()
        params = {
            "oldest": _to_iso(oldest),
            "newest": _to_iso(newest),
        }
        return self._get(f"/athlete/{self.athlete_id}/activities", params=params)

    def get_activity(self, activity_id: str) -> dict[str, Any]:
        return self._get(f"/activity/{activity_id}")

    def list_wellness(
        self,
        oldest: date | str | None = None,
        newest: date | str | None = None,
    ) -> list[dict[str, Any]]:
        """Daily wellness rows. Includes ctl, atl, ctlLoad, atlLoad, weight, hrv, sleep, etc.

        TSB is not stored — compute as ctl - atl downstream.
        """
        if oldest is None:
            oldest = date.today() - timedelta(days=365 * 5)
        if newest is None:
            newest = date.today()
        params = {
            "oldest": _to_iso(oldest),
            "newest": _to_iso(newest),
        }
        return self._get(f"/athlete/{self.athlete_id}/wellness", params=params)

    def extract_ftp_history(
        self, activities: Iterable[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Derive an FTP change timeline from per-activity icu_ftp values.

        Returns rows shaped {date, ftp} only when FTP changes from the previous activity.
        """
        history: list[dict[str, Any]] = []
        last_ftp: float | None = None
        # Activities arrive newest-first from the API; iterate oldest-first for the timeline.
        for act in sorted(activities, key=lambda a: a.get("start_date_local", "")):
            ftp = act.get("icu_ftp")
            if ftp is None:
                continue
            if last_ftp is None or ftp != last_ftp:
                history.append(
                    {
                        "date": act.get("start_date_local", "")[:10],
                        "ftp": ftp,
                        "source_activity_id": act.get("id"),
                    }
                )
                last_ftp = ftp
        return history


def _to_iso(d: date | str) -> str:
    if isinstance(d, str):
        return d
    if isinstance(d, datetime):
        return d.date().isoformat()
    return d.isoformat()
