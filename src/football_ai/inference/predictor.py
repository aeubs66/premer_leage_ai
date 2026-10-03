"""Generate real forecasts and save immutable snapshots before kickoff."""

import uuid
from datetime import UTC, datetime

import numpy as np
from scipy.special import entr

from football_ai.config import Settings
from football_ai.database.repository import Repository
from football_ai.evaluation.reports import disagreement
from football_ai.features.pipeline import FeaturePipeline
from football_ai.training.registry import LocalRegistry


def safe_numeric(value):
    return float(value) if np.isfinite(value) else None


class Predictor:
    def __init__(self, settings: Settings, repository: Repository | None = None):
        self.settings = settings
        self.repository = repository or Repository(settings)

    def predict(self, fixture_id: str):
        now = datetime.now(UTC)
        records = self.repository.matches()
        fixture = next((m for m in records if m.id == fixture_id), None)
        if fixture is None:
            raise KeyError("Unknown fixture")
        if fixture.status != "scheduled" or fixture.kickoff <= now:
            raise ValueError("Only scheduled fixtures before kickoff can be predicted")
        if fixture.date_only:
            raise ValueError("A confirmed kickoff time is required for a saved prediction")
        artifact, manifest = LocalRegistry(self.settings).load()
        if datetime.fromisoformat(manifest["data_cutoff"]) >= now:
            raise ValueError("Model training cutoff is not before this prediction")
        # Features are computed at generation time, not the future kickoff time.
        features = FeaturePipeline(
            artifact.recipe["feature_config"], self.repository.observations()
        ).for_fixture(records, fixture, now)
        probabilities, grids, individual = artifact.predict(features, [fixture])
        p, grid = probabilities[0], grids[0]
        scores = np.arange(len(grid))
        ranking = sorted(
            [(float(grid[h, a]), h, a) for h in range(len(grid)) for a in range(len(grid))],
            reverse=True,
        )
        members = {name: individual[name] for name in artifact.ensemble.names}
        js = float(disagreement(members)[0])
        diagnostics = artifact.diagnostics
        disagreement_level = (
            "insufficient evidence"
            if len(members) < 2
            else ["low", "medium", "high"][
                int(np.searchsorted(diagnostics["disagreement_quantiles"], js))
            ]
        )
        top_probability = float(p.max())
        bins = diagnostics["calibration_bins"]
        historical_bin = next(
            (
                b
                for b in bins
                if b["lower"] <= top_probability < b["upper"]
                or (top_probability == 1 and b["upper"] == 1)
            ),
            None,
        )
        enough = historical_bin is not None and historical_bin["count"] >= 30
        certainty = (
            ["low", "moderate", "high"][
                int(np.searchsorted(diagnostics["probability_quantiles"], top_probability))
            ]
            if enough
            else "insufficient evidence"
        )
        if disagreement_level == "high" and certainty == "high":
            certainty = "moderate"
        labels = [fixture.home_team, "Draw", fixture.away_team]
        row = features.iloc[0]
        factors = self.explain(artifact, features, fixture)
        payload = {
            "prediction_id": uuid.uuid4().hex,
            "fixture_id": fixture.id,
            "match": {
                "home_team": fixture.home_team,
                "away_team": fixture.away_team,
                "kickoff": fixture.kickoff.isoformat(),
            },
            "probabilities": dict(zip(["home", "draw", "away"], map(float, p), strict=True)),
            "predicted_winner": labels[int(p.argmax())],
            "predicted_score": f"{ranking[0][1]}-{ranking[0][2]}",
            "expected_goals": {
                "home": float(np.dot(grid.sum(axis=1), scores)),
                "away": float(np.dot(grid.sum(axis=0), scores)),
            },
            "score_probabilities": [
                {"score": f"{h}-{a}", "probability": probability}
                for probability, h, a in ranking[:10]
            ],
            "score_matrix": grid[:9, :9].tolist(),
            "other_scores_probability": float(max(0, 1 - grid[:9, :9].sum())),
            "score_distribution_method": "Outcome-conditioned Poisson/Dixon-Coles, reconciled to calibrated outcome probabilities",
            "model_predictions": {
                name: dict(zip(["home", "draw", "away"], map(float, values[0]), strict=True))
                for name, values in individual.items()
            },
            "ensemble_members": artifact.ensemble.names,
            "model_disagreement": disagreement_level,
            "uncertainty": {
                "label": certainty,
                "top_probability": top_probability,
                "entropy": float(entr(p).sum()),
                "jensen_shannon_divergence": js,
                "historical_bin": historical_bin,
                "validation_ece": diagnostics["validation_ece"],
                "validation_n": diagnostics["validation_n"],
                "method": "Relative validation probability thirds; at least 30 historical bin samples required; high disagreement caps high confidence. No certainty guarantee.",
            },
            "context": {
                side: {
                    "elo": safe_numeric(row[f"{side}_elo"]),
                    "points_per_game": safe_numeric(row[f"{side}_points_5"]),
                    "goals_for": safe_numeric(row[f"{side}_gf_5"]),
                    "goals_against": safe_numeric(row[f"{side}_ga_5"]),
                    "xg": safe_numeric(row[f"{side}_xg_5"]),
                    "xga": safe_numeric(row[f"{side}_xga_5"]),
                    "rest_days": safe_numeric(row[f"{side}_rest_days"]),
                    "unavailable_players": safe_numeric(row[f"{side}_unavailable_players"]),
                }
                for side in ["home", "away"]
            },
            "explanation": factors,
            "data_coverage": {
                "available_features": int(features.notna().sum(axis=1).iloc[0]),
                "total_features": len(features.columns),
                "player_information": bool(
                    row.home_player_data_available or row.away_player_data_available
                ),
                "xg_available": bool(np.isfinite(row.home_xg_5) and np.isfinite(row.away_xg_5)),
                "historical_availability_assumed": any(m.availability_assumed for m in records),
            },
            "model_version": manifest["version"],
            "dataset_version": manifest["dataset_version"],
            "feature_version": manifest["feature_version"],
            "generated_at": now.isoformat(),
            "features_as_of": now.isoformat(),
            "warning": "Football outcomes are uncertain; historical results do not guarantee future performance.",
        }
        # Recheck time at the write boundary so slow inference cannot save after kickoff.
        if datetime.now(UTC) >= fixture.kickoff:
            raise ValueError("Kickoff occurred during inference; prediction was not saved")
        self.repository.save_prediction(payload, fixture)
        return payload

    @staticmethod
    def explain(artifact, features, fixture):
        model = artifact.models.get("xgboost")
        factors = []
        if model is not None:
            import xgboost as xgb

            numeric = model.imputer.transform(features[model.columns])
            contributions = model.model.get_booster().predict(
                xgb.DMatrix(numeric), pred_contribs=True, strict_shape=True
            )[0]
            predicted_class = int(model.predict_proba(features, [fixture])[0].argmax())
            importance = contributions[predicted_class, :-1]
            names = model.imputer.get_feature_names_out(model.columns)
            order = np.argsort(np.abs(importance))[::-1][:8]
            factors = [
                {
                    "feature": str(names[i]),
                    "value": safe_numeric(numeric[0, i]),
                    "logit_contribution": float(importance[i]),
                    "direction": "supports" if importance[i] > 0 else "opposes",
                }
                for i in order
            ]
        return {
            "title": "Factors associated with this prediction",
            "method": "Exact tree SHAP contributions for the XGBoost component; contributions are to its selected outcome logit, not the final ensemble probability.",
            "component": "xgboost",
            "factors": factors,
            "caution": "Associations are not proven causes.",
        }
