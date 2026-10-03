# Optional research and market benchmarks

`experiments/framework.py` defines a hypothesis-bearing experiment with minimum data and a declared CPU budget. Execution records elapsed time and budget overruns; the budget is diagnostic, not a hard process kill. Experiment results are never automatically promoted. `monte_carlo_scores` provides a seeded CPU check of sampled score frequencies against the exact distribution. Sampling is useful for more complex hypotheses but should not replace an available exact calculation merely to look sophisticated.

Bayesian models, attention, temporal networks, and graph/player embeddings are deliberately not production implementations. Add one only with enough data, a specific hypothesis, CPU feasibility evidence, and the same chronological evaluation contract.

`benchmarks/odds.py` converts decimal home/draw/away odds into inverse probabilities and removes margin proportionally. It returns the margin and normalized probabilities for an optional independent benchmark. Odds do not enter the provider's statistical feature whitelist or any training model. More advanced margin-removal methods may be compared independently. No bet sizing, bankroll management, or automatic betting is implemented.

Exercise: verify that three decimal odds convert to probabilities summing to one, then explain what the overround represents without treating it as a prediction feature.
