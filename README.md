# ride-matcher

Two-node LangGraph that matches a single Uber ride request to an available driver.

## Data

- `data/uber_ride_requests_test_set.csv` — ride requests.
- `data/uber_candidate_drivers_snapshot.csv` — candidate drivers per request.

Both files live in `data/` and are loaded from this folder.

## Graph (two nodes)

`START → filter_rank → model_select → END`

**Node 1 — filter_rank (plain code):** keeps only the request's candidate rows from the drivers snapshot where `driver_status == "available"`, then ranks them by `road_pickup_minutes` ascending (not straight-line distance). Drivers with any other status (`offline`, `on_trip`) are filtered out before anything reaches node 2.

**Node 2 — model_select (current model):** receives only the checked, ranked list from node 1. The model picks one `driver_id` from that list and gives an arrival estimate in minutes. Node 2 validates that the returned `driver_id` is on the checked list. If the pick fails validation, or the request has no available driver, the graph returns a no-match result instead of a driver.

## Run output — request RQ-0303-001

Request RQ-0303-001 has 4 candidate driver rows in the snapshot; 3 are available and 1 (`DRV-27760`) is offline and filtered out.

Checked drivers ranked by road pickup minutes:
- DRV-20417 — 3.0 min (straight-line 0.31 km, west side)
- DRV-31882 — 5 min (straight-line 0.47 km, west side)
- DRV-44105 — 11 min (straight-line 1.47 km, east side)

```
Request ID: RQ-0303-001
Assigned driver: DRV-20417
Arrival estimate: 3.0 minutes
```

Why DRV-20417 beat the straight-line nearest: DRV-20417 is also the nearest in straight-line distance (0.31 km) and has the fastest road pickup (3.0 min), so it wins on both metrics.

## OpenRouter Activity screenshot

**Not available.** No OpenRouter call was made in this run — per instruction, OpenRouter was skipped and the current model was used directly. Therefore `docs/openrouter-activity.png` does not exist and there is no OpenRouter Activity call to screenshot.

## Plan-mode prompt

Original plan-mode instruction:

> Plan a two-node LangGraph graph for one ride request. Node one is plain code: it keeps only that request's available drivers from the drivers snapshot and ranks them by estimated road pickup minutes, not straight-line distance. Node two sends only that checked list to the OpenRouter model named in config and asks it to pick one driver and give an arrival estimate. Do not write any code later.

Subsequent pushbacks applied:
- Skip OpenRouter; use the current model.
- Node 2 validates the returned `driver_id` is on the checked list; if not, or if no drivers are available, return a no-match result.

## Pushback line — gap found and how the approved plan closed it

Gap in the first plan: node 2 blindly trusted the model's returned `driver_id` without checking it was on the checked list, and there was no handling for a request with no available driver. The approved plan closed it by adding validation in node 2 (confirm the returned id is on the checked list) and returning a no-match result instead of a driver when the pick fails validation or no drivers are available.

## Config check

`.env` is not committed (it does not exist; `.gitignore` excludes `.env` anyway).

## Run

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
python run_two_node.py
```

## Repository

https://github.com/arhan18/ride-matcher
