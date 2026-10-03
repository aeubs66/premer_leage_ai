# Calibrated probabilities

Intuition: among many outcomes assigned 60% probability, roughly 60% should occur. Winner accuracy alone cannot check that.

Read `models/calibration.py` and `evaluation/metrics.py`. Sigmoid calibration learns a logistic transformation for each outcome. Isotonic learns a monotone transformation without a fixed functional shape. Temperature scaling divides log probabilities by a learned positive temperature before softmax. A no-calibration candidate is essential.

Calibration fits a separate chronological block of out-of-fold probabilities and labels. Candidate transforms are compared on a later selection block. Final-test behavior is reported, never used to choose a transform. Independently calibrated classes are normalized afterward, so per-class transformations need not preserve exact marginal calibration.

Brier score here is the mean sum of squared errors across all three classes, with range 0–2. Log loss penalizes probability assigned to the realized class. Reliability plots use the largest assigned outcome probability against correctness, with ten bins. ECE is the sample-weighted absolute gap in those bins; it is a diagnostic dependent on binning, not a universal guarantee.

Uncertainty labels use validation probability thirds, historical bin sample counts, and Jensen–Shannon disagreement. Labels require at least 30 samples in the corresponding probability bin; otherwise evidence is insufficient. High disagreement caps a high label at moderate. The raw quantities and method accompany every prediction.

Exercise: show why predictions of 0.99 assigned to frequently incorrect outcomes can have reasonable accuracy but terrible log loss.
