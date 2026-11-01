"""Entry point: run the ride-matching graph and print assignments."""

from __future__ import annotations

from .graph import run


def main() -> None:
    assignments = run()
    print(f"{len(assignments)} ride requests processed\n")
    for a in assignments:
        print(
            f"{a['request_id']} | {a['rider_id']} | "
            f"{a['pickup_zone']} -> {a['dropoff_zone']} | "
            f"driver={a['driver_id'] or 'UNASSIGNED'} | "
            f"score={a['score']} | {a['reason']}"
        )


if __name__ == "__main__":
    main()
