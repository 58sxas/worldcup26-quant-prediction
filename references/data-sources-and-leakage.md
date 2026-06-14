# Data Sources and Leakage Rules

## Timing contract

Every feature must satisfy:

```text
source_observed_at <= feature_available_time <= prediction_time < kickoff_time
```

Use prediction tiers:

- `pre_tournament`: schedule, stadiums, qualified teams, historical ratings, official squads, historical squad values.
- `pre_match_24h`: odds movement, public injuries, rest/travel, forecast weather.
- `pre_match_1h`: official lineups, substitutes, last market prices.

Do not use `pre_match_1h` information to evaluate a `pre_match_24h` strategy.

## Current integrated sources

Core public sources from the source project:

- International football results.
- OpenFootball World Cup schedule/results.
- Football-Data.co.uk World Cup and qualifier odds.
- WorldCup26 open API for 2026 games, groups, teams, and stadiums.
- REST Countries for country metadata.
- Nominatim and Wikidata for venue geocoding.
- Open-Meteo forecast for future match weather.
- football-data.org public competition catalog.

## High-value next sources

Add sources in this order when extending the model:

1. FIFA ranking and World Football Elo snapshots.
2. Official squads and player identity tables.
3. Historical market-value snapshots and position-weighted squad features.
4. 2026 venue, rest, travel, base-camp, weather, and altitude features.
5. Richer odds markets: Asian handicap, totals, opening/closing movement, exchange liquidity.
6. Event/xG/tactical data only after the anti-leakage pipeline is stable.

## Source categories

Use these labels in notes and docs:

- `verified_direct`: URL or no-key API works directly.
- `manual_or_auth`: Kaggle, API key, manual download, or paid source is required.
- `monitor`: useful but unstable, unclear, license-sensitive, or not yet structurally verified.

## Do not do

- Do not train complex models only on World Cup matches.
- Do not use random splits as the headline validation.
- Do not use closing odds for bets simulated before closing.
- Do not use post-match stats, xG, shots, confirmed lineups, injuries, or realized weather unless they were available at the simulated prediction time.
- Do not use current player market values to evaluate old tournaments unless historical valuation dates exist.
- Do not fill missing player values as zero strength; use missingness flags and fallback ratings.
- Do not let same-day matches leak into each other. Generate same-day pre-match features first, then batch update Elo or form states.
- Do not claim betting value from a model that merely reuses the same market probability without independent signal or a validated market-mispricing layer.

## Source matching

Maintain explicit alias and ID tables:

```text
team_aliases
player_aliases
source_team_ids
source_player_ids
```

Known team-name normalization examples:

```text
Curacao <-> Curaçao
DR Congo <-> Democratic Republic of the Congo
United States <-> USA or Chinese source names
Bosnia and Herzegovina <-> Bosnia or Chinese source names
```

Always keep raw source names alongside normalized names so mismatches can be audited.
