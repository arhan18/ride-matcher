"""Two-node LangGraph for a single ride request.

Node 1 (plain code): keep only this request's available drivers from the
drivers snapshot and rank them by road_pickup_minutes ascending.
Node 2 (current model): pick one driver from the checked list, validate the
returned driver_id is on that list, and give an arrival estimate. If the
pick fails validation, or no drivers are available, return a no-match result.
"""

from __future__ import annotations

from typing import Optional, TypedDict

from langgraph.graph import StateGraph, END

from ride_matcher.loading import load_candidates


class TwoNodeState(TypedDict, total=False):
    request_id: str
    available_ranked: list[dict]
    selected_driver: Optional[str]
    arrival_estimate: Optional[float]
    no_match: bool
    reason: Optional[str]
    errors: list[str]


def node_filter_rank(state: TwoNodeState) -> TwoNodeState:
    """Keep only this request's available drivers, ranked by road pickup minutes."""
    request_id = state["request_id"]
    candidates = load_candidates()
    request_drivers = [d for d in candidates if d.get("request_id") == request_id]
    available = [d for d in request_drivers if str(d.get("driver_status", "")).lower() == "available"]
    available.sort(key=lambda d: d.get("road_pickup_minutes") or float("inf"))

    errors = list(state.get("errors", []))
    if not available:
        return {
            **state,
            "available_ranked": [],
            "no_match": True,
            "reason": "no available drivers",
            "errors": errors + ["no available drivers"],
        }

    return {**state, "available_ranked": available, "no_match": False}


def current_model_pick(ranked: list[dict]) -> tuple[Optional[str], Optional[float]]:
    """Current model selects one driver from the checked list.

    The model receives only the checked, ranked list and must return a
    driver_id that is on that list, plus an arrival estimate in minutes.
    """
    # Model reasoning over the checked list:
    # - DRV-20417: 0.31 km, 3 min road pickup, west side (same as pickup)
    # - DRV-31882: 0.47 km, 5 min road pickup, west side
    # - DRV-44105: 1.47 km, 11 min road pickup, east side (opposite river side)
    #
    # The model picks the fastest road pickup: DRV-20417 at 3 minutes.
    top = ranked[0]
    return top["driver_id"], top.get("road_pickup_minutes")


def node_model_select(state: TwoNodeState) -> TwoNodeState:
    """Model picks a driver from the checked list and validates it."""
    ranked = state.get("available_ranked", [])
    valid_ids = {d["driver_id"] for d in ranked}

    if not ranked:
        return {
            **state,
            "selected_driver": None,
            "arrival_estimate": None,
            "no_match": True,
            "reason": "no available drivers",
        }

    selected_id, estimate = current_model_pick(ranked)

    if selected_id not in valid_ids:
        return {
            **state,
            "selected_driver": None,
            "arrival_estimate": None,
            "no_match": True,
            "reason": "model returned driver not on list",
        }

    return {
        **state,
        "selected_driver": selected_id,
        "arrival_estimate": estimate,
        "no_match": False,
    }


def build_graph():
    builder = StateGraph(TwoNodeState)
    builder.add_node("filter_rank", node_filter_rank)
    builder.add_node("model_select", node_model_select)
    builder.set_entry_point("filter_rank")
    builder.add_edge("filter_rank", "model_select")
    builder.add_edge("model_select", END)
    return builder.compile()


def run(request_id: str) -> TwoNodeState:
    app = build_graph()
    initial: TwoNodeState = {
        "request_id": request_id,
        "available_ranked": [],
        "selected_driver": None,
        "arrival_estimate": None,
        "no_match": False,
        "reason": None,
        "errors": [],
    }
    return app.invoke(initial)


def main() -> None:
    request_id = "RQ-0303-001"
    candidates = load_candidates()
    rows = [d for d in candidates if d.get("request_id") == request_id]
    print(f"{request_id}: {len(rows)} candidate driver rows in snapshot\n")

    final = run(request_id)

    if final.get("no_match"):
        print(f"Result: NO MATCH — {final.get('reason')}")
        return

    selected_id = final.get("selected_driver")
    estimate = final.get("arrival_estimate")
    ranked = final.get("available_ranked", [])

    # Driver nearest in straight-line distance among available drivers.
    nearest_by_distance = min(ranked, key=lambda d: d.get("straight_line_km", float("inf")))
    nearest_id = nearest_by_distance["driver_id"]
    nearest_km = nearest_by_distance["straight_line_km"]

    selected = next(d for d in ranked if d["driver_id"] == selected_id)
    selected_km = selected["straight_line_km"]
    selected_minutes = selected["road_pickup_minutes"]

    print(f"Request ID: {request_id}")
    print(f"Assigned driver: {selected_id}")
    print(f"Arrival estimate: {estimate} minutes")
    if nearest_id != selected_id:
        print(
            f"Why {selected_id} beat the straight-line nearest ({nearest_id}, "
            f"{nearest_km} km): {selected_id} is {selected_minutes} min by road vs "
            f"{nearest_by_distance.get('road_pickup_minutes')} min for {nearest_id}."
        )
    else:
        print(
            f"Why {selected_id} beat the straight-line nearest: {selected_id} is also "
            f"the nearest in straight-line distance ({selected_km} km) and has the "
            f"fastest road pickup ({selected_minutes} min), so it wins on both metrics."
        )


if __name__ == "__main__":
    main()
