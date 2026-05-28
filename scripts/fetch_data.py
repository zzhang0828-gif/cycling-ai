"""Entry point: pull activities, wellness (CTL/ATL/TSB), and FTP history from Intervals.icu.

Usage:
    python scripts/fetch_data.py
    python scripts/fetch_data.py --oldest 2020-01-01 --newest 2026-05-28
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Allow running as a script: add project root to sys.path.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config.config import RAW_DIR, IntervalsConfig  # noqa: E402
from src.api.intervals_client import IntervalsClient  # noqa: E402
from src.data.fetcher import IntervalsDataFetcher  # noqa: E402
from src.utils.logger import get_logger  # noqa: E402

logger = get_logger("fetch_data")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Fetch Intervals.icu training history.")
    p.add_argument("--oldest", default=None, help="ISO date, e.g. 2020-01-01")
    p.add_argument("--newest", default=None, help="ISO date, e.g. 2026-05-28")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    cfg = IntervalsConfig.from_env()
    client = IntervalsClient(athlete_id=cfg.athlete_id, api_key=cfg.api_key, base_url=cfg.base_url)
    fetcher = IntervalsDataFetcher(client=client, raw_dir=RAW_DIR)

    result = fetcher.fetch_all(oldest=args.oldest, newest=args.newest)

    logger.info("Done. Counts: %s", result.counts)
    logger.info("Files written under: %s", RAW_DIR)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
