"""Scoring and selection logic for driver assignment."""

from __future__ import annotations

from typing import List

from .state import Assignment, DriverCandidate


def score_candidate(request: dict, driver: DriverCandidate) -> tuple[float, str]:
    """Return (score, reason). Higher score is a better match."""
    reasons: List[str] = []
    score = 0.0

    # Prefer closer drivers (straight-line distance).
    distance = float(driver.get("straight_line_km") or 0.0)
    score -= distance * 10.0
    reasons.append(f"{distance:.2f} km away")

    # Prefer drivers on the same side of the river as the pickup.
    pickup_side = str(request.get("pickup_river_side", ""))
    driver_side = str(driver.get("driver_river_side", ""))
    if pickup_side and pickup_side == driver_side:
        score += 5.0
        reasons.append("same river side")
    else:
        reasons.append("opposite river side")

    if bool(request.get("is_bridge_case", False)):
        reasons.append("bridge case")

    road_minutes = driver.get("road_pickup_minutes")
    if road_minutes is not None:
        score -= float(road_minutes) * 0.5
        reasons.append(f"{road_minutes:.0f} min pickup")
    else:
        reasons.append("no road ETA")

    return score, "; ".join(reasons)


def filter_available(candidates: List[dict]) -> List[dict]:
    """Keep only drivers whose status is available."""
    return [c for c in candidates if str(c.get("driver_status", "")).lower() == "available"]


def select_driver(request: dict, candidates: List[dict]) -> Assignment:
    """Pick the best available driver for one request."""
    available = filter_available(candidates)

    best: dict | None = None
    best_score = float("-inf")
    best_reason = ""
    for driver in available:
        score, reason = score_candidate(request, driver)
        if score > best_score:
            best_score = score
            best = driver
            best_reason = reason

    if best is None:
        return {
            "request_id": request.get("request_id"),
            "rider_id": request.get("rider_id"),
            "pickup_zone": request.get("pickup_zone"),
            "dropoff_zone": request.get("dropoff_zone"),
            "is_bridge_case": bool(request.get("is_bridge_case", False)),
            "driver_id": None,
            "score": None,
            "reason": "no available driver",
        }

    return {
        "request_id": request.get("request_id"),
        "rider_id": request.get("rider_id"),
        "pickup_zone": request.get("pickup_zone"),
        "dropoff_zone": request.get("dropoff_zone"),
        "is_bridge_case": bool(request.get("is_bridge_case", False)),
        "driver_id": best.get("driver_id"),
        "score": round(best_score, 2),
        "reason": best_reason,
    }
