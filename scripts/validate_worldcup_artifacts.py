from __future__ import annotations

import argparse
import csv
import json
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable


PROB_TOLERANCE = 0.002


@dataclass
class Finding:
    level: str
    path: str
    message: str


def _load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8-sig") as handle:
        return json.load(handle)


def _parse_datetime(value: Any) -> datetime | None:
    if value in (None, ""):
        return None
    text = str(value).replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        return None


def _as_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _check_probability_triple(values: Iterable[Any]) -> str | None:
    nums = [_as_float(value) for value in values]
    if any(value is None for value in nums):
        return "probability fields must be numeric"
    if any(value < 0 or value > 1 for value in nums if value is not None):
        return "probability fields must be between 0 and 1"
    total = sum(value for value in nums if value is not None)
    if abs(total - 1.0) > PROB_TOLERANCE:
        return f"probability fields must sum to 1.0 within {PROB_TOLERANCE}; got {total:.6f}"
    return None


def validate_score_payload(payload: dict[str, Any], path: str = "<payload>") -> list[Finding]:
    findings: list[Finding] = []
    required = [
        "match",
        "source_game_id",
        "probability_source",
        "prob_home",
        "prob_draw",
        "prob_away",
        "viewer_datetime",
        "utc_datetime",
        "stadium_datetime_iso",
        "calibrated_recommended_score",
        "primary_cluster",
        "top_scores",
    ]
    for key in required:
        if key not in payload or payload.get(key) in (None, ""):
            findings.append(Finding("error", path, f"missing required field: {key}"))

    prob_error = _check_probability_triple(
        (payload.get("prob_home"), payload.get("prob_draw"), payload.get("prob_away"))
    )
    if prob_error:
        findings.append(Finding("error", path, prob_error))

    for key in ("viewer_datetime", "utc_datetime", "stadium_datetime_iso"):
        if key in payload and _parse_datetime(payload.get(key)) is None:
            findings.append(Finding("error", path, f"{key} must be an ISO datetime"))

    if payload.get("leakage_safe") in (0, False, "0", "false", "False"):
        findings.append(Finding("error", path, "leakage_safe is false"))
    if "source_cutoff" not in payload:
        findings.append(Finding("warning", path, "source_cutoff is missing"))

    for list_key in ("primary_cluster", "top_scores"):
        rows = payload.get(list_key)
        if not isinstance(rows, list) or not rows:
            findings.append(Finding("error", path, f"{list_key} must be a non-empty list"))
            continue
        for idx, row in enumerate(rows, start=1):
            if not isinstance(row, dict):
                findings.append(Finding("error", path, f"{list_key}[{idx}] must be an object"))
                continue
            for field in ("score", "outcome", "probability", "rank_score"):
                if field not in row:
                    findings.append(Finding("error", path, f"{list_key}[{idx}] missing {field}"))
            probability = _as_float(row.get("probability"))
            if probability is None or probability < 0 or probability > 1:
                findings.append(Finding("error", path, f"{list_key}[{idx}].probability must be between 0 and 1"))
    return findings


def validate_score_json(path: Path) -> list[Finding]:
    payload = _load_json(path)
    if not isinstance(payload, dict):
        return [Finding("error", str(path), "score JSON root must be an object")]
    return validate_score_payload(payload, str(path))


def validate_score_summary_csv(path: Path) -> list[Finding]:
    findings: list[Finding] = []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        return [Finding("error", str(path), "score summary CSV has no rows")]

    required = {
        "source_game_id",
        "viewer_datetime",
        "viewer_timezone",
        "match",
        "probability_source",
        "recommended_score",
        "prob_home",
        "prob_draw",
        "prob_away",
    }
    missing = sorted(required - set(rows[0].keys()))
    for key in missing:
        findings.append(Finding("error", str(path), f"missing required column: {key}"))

    previous_dt: datetime | None = None
    for idx, row in enumerate(rows, start=2):
        prob_error = _check_probability_triple((row.get("prob_home"), row.get("prob_draw"), row.get("prob_away")))
        if prob_error:
            findings.append(Finding("error", str(path), f"row {idx}: {prob_error}"))
        viewer_dt = _parse_datetime(row.get("viewer_datetime"))
        if viewer_dt is None:
            findings.append(Finding("error", str(path), f"row {idx}: viewer_datetime must be ISO datetime"))
        elif previous_dt and viewer_dt < previous_dt:
            findings.append(Finding("error", str(path), f"row {idx}: viewer_datetime order decreased"))
        previous_dt = viewer_dt or previous_dt
    return findings


def validate_schedule_audit_json(path: Path) -> list[Finding]:
    payload = _load_json(path)
    findings: list[Finding] = []
    if not isinstance(payload, dict):
        return [Finding("error", str(path), "schedule audit JSON root must be an object")]
    if payload.get("all_stadium_timezones_known") is not True:
        findings.append(Finding("error", str(path), "all_stadium_timezones_known must be true"))
    if payload.get("loader_after_fix_utc_inversions") != 0:
        findings.append(Finding("error", str(path), "loader_after_fix_utc_inversions must be 0"))
    if payload.get("source_id_order_utc_inversions", 0) > 0:
        findings.append(Finding("warning", str(path), "source_game_id order is not chronological; use UTC order"))
    return findings


def findings_to_dict(findings: list[Finding]) -> list[dict[str, str]]:
    return [{"level": item.level, "path": item.path, "message": item.message} for item in findings]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate World Cup prediction artifacts")
    parser.add_argument("--score-json", action="append", type=Path, default=[])
    parser.add_argument("--score-summary-csv", action="append", type=Path, default=[])
    parser.add_argument("--schedule-audit-json", action="append", type=Path, default=[])
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args(argv)

    findings: list[Finding] = []
    for path in args.score_json:
        findings.extend(validate_score_json(path))
    for path in args.score_summary_csv:
        findings.extend(validate_score_summary_csv(path))
    for path in args.schedule_audit_json:
        findings.extend(validate_schedule_audit_json(path))

    if args.as_json:
        print(json.dumps({"findings": findings_to_dict(findings)}, indent=2))
    else:
        if not findings:
            print("OK: all checked artifacts passed")
        for finding in findings:
            print(f"{finding.level.upper()}: {finding.path}: {finding.message}")

    return 1 if any(finding.level == "error" for finding in findings) else 0


if __name__ == "__main__":
    raise SystemExit(main())
