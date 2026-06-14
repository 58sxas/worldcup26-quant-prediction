from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def _pct(value: Any) -> str:
    return f"{float(value) * 100:.1f}%"


def _score_rows(payload: dict[str, Any], top: int) -> list[dict[str, Any]]:
    rows = payload.get("primary_cluster") or payload.get("top_scores") or []
    if len(rows) < top:
        seen = {row.get("score") for row in rows if isinstance(row, dict)}
        for row in payload.get("top_scores") or []:
            if row.get("score") not in seen:
                rows.append(row)
                seen.add(row.get("score"))
            if len(rows) >= top:
                break
    return rows[:top]


def render_markdown(payload: dict[str, Any], *, top: int = 6) -> str:
    lines = []
    lines.append(f"## {payload.get('match', 'World Cup match')}")
    if payload.get("viewer_datetime"):
        lines.append(f"Time: {payload['viewer_datetime']} ({payload.get('viewer_timezone', 'viewer local')})")
    if payload.get("stadium_datetime_iso"):
        lines.append(f"Stadium time: {payload['stadium_datetime_iso']} ({payload.get('stadium_timezone', 'stadium local')})")
    lines.append("")
    lines.append("| Outcome | Probability |")
    lines.append("|---|---:|")
    lines.append(f"| Home | {_pct(payload.get('prob_home', 0))} |")
    lines.append(f"| Draw | {_pct(payload.get('prob_draw', 0))} |")
    lines.append(f"| Away | {_pct(payload.get('prob_away', 0))} |")
    lines.append("")
    lines.append(f"Recommended score: `{payload.get('calibrated_recommended_score', payload.get('raw_top_score', 'n/a'))}`")
    lines.append("")
    lines.append("| Rank | Score | Outcome | Probability | Rank score |")
    lines.append("|---:|---|---|---:|---:|")
    for idx, row in enumerate(_score_rows(payload, top), start=1):
        lines.append(
            f"| {idx} | {row.get('score')} | {row.get('outcome')} | "
            f"{_pct(row.get('probability', 0))} | {float(row.get('rank_score', 0)):.4f} |"
        )
    source = payload.get("probability_source")
    leakage = payload.get("leakage_safe")
    if source or leakage is not None:
        lines.append("")
        lines.append(f"Source: `{source or 'unknown'}`; leakage_safe: `{leakage}`.")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Format a World Cup exact-score JSON as markdown")
    parser.add_argument("score_json", type=Path)
    parser.add_argument("--top", type=int, default=6)
    args = parser.parse_args(argv)

    with args.score_json.open("r", encoding="utf-8-sig") as handle:
        payload = json.load(handle)
    print(render_markdown(payload, top=args.top))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
