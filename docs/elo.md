# Elo: strength as a changing number

Intuition: beating a strong opponent should change your rating more than beating a weak one. A draw is half a win for the update, not a claim that draws have 50% probability.

Read `features/elo.py` for the update and `models/elo.py` for the outcome model. With home rating R_h, away R_a, and advantage H:

`E_h = 1 / (1 + 10^(-(R_h + H - R_a)/400))`

`delta = K * (actual - E_h)`; add delta to home and subtract it from away. Actual is 1, 0.5, or 0. Optional goal-margin scaling uses log(1 + margin). The default K is 20 and home advantage 65. These are configurable, explicit assumptions.

Between seasons, ratings regress toward 1500: `R_new = 1500 + retention*(R_old - 1500)`, including multiple missing seasons. New clubs start at that prior.

Elo produces an expected result, not three separate football probabilities. A multinomial logistic model learns HOME/DRAW/AWAY from the rating difference and its absolute magnitude using training-only labels. Its input matrix has shape `[matches, 2]`; coefficients map those two inputs into class logits. Softmax converts logits to probabilities summing to one.

Exercise: calculate an equal-rating match with no home advantage. Verify that a win moves ratings to 1510 and 1490, then explain why this conserves the sum.
