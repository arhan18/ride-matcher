"""Shared graph state for the ride-matching LangGraph."""

from __future__ import annotations

from typing import List, TypedDict


class DriverCandidate(TypedDict, total=False):
    """One candidate driver row, enriched with a match score."""

    request_id: str
    driver_id: str
    driver_status: str
    driver_lat: float
    driver_lng: float
    driver_river_side: str
    straight_line_km: float
    road_pickup_minutes: float | None
    route_note: str
    score: float


class Assignment(TypedDict, total=False):
    """Final driver assignment for a single ride request."""

    request_id: str
    rider_id: str
    pickup_zone: str
    dropoff_zone: str
    is_bridge_case: bool
    driver_id: str | None
    score: float | None
    reason: str


class RideMatchState(TypedDict):
    """State carried between LangGraph nodes."""

    requests: List[dict]
    candidates: List[dict]
    assignments: List[Assignment]
    errors: List[str]
