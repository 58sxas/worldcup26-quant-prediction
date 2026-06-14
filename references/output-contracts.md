# Output Contracts

## Schedule and timezone contract

World Cup 2026 schedules must be sorted by true UTC time, not `source_game_id` and not stadium-local clock alone.

Required schedule fields:

```text
source_game_id
match
stadium
stadium_timezone
stadium_datetime or stadium_datetime_iso
utc_datetime
viewer_datetime or taipei_datetime
viewer_timezone when viewer_datetime is used
```

Trust a schedule audit only when:

```text
all_stadium_timezones_known = true
loader_after_fix_utc_inversions = 0
```

Known unsafe pattern:

```text
source_id_order_utc_inversions > 0
```

That means source IDs are not chronological.

## Exact-score JSON contract

Required top-level fields:

```text
match
source_game_id
probability_source
prob_home
prob_draw
prob_away
stadium_timezone
stadium_datetime_iso
utc_datetime
viewer_timezone
viewer_datetime
calibrated_recommended_score
primary_cluster
top_scores
source_cutoff
leakage_safe
```

Validation rules:

- `prob_home + prob_draw + prob_away` should be within 0.002 of 1.0.
- Probabilities must be between 0 and 1.
- `leakage_safe` should be `1` or `true` when present.
- `primary_cluster` and `top_scores` rows should contain `score`, `outcome`, `probability`, and `rank_score`.
- `viewer_datetime`, `utc_datetime`, and `stadium_datetime_iso` should parse as ISO datetimes.

## Score-summary CSV contract

Recommended columns:

```text
source_game_id
viewer_datetime
viewer_timezone
stadium_datetime
stadium_timezone
match
stadium
probability_source
recommended_score
prob_home
prob_draw
prob_away
```

Rows must be ordered by `viewer_datetime` or by `utc_datetime` if present. Do not use `source_game_id` for final display order.

## Live prediction contract

For 1X2 odds comparison, include:

```text
match_date
match_num
home_team
away_team
odds_home
odds_draw
odds_away
market_prob_home
market_prob_draw
market_prob_away
prob_home
prob_draw
prob_away
edge_home_pp
edge_draw_pp
edge_away_pp
ev_home_pct
ev_draw_pct
ev_away_pct
best_outcome
best_ev_pct
recommendation
leakage_safe
source_match_cutoff
```

`recommendation` values should be conservative:

- `action_home`, `action_draw`, `action_away`: passes minimum edge and EV thresholds.
- `watch_home`, `watch_draw`, `watch_away`: edge exists but action threshold is not met.
- `no_bet`: no actionable edge.

## Tournament output contract

Title table fields:

```text
team
champion_prob
fair_title_odds
fair_title_odds_text
advance_r32_prob
advance_r16_prob
advance_qf_prob
advance_sf_prob
advance_final_prob
group_winner_prob
group_runner_up_prob
group_third_prob
avg_group_points
```

Final-pair rows are unordered when matching China Sports Lottery champion-runner-up pair selections. For example, `France-Spain` and `Spain-France` should be treated as the same pair if the market rules do so.

## Answer template

For a match prediction, answer in this order:

```text
Match and time
1X2 table
Ranked exact-score table
Most likely scorelines: score (probability), score (probability), ...
Notes: probability source, leakage/timezone caveat, direct vs derived exact-score status
```

For stake sizing:

```text
Strict Kelly table
Forced allocation table, only if requested
Short note that forced allocation is not optimal if EV is negative
```
