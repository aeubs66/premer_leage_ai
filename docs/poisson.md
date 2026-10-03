# Goals, Poisson, and Dixon–Coles

Intuition: instead of guessing one score, model the likelihood of every plausible score. A goal rate lambda is a distribution parameter, not a guarantee of that number of goals.

Read `models/poisson.py`. `P(G=k) = exp(-lambda)*lambda^k/k!`. Home log-rate combines league intercept, home advantage, home attack, and away defence. Away log-rate combines intercept, away attack, and home defence. Positive defence coefficients mean conceding more goals.

Centered attack coefficients identify the model. SciPy minimizes time-weighted negative log likelihood plus squared-coefficient regularization. The decay scale is 365 days; regularization prevents noisy estimates for sparse teams. Unknown teams receive learned league-average effects.

Under conditional independence, multiply the two goal distributions to form a score matrix. Dixon–Coles adds four corrections at 0–0, 0–1, 1–0, and 1–1. Its rho is fitted on training data and bounded to keep probabilities positive. Validation decides whether the corrected model contributes.

The grid expands until excluded Poisson tail mass is below approximately 1e-12 per margin, then normalizes numerical residue. Home win is the lower triangle, draw the diagonal, and away win the upper triangle. The final outcome ensemble reweights those regions while retaining their conditional score shapes. Expected goals are then the row/column expectations of that reconciled matrix; they need not equal the original Poisson lambdas.

Exercise: sum the diagonal for a 1.5/1.1 goal-rate fixture. Explain why a most-likely score can be a draw while home win remains the most-likely outcome.
