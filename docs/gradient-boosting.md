# Gradient boosting on CPU

Intuition: a sequence of small trees improves a probability model by addressing the errors left by earlier trees. More trees or deeper trees can also fit noise.

Read `models/boosting.py` and `training/tuning.py`. Inputs are numeric pre-match features `[N,F]`. A training-fitted median imputer preserves unavailable columns and adds missingness indicators. XGBoost uses CPU histogram trees, a three-class probability objective, two LIGHT threads, and regularization.

Outputs are `[N,3]` in HOME/DRAW/AWAY order. Each row is validated and normalized. The fallback HistGradientBoosting implementation can be selected programmatically, but the default training comparison uses XGBoost.

Optuna samples bounded depths, learning rates, tree counts, sampling fractions, minimum child weights, and regularization. Each trial is scored on inner expanding chronological folds within an outer training prefix. FAST has 10 trials, NORMAL 30, DEEP 100, with time limits. Trials run serially to prevent CPU oversubscription.

A parallel candidate excludes head-to-head information. Validation selects whether it helps. Tree gain is global importance; exact tree SHAP values describe the contribution of numeric features to an individual component's logit. Neither establishes causality.

Exercise: compare two tree depths on inner validation only. Explain why inspecting the final test to decide depth would invalidate the evaluation.
