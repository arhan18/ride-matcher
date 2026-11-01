# ride-matcher

LangGraph project that matches Uber ride requests to available candidate drivers.

## Data

- `data/uber_ride_requests_test_set.csv` — ride requests (request, rider, pickup/dropoff zones & coordinates, bridge-case flag).
- `data/uber_candidate_drivers_snapshot.csv` — candidate drivers per request (status, location, distance, road pickup ETA).

Both files are loaded from this folder.

## Graph

`load_requests` → `load_candidates` → `filter_and_score` → `format_output`

Each request is scored against its available drivers by distance, same-river-side preference, and road pickup ETA. The best driver is assigned, or the request is left unassigned with a reason when no driver is available.

## Run

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
python -m ride_matcher
```

## Tests

```bash
pip install -e .[dev]
pytest
```
