# Methodology

## Target

The primary target is calibrated 90-minute 1X2 probability:

```text
P(home win), P(draw), P(away win)
```

Knockout advancement, title odds, exact scores, totals, and stakes are downstream products. Do not mix extra time or penalties into the base 1X2 probability unless the task explicitly asks for advancement.

## Data-first build order

1. Build raw ingestion and local SQLite tables.
2. Validate schema, row counts, probability normalization, and source matching.
3. Build leakage-safe features with explicit availability timestamps.
4. Establish market and Elo baselines.
5. Add `CF-WC` competition features and ensemble models.
6. Produce exact-score and tournament outputs only after the base probability layer is healthy.

## CF-WC model stack

Use `CF-WC` as the default production ensemble when the compatible project already has it implemented.

Component roles:

- `market_m0`: de-vigged bookmaker consensus. This is a strong baseline and the default anchor when odds are available.
- `pi_gbm`: pi-style team strength, attack/defense ratings, rolling form, rest days, and stage context in a gradient boosting classifier.
- `rating_knn`: distance-weighted neighbors on compact rating and recency features.
- `poisson_rating`: expected-goal model from rating/scoring indicators, converted to 1X2.
- `sequence_deep`: last-10-match sequence tensors with chronological validation and early stopping.
- `elo_form_logit`: interpretable low-variance backup model.

The source project's default market-available blend was:

```text
0.72 * market_m0
+ 0.09 * pi_gbm
+ 0.04 * rating_knn
+ 0.05 * poisson_rating
+ 0.06 * sequence_deep
+ 0.04 * elo_form_logit
```

Use this as a reference, not a universal law. If retraining on a new repository, relearn or revalidate weights chronologically.

## Validation

Primary validation must be chronological. Acceptable schemes:

```text
train <= 2009-12-31 -> test World Cup 2010
train <= 2013-12-31 -> test World Cup 2014
train <= 2017-12-31 -> test World Cup 2018
train <= 2021-12-31 -> test World Cup 2022
```

Report log loss, ranked probability score, Brier score, calibration, CLV where available, ROI only as a secondary betting metric, and max drawdown for stake systems.

Random row splits are only diagnostic after a time-split result already exists.

## Exact-score method

The project's exact-score pipeline:

1. Start with model 1X2 probabilities.
2. Predict prior home and away lambdas from the Poisson component.
3. Fit lambdas so Poisson-implied 1X2 approximates the target 1X2.
4. Calibrate lambdas with conservative football heuristics:
   - raise plausible underdog goal floors;
   - penalize overconfident 1-0 or 0-1 picks;
   - promote both-teams-score rows when supported;
   - promote 2-1 or 1-2 in moderate-favorite games;
   - allow host open-game tail coverage when the host favorite is in a balanced, higher-variance profile.
5. Rank exact scores by `rank_score`, while still reporting raw `probability`.
6. Include `primary_cluster` and `tail_cluster` to avoid overclaiming a single brittle scoreline.

When presenting exact scores, say whether the score distribution is direct model output or derived from 1X2 probabilities.

## Tournament simulation

Use group-stage 90-minute 1X2 probabilities for W/D/L sampling. Sample scorelines from historical same-outcome score distributions to compute points, goal difference, and goals scored.

For FIFA 2026:

- 12 groups.
- Top two in each group qualify.
- 8 best third-place teams qualify.
- Third-place slot allocation follows the official 495-combination table when available.
- Knockout advancement treats draw probability as extra-time/penalty uncertainty and redistributes it across the non-draw strengths.

Monte Carlo title odds are frequency-derived fair odds:

```text
fair_title_odds = 1 / champion_probability
```

Do not derive title odds by multiplying or inverting isolated single-match prices.

## Odds and value

Decimal 1X2 odds contain margin. De-vig before comparing:

```text
raw_implied_i = 1 / odds_i
fair_market_prob_i = raw_implied_i / sum(raw_implied)
edge_pp_i = (model_prob_i - fair_market_prob_i) * 100
EV_i = model_prob_i * odds_i - 1
```

A positive edge is not enough by itself. Prefer recommendations that also pass validation, minimum EV, minimum edge, calibration sanity, and source freshness checks.

## Stake sizing

For decimal odds:

```text
kelly_fraction = (p * odds - 1) / (odds - 1)
```

Clamp negative Kelly to zero. For mutually exclusive exact scores in the same match, do not blindly sum independent full-Kelly fractions. Use fractional Kelly or a constrained allocation.

If the user forces every selection to be bought, label the result as forced allocation, not optimal Kelly. When all selections are negative EV, strict Kelly is zero; any nonzero stake is entertainment or coverage spending.
