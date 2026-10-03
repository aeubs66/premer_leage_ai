"""CPU histogram boosting with training-only imputation."""

import numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.impute import SimpleImputer

from football_ai.models.base import normalize


class BoostingModel:
    def __init__(self, parameters=None, threads=2, seed=42, engine="xgboost", exclude_head_to_head=False):
        self.parameters, self.threads, self.seed, self.engine = parameters or {}, threads, seed, engine
        self.exclude_head_to_head = exclude_head_to_head

    def fit(self, features, matches):
        self.columns = [c for c in features.columns if not (self.exclude_head_to_head and c.startswith("head_to_head"))]
        features = features[self.columns]
        self.imputer = SimpleImputer(strategy="median", keep_empty_features=True, add_indicator=True)
        numeric = self.imputer.fit_transform(features)
        if self.engine == "xgboost":
            from xgboost import XGBClassifier
            self.model = XGBClassifier(**self.parameters, device="cpu", tree_method="hist", n_jobs=self.threads,
                                       random_state=self.seed, objective="multi:softprob", num_class=3, eval_metric="mlogloss")
        else:
            self.model = HistGradientBoostingClassifier(max_iter=150, max_leaf_nodes=15, random_state=self.seed, early_stopping=False)
        self.model.fit(numeric, np.array([m.outcome for m in matches]))
        return self

    def predict_proba(self, features, matches):
        numeric = self.imputer.transform(features[self.columns])
        output = np.full((len(features), 3), 1e-12)
        output[:, self.model.classes_] = self.model.predict_proba(numeric)
        return normalize(output)
