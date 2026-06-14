from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_script(name: str):
    path = ROOT / "scripts" / name
    spec = importlib.util.spec_from_file_location(name.removesuffix(".py"), path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


validate = load_script("validate_worldcup_artifacts.py")
format_score = load_script("format_score_answer.py")
kelly = load_script("kelly_exact_scores.py")


class SkillScriptTests(unittest.TestCase):
    def test_example_artifacts_validate(self) -> None:
        findings = []
        findings.extend(validate.validate_score_json(ROOT / "examples" / "score_prediction_sample.json"))
        findings.extend(validate.validate_score_summary_csv(ROOT / "examples" / "score_summary_sample.csv"))
        findings.extend(validate.validate_schedule_audit_json(ROOT / "examples" / "schedule_audit_sample.json"))
        errors = [finding for finding in findings if finding.level == "error"]

        self.assertEqual(errors, [])

    def test_format_score_answer_contains_recommendation(self) -> None:
        import json

        payload = json.loads((ROOT / "examples" / "score_prediction_sample.json").read_text(encoding="utf-8"))
        rendered = format_score.render_markdown(payload, top=3)

        self.assertIn("Qatar vs Switzerland", rendered)
        self.assertIn("Recommended score: `0-2`", rendered)
        self.assertIn("| 1 | 0-2 |", rendered)

    def test_strict_kelly_zero_for_negative_ev(self) -> None:
        self.assertEqual(kelly.strict_kelly_fraction(0.10, 5.0), 0.0)

    def test_forced_allocation_sums_to_total(self) -> None:
        rows = [
            {"selection": "0-0", "probability": 0.10, "odds": 6.0},
            {"selection": "1-1", "probability": 0.12, "odds": 5.0},
        ]
        table = kelly.build_stake_table(rows, bankroll=1000, kelly_fraction=0.25, forced_total=100, forced_power=1.0)

        self.assertAlmostEqual(sum(row["forced_stake"] for row in table), 100.0)
        self.assertTrue(all(row["strict_stake"] == 0 for row in table))

    def test_kelly_cli_writes_csv(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "stakes.csv"
            rc = kelly.main(
                [
                    str(ROOT / "examples" / "exact_score_odds_sample.csv"),
                    "--bankroll",
                    "1000",
                    "--forced-total",
                    "100",
                    "--output",
                    str(output),
                ]
            )
            self.assertEqual(rc, 0)
            self.assertIn("forced_stake", output.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
