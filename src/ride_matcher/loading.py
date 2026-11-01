"""Load ride-request and candidate-driver CSV data from the project data folder."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import List

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"

REQUESTS_FILE = DATA_DIR / "uber_ride_requests_test_set.csv"
CANDIDATES_FILE = DATA_DIR / "uber_candidate_drivers_snapshot.csv"


def _read_csv(path: Path) -> List[dict]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def load_requests(path: str | Path | None = None) -> List[dict]:
    """Load ride requests and coerce typed fields."""
    p = Path(path) if path else REQUESTS_FILE
    rows = _read_csv(p)
    for row in rows:
        row["pickup_lat"] = float(row["pickup_lat"])
        row["pickup_lng"] = float(row["pickup_lng"])
        row["is_bridge_case"] = str(row.get("is_bridge_case", "")).lower() == "true"
        row["distance_time_disagree"] = str(row.get("distance_time_disagree", "")).lower() == "true"
    return rows


def load_candidates(path: str | Path | None = None) -> List[dict]:
    """Load candidate drivers and coerce typed fields."""
    p = Path(path) if path else CANDIDATES_FILE
    rows = _read_csv(p)
    for row in rows:
        row["driver_lat"] = float(row["driver_lat"])
        row["driver_lng"] = float(row["driver_lng"])
        row["straight_line_km"] = float(row["straight_line_km"])
        raw_minutes = row.get("road_pickup_minutes") or ""
        row["road_pickup_minutes"] = float(raw_minutes) if raw_minutes.strip() else None
    return rows
