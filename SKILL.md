---
name: worldcup26-quant-prediction
description: End-to-end World Cup 2026 quant workflow for leakage-safe data ingestion, 90-minute 1X2 probability modeling, exact-score ranking, Taiwan-local schedule ordering, China Sports Lottery odds comparison, tournament title simulation, and Kelly or forced-stake sizing. Use when Codex needs to work on a World Cup quant repository, predict World Cup matches, audit match dates or timezone ordering, generate ranked score probabilities, compare model probabilities with de-vigged odds, or turn exact-score probabilities into practical betting guidance.
---

# World Cup 26 Quant Prediction

Use this skill to execute and explain the World Cup quant method as a reproducible workflow, not as a one-off sports opinion. The core job is to produce auditable 90-minute 1X2 probabilities, exact-score rankings, tournament simulations, and stake guidance while preserving chronological correctness and avoiding future-data leakage.

## First Move

1. Locate the project root. Prefer a repository that contains `worldcup_quant/`, `data_sources.yml`, `requirements.txt`, and `data/outputs/`.
2. If the user asks for current odds, current schedules, or latest team context, refresh or verify the live inputs before answering.
3. On Windows PowerShell, read UTF-8 project files with `Get-Content -Encoding UTF8` if Chinese text appears garbled.
4. Run or inspect validation before trusting generated predictions:

```powershell
python -m worldcup_quant.pipeline validate
python -m worldcup_quant.modeling validate-features
python -m worldcup_quant.modeling validate-competition-features
python scripts/validate_worldcup_artifacts.py --schedule-audit-json data/outputs/schedule_audit/worldcup26_time_order_audit.json
```

## Workflow

### 1. Rebuild the data layer

Start from ingestion and validation before changing models. Rebuild the SQLite database, fetch the no-key World Cup 2026 context bundle, ingest API data, then validate. See `references/project-commands.md` for the command sequence.

Keep raw files immutable under `data/raw`. Every derived feature must carry a source timestamp such as `source_observed_at`, `available_time`, `source_snapshot_date`, or `source_match_cutoff`.

### 2. Build 90-minute 1X2 probabilities

The target is always regulation-time home/draw/away probability. Use `CF-WC` as the default production model when available. It blends:

- `market_m0`: de-vigged bookmaker consensus.
- `pi_gbm`: pi-style rating, attack/defense rating, rolling form, rest, and stage context.
- `rating_knn`: distance-weighted KNN on compact rating/recency features.
- `poisson_rating`: rating/scoring indicators converted through a Poisson score model.
- `sequence_deep`: leakage-safe last-10-match LSTM sequence model.
- `elo_form_logit`: low-variance Elo/form logistic baseline.

When market odds are present, treat the market as the anchor and model components as residual correction. When market odds are absent, redistribute market weight across skill-only models; never treat missing market probability as zero.

### 3. Generate exact scores

Exact scores are derived from calibrated expected goals fitted to the 1X2 probabilities. Prefer project outputs from `worldcup_quant.score_predictions` when available.

```powershell
python -m worldcup_quant.score_predictions --source-game-id 8 --viewer-timezone Asia/Taipei
python -m worldcup_quant.score_predictions --source-game-ids 8 7 5 6 --viewer-timezone Asia/Taipei
```

Report both the calibrated recommended score and a ranked score-probability list. If the score list was derived from 1X2 rather than a direct exact-score model, state that clearly.

### 4. Audit chronology and timezone order

Do not sort user-facing World Cup 2026 schedules by `source_game_id`. Do not group by stadium-local date alone. Sort internally by UTC, then present in the user's viewer timezone, usually `Asia/Taipei`.

Trust outputs only when they include `viewer_datetime`, `utc_datetime`, and `stadium_datetime_iso`, and when `loader_after_fix_utc_inversions` is zero in the schedule audit.

### 5. Compare odds and value

For decimal 1X2 odds, de-vig before comparing with model probabilities:

```text
raw_implied_i = 1 / decimal_odds_i
fair_market_prob_i = raw_implied_i / sum(raw_implied)
model_fair_odds_i = 1 / model_prob_i
EV_i = model_prob_i * decimal_odds_i - 1
```

Use `worldcup_quant.live_predictions` for current China Sports Lottery style 1X2 rows, or a manual CSV when the source site is unavailable.

### 6. Simulate the tournament

Use `worldcup_quant.tournament_simulation` for advancement, title, and final-pair probabilities. Monte Carlo title odds are derived from simulated frequencies. They are not direct inversions of single-match odds.

Use the exact-outcome method for deterministic group-state enumeration when the user wants a cleaner structural check. Use Monte Carlo when the user wants final-pair distributions, sample paths, or full title tables.

### 7. Size stakes

For mutually exclusive exact-score selections, independent single-bet Kelly can overstate risk. Always separate:

- Strict Kelly: zero stake on negative-EV selections.
- Forced allocation: a non-optimal entertainment or coverage allocation when the user explicitly wants every selection bought.

Use `scripts/kelly_exact_scores.py` for reproducible stake tables.

## Answer Style

Put the direct table first. For match predictions, show 1X2 probabilities, then the ranked score list, and end with the most likely scorelines and probabilities.

If the user questions dates or ordering, treat it as a full timezone audit. Use exact dates and include both viewer time and stadium time when relevant.

If the user says "same method", reuse this workflow without re-explaining the whole system.

## References

Read these files only when the task needs the detail:

- `references/project-commands.md`: concrete command recipes.
- `references/methodology.md`: model stack, exact-score method, tournament simulation, and staking logic.
- `references/output-contracts.md`: required output fields and answer formats.
- `references/data-sources-and-leakage.md`: source tiers, timing contract, and anti-leakage rules.

## Bundled Scripts

- `scripts/validate_worldcup_artifacts.py`: validate score JSON, score summary CSV, and schedule audit JSON.
- `scripts/format_score_answer.py`: turn a score prediction JSON into a concise markdown answer table.
- `scripts/kelly_exact_scores.py`: compute strict Kelly and optional forced allocations for exact-score selections.
