# Feature engineering

WHAT: summarize a team's history as numeric evidence. WHY: models cannot infer recent form from an unordered team name alone. INPUT: canonical eligible historical matches. OUTPUT: one named numeric row per fixture. FIT: the same engine feeds training, backtests, and live forecasts.

Read `features/pipeline.py`. Each side has 3/5/10-match means for points, outcomes, goals, clean sheets, and available statistics. Home/away venue form uses the five prior games at that venue. Exponentially weighted form follows `s_t = alpha*x_t + (1-alpha)*s_(t-1)` with alpha 0.25, placing more weight on recent evidence.

Elo is read before the update. Season points, goal difference, games played, and positions are reconstructed from eligible outcomes. Equal points/GD/goals share positions. These are sporting tables without administrative sanctions or advanced league tie rules.

Attack and defence rates shrink a sparse ten-match sample toward the eligible league scoring mean, using five pseudo-games. The initial scoring prior is 1.3 goals per team and has a numerical floor of 0.1. These are declared modeling priors, not invented observations.

Rest days and 7/14-day congestion use previous fixtures; optional timestamped cup observations extend schedule context. xG, possession, and player features stay NaN when unavailable. Model preprocessing learns medians and missingness indicators from its training prefix only.

Feature caches depend on dataset hash, full feature configuration, and observation payloads. Changing an enrichment source invalidates the cache. Head-to-head is tested through a no-H2H boosting candidate rather than assumed useful.
