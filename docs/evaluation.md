# Evaluation and research reports

Primary metrics: multiclass log loss and three-class summed Brier score. Secondary diagnostics: accuracy, balanced accuracy, confusion matrix, ECE, mean top probability, home/away goal MAE, and exact-score negative log likelihood.

The newest season with 380 completed games and an end before the current season is the sealed test. At least 760 earlier matches are required. A 380-match warmup precedes six outer validation blocks. OOF predictions are divided approximately 50%/25%/25% by whole dates for meta fitting, calibration, and selection. Insufficient data raises an error rather than manufacturing a score.

Read `evaluation/metrics.py`, `evaluation/reports.py`, and `training/trainer.py`. Reports include measured individual-model and selected-model results, calibration plots, model comparisons, prediction CSVs, fold lineage, and tuning trials. Poor results remain visible.

The default recipe selects lowest selection log loss, with Brier as tie-breaker. This does not demonstrate a statistically certain improvement: validation is finite, many recipes are compared, and season-to-season drift exists. Confidence intervals and repeated temporal development experiments are useful future research; they must not reuse the sealed test for optimization.

MLflow records local experiment metadata, configurations, dependencies, dataset/feature versions, Git commit, validation/test metrics, and model/report artifacts. Content checksums verify trusted local serialized models before loading. Never load untrusted joblib files.

Exercise: compare the selected model to the frequency baseline across both probability metrics. Explain why the answer may differ from the accuracy comparison.
