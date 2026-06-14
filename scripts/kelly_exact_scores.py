from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path
from typing import Any


def strict_kelly_fraction(probability: float, decimal_odds: float) -> float:
    if decimal_odds <= 1.0:
        return 0.0
    fraction = (probability * decimal_odds - 1.0) / (decimal_odds - 1.0)
    return max(0.0, fraction)


def _as_probability(value: Any) -> float:
    probability = float(value)
    if probability > 1.0:
        probability /= 100.0
    return probability


def _selection(row: dict[str, str]) -> str:
    return row.get("selection") or row.get("score") or row.get("outcome") or "selection"


def load_rows(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    parsed = []
    for idx, row in enumerate(rows, start=1):
        try:
            probability = _as_probability(row.get("probability"))
            odds = float(row.get("odds") or row.get("decimal_odds"))
        except (TypeError, ValueError) as exc:
            raise ValueError(f"row {idx} must include numeric probability and odds") from exc
        parsed.append(
            {
                "selection": _selection(row),
                "probability": probability,
                "odds": odds,
            }
        )
    return parsed


def build_stake_table(
    rows: list[dict[str, Any]],
    *,
    bankroll: float,
    kelly_fraction: float,
    forced_total: float | None,
    forced_power: float,
) -> list[dict[str, Any]]:
    table = []
    forced_weights = []
    for row in rows:
        probability = float(row["probability"])
        odds = float(row["odds"])
        ev = probability * odds - 1.0
        strict_fraction = strict_kelly_fraction(probability, odds)
        table.append(
            {
                "selection": row["selection"],
                "probability": probability,
                "odds": odds,
                "ev_pct": ev * 100.0,
                "strict_kelly_fraction": strict_fraction,
                "strict_stake": bankroll * kelly_fraction * strict_fraction,
                "forced_stake": 0.0,
                "note": "positive_ev" if ev > 0 else "strict_kelly_zero",
            }
        )
        forced_weights.append(max(ev, 0.0) ** forced_power)

    if forced_total is not None:
        if sum(forced_weights) <= 0:
            forced_weights = [max(float(row["probability"]), 0.0) for row in rows]
            forced_note = "forced_allocation_probability_weighted_negative_ev"
        else:
            forced_note = "forced_allocation_positive_ev_weighted"
        total_weight = sum(forced_weights) or 1.0
        for output, weight in zip(table, forced_weights):
            output["forced_stake"] = forced_total * weight / total_weight
            output["note"] = forced_note if output["ev_pct"] <= 0 else output["note"] + "+forced"
    return table


def write_rows(rows: list[dict[str, Any]], output: Path | None) -> None:
    fieldnames = [
        "selection",
        "probability",
        "odds",
        "ev_pct",
        "strict_kelly_fraction",
        "strict_stake",
        "forced_stake",
        "note",
    ]
    handle = output.open("w", encoding="utf-8", newline="") if output else sys.stdout
    close = output is not None
    try:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    "selection": row["selection"],
                    "probability": f"{row['probability']:.6f}",
                    "odds": f"{row['odds']:.3f}",
                    "ev_pct": f"{row['ev_pct']:.3f}",
                    "strict_kelly_fraction": f"{row['strict_kelly_fraction']:.6f}",
                    "strict_stake": f"{row['strict_stake']:.2f}",
                    "forced_stake": f"{row['forced_stake']:.2f}",
                    "note": row["note"],
                }
            )
    finally:
        if close:
            handle.close()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Compute strict Kelly and optional forced exact-score allocations")
    parser.add_argument("input_csv", type=Path)
    parser.add_argument("--bankroll", type=float, default=1000.0)
    parser.add_argument("--kelly-fraction", type=float, default=0.25)
    parser.add_argument("--forced-total", type=float, default=None)
    parser.add_argument("--forced-power", type=float, default=1.0)
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args(argv)

    rows = load_rows(args.input_csv)
    table = build_stake_table(
        rows,
        bankroll=args.bankroll,
        kelly_fraction=args.kelly_fraction,
        forced_total=args.forced_total,
        forced_power=args.forced_power,
    )
    write_rows(table, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
