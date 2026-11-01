"""Tests for ride-matching scoring and selection."""

from ride_matcher.matching import score_candidate, filter_available, select_driver


def test_prefers_same_river_side():
    request = {"pickup_river_side": "west", "is_bridge_case": False}
    same = {
        "driver_id": "DRV-A",
        "driver_status": "available",
        "driver_river_side": "west",
        "straight_line_km": 1.0,
        "road_pickup_minutes": 3.0,
    }
    other = {
        "driver_id": "DRV-B",
        "driver_status": "available",
        "driver_river_side": "east",
        "straight_line_km": 1.0,
        "road_pickup_minutes": 3.0,
    }
    score_a, _ = score_candidate(request, same)
    score_b, _ = score_candidate(request, other)
    assert score_a > score_b


def test_filters_only_available():
    drivers = [
        {"driver_status": "available"},
        {"driver_status": "offline"},
        {"driver_status": "busy"},
    ]
    assert len(filter_available(drivers)) == 1


def test_selects_none_when_no_available_driver():
    request = {
        "request_id": "RQ-X",
        "rider_id": "RD-X",
        "pickup_zone": "A",
        "dropoff_zone": "B",
        "is_bridge_case": False,
    }
    result = select_driver(request, [{"driver_status": "offline"}])
    assert result["driver_id"] is None
    assert result["reason"] == "no available driver"
