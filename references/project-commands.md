# Project Commands

Use these commands in a compatible repository that contains the `worldcup_quant` Python package.

## Setup

```powershell
python -m pip install -r requirements.txt
```

## Data layer

```powershell
python -m worldcup_quant.pipeline build
python -m worldcup_quant.pipeline validate
```

Optional public API context:

```powershell
python -m worldcup_quant.api_sources verify
python -m worldcup_quant.api_sources fetch-worldcup26
python -m worldcup_quant.api_sources ingest-db
python -m worldcup_quant.api_sources validate-db
```

Expected coverage in the source project after `fetch-worldcup26`:

```text
games: 104
groups: 12
teams: 48
stadiums: 16
country metadata: 48/48
stadium geocodes: 16/16
stadium weather forecasts: 16/16
```

## Feature and model validation

```powershell
python -m worldcup_quant.modeling build-features
python -m worldcup_quant.modeling validate-features
python -m worldcup_quant.modeling build-competition-features
python -m worldcup_quant.modeling validate-competition-features
python -m worldcup_quant.modeling evaluate-elo
python -m worldcup_quant.modeling evaluate-cfwc
```

## Single-match 1X2 prediction

```powershell
python -m worldcup_quant.modeling predict --home Argentina --away France --date 2026-06-20 --neutral
python -m worldcup_quant.modeling predict-cfwc --home Argentina --away France --date 2026-06-20 --stage "Group" --neutral
```

Use `--market-probs HOME DRAW AWAY` only when the probabilities are already de-vigged and sum to one.

## Live odds prediction

Current source:

```powershell
python -m worldcup_quant.live_predictions
python -m worldcup_quant.live_predictions --date-from 2026-06-11 --date-to 2026-06-13
python -m worldcup_quant.live_predictions --no-store
```

Manual CSV fallback:

```powershell
python -m worldcup_quant.live_predictions --source csv --odds-csv path\to\odds.csv --no-store
```

Expected CSV columns for manual odds:

```text
home,away,odds_home,odds_draw,odds_away,match_date
```

## Exact score prediction

```powershell
python -m worldcup_quant.score_predictions --source-game-id 8 --viewer-timezone Asia/Taipei
python -m worldcup_quant.score_predictions --source-game-ids 8 7 5 6 --viewer-timezone Asia/Taipei
```

The score command writes one JSON payload and one score-row CSV per match when `--output-dir` is set or defaults to `data/outputs`.

## Tournament simulation

```powershell
python -m worldcup_quant.tournament_simulation --method monte-carlo --simulations 100000
python -m worldcup_quant.tournament_simulation --method exact-outcome
python -m worldcup_quant.tournament_simulation --method both --simulations 100000
```

Optional China Sports Lottery champion-runner-up pair CSV:

```powershell
python -m worldcup_quant.tournament_simulation --method both --simulations 100000 --official-final-pair-odds-csv data\manual\china_sports_lottery_final_pair_odds_20260612.csv
```

## Tests

```powershell
python -m unittest discover -s tests
```

## Windows notes

If Chinese markdown appears garbled in PowerShell:

```powershell
[Console]::OutputEncoding=[System.Text.Encoding]::UTF8
Get-Content -Raw -Encoding UTF8 README.md
```

For inline Python in PowerShell, use:

```powershell
@'
print("hello")
'@ | python -
```

Do not use Bash-style `python - <<'PY'` in PowerShell.
