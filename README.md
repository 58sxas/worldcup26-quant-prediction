# World Cup 26 Quant Prediction Skill

This repository contains a Codex skill package for World Cup 2026 quant work: data validation, 90-minute 1X2 modeling, exact-score ranking, timezone-safe schedule output, odds comparison, tournament simulation, and stake sizing.

## Contents

- `SKILL.md`: main Codex instructions and trigger metadata.
- `agents/openai.yaml`: UI metadata for Codex skill lists.
- `references/`: detailed workflow notes and output contracts.
- `scripts/`: standalone helper scripts with no third-party dependencies.
- `examples/`: small sample inputs and outputs for users and tests.
- `tests/`: standard-library unit tests for bundled scripts.

## Install

Copy this folder as `worldcup26-quant-prediction` into a Codex skills directory, for example:

```powershell
$dest = Join-Path $env:USERPROFILE ".codex\skills\worldcup26-quant-prediction"
Copy-Item -Recurse -Force . $dest
```

Then restart Codex so the skill metadata can be discovered.

## Validate

From the repository root:

```powershell
python -m unittest discover -s tests
python scripts/validate_worldcup_artifacts.py --score-json examples/score_prediction_sample.json
python scripts/format_score_answer.py examples/score_prediction_sample.json --top 4
python scripts/kelly_exact_scores.py examples/exact_score_odds_sample.csv --bankroll 1000 --forced-total 100
```

This skill does not bundle the full model database. It captures the reusable operating method and helper tooling for a compatible World Cup quant repository.
