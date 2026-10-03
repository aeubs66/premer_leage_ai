import numpy as np
import pandas as pd
import pytest

from football_ai.config import Settings
from football_ai.features.elo import Elo
from football_ai.features.pipeline import FeaturePipeline
from test_data import match


def pipeline():
    return FeaturePipeline(Settings().load("features"))


def test_current_and_future_mutations_do_not_change_past_features():
    records = [match(i, hg=i % 3) for i in range(8)]
    expected = pipeline().transform(records)
    changed = [r.model_copy(update={"home_goals": 12, "home_stats": {"xg": 50}}) if i >= 3 else r for i, r in enumerate(records)]
    actual = pipeline().transform(changed)
    pd.testing.assert_frame_equal(expected.iloc[:4], actual.iloc[:4])


def test_simultaneous_and_unavailable_results():
    first, second = match(0), match(1)
    second = second.model_copy(update={"kickoff": first.kickoff, "available_at": first.available_at})
    features = pipeline().transform([first, second])
    assert (features.home_history_count == 0).all()
    assert features.home_gf_3.isna().all()
    near = second.model_copy(update={"kickoff": first.available_at})
    assert pipeline().for_fixture([first], near).home_history_count.iloc[0] == 0


def test_form_and_inference_share_engine():
    records = [match(i, hg=i % 3) for i in range(5)]
    features = pipeline().transform(records)
    assert features.loc["4", "home_history_count"] == 4
    assert features.loc["4", "home_gf_3"] == pytest.approx(1)
    pd.testing.assert_series_equal(features.loc["4"], pipeline().for_fixture(records[:4], records[4]).iloc[0], check_names=False)


def test_elo_update_conserves_rating_and_season_shrinkage():
    elo = Elo(home_advantage=0)
    elo.update("A", "B", "2020/2021", 1, 0)
    assert elo.ratings == {"A": 1510, "B": 1490}
    assert elo.rating("A", "2021/2022") == 1507.5
    assert elo.expected("A", "B", "2020/2021") > 0.5


def test_empty_history_is_missing_not_invented():
    features = pipeline().transform([match()])
    assert np.isnan(features.home_xg_5.iloc[0])
    assert features.home_player_data_available.iloc[0] == 0
