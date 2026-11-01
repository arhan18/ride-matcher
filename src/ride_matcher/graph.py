"""LangGraph definition for ride matching."""

from __future__ import annotations

from langgraph.graph import StateGraph, END

from . import loading, matching
from .state import RideMatchState


def node_load_requests(state: RideMatchState) -> RideMatchState:
    requests = loading.load_requests()
    errors = list(state.get("errors", []))
    if not requests:
        errors.append("No ride requests loaded.")
    return {"requests": requests, "errors": errors}


def node_load_candidates(state: RideMatchState) -> RideMatchState:
    candidates = loading.load_candidates()
    errors = list(state.get("errors", []))
    if not candidates:
        errors.append("No candidate drivers loaded.")
    return {"candidates": candidates, "errors": errors}


def node_filter_and_score(state: RideMatchState) -> RideMatchState:
    requests = state.get("requests", [])
    candidates = state.get("candidates", [])
    errors = list(state.get("errors", []))

    # Index candidates by request_id for fast lookup.
    by_request: dict[str, List[dict]] = {}
    for driver in candidates:
        by_request.setdefault(str(driver.get("request_id", "")), []).append(driver)

    assignments: List[dict] = []
    for request in requests:
        request_candidates = by_request.get(str(request.get("request_id", "")), [])
        assignments.append(matching.select_driver(request, request_candidates))

    return {"assignments": assignments, "errors": errors}


def node_format_output(state: RideMatchState) -> RideMatchState:
    """Hook for future output formatting; passes state through unchanged."""
    return state


def build_app():
    builder = StateGraph(RideMatchState)
    builder.add_node("load_requests", node_load_requests)
    builder.add_node("load_candidates", node_load_candidates)
    builder.add_node("filter_and_score", node_filter_and_score)
    builder.add_node("format_output", node_format_output)

    builder.set_entry_point("load_requests")
    builder.add_edge("load_requests", "load_candidates")
    builder.add_edge("load_candidates", "filter_and_score")
    builder.add_edge("filter_and_score", "format_output")
    builder.add_edge("format_output", END)

    return builder.compile()


def run() -> List[dict]:
    app = build_app()
    initial: RideMatchState = {
        "requests": [],
        "candidates": [],
        "assignments": [],
        "errors": [],
    }
    final = app.invoke(initial)
    return final.get("assignments", [])
