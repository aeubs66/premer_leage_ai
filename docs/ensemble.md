# Ensembles without training on leaked predictions

Intuition: different models describe different aspects of football. Combining them can help only if the combination is evaluated on future matches it has not seen.

Read `models/ensemble.py` and `training/trainer.py`. Each outer expanding fold fits its own base models, with hyperparameters chosen on inner folds. It predicts the next period. Concatenating these predictions forms an out-of-fold matrix; no row is predicted by a base learner fitted on that row's outcome.

Chronological OOF rows are separated into meta fitting, calibration fitting, and selection. Weighted blending learns nonnegative weights summing to one. Logistic stacking learns class logits from log base probabilities. A tiny regularized eight-unit MLP is another meta-model candidate. Single models remain candidates; the system need not deploy an ensemble.

The fitting stage learns combination parameters. The calibration stage learns probability transforms. The selection stage compares complete recipes. The final complete season remains sealed. Neural inclusion and H2H exclusion are determined through validation, not marketing language.

Research artifacts are fitted on pre-test data. After evaluation, production base models refit the frozen recipe on available completed matches. Meta/calibration parameters remain those learned from independent OOF predictions. This refit can create distribution shift; prospective evaluation measures the deployed behavior.

Exercise: explain why fitting a stacker on base-model training predictions gives it an unrealistically optimistic view.
