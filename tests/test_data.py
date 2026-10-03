from datetime import UTC, datetime, timedelta

import pytest

from football_ai.config import Settings
from football_ai.data.providers import CSVDataProvider
from football_ai.data.schemas import Match, match_key
from football_ai.data.store import load_snapshot, save_snapshot, validate_records


def match(i=0, home="A", away="B", hg=1, ag=0):
    kickoff = datetime(2020, 8, 1, 15, tzinfo=UTC) + timedelta(days=i * 7)
    return Match(id=str(i), season="2020/2021", home_team=home, away_team=away,
                 kickoff=kickoff, status="finished", home_goals=hg, away_goals=ag,
                 available_at=kickoff + timedelta(hours=3), source="test")


def test_csv_date_only_and_odds(tmp_path):
    path = tmp_path / "matches.csv"
    path.write_text("Date,HomeTeam,AwayTeam,FTHG,FTAG,HS,B365H\n01/08/2020,Man City,Arsenal,2,1,10,1.5\n")
    record = CSVDataProvider(path, "2020/2021").results()[0]
    assert record.home_team == "Manchester City"
    assert record.available_at - record.kickoff == timedelta(days=1)
    assert record.home_stats["xg"] is None
    assert "B365H" not in record.home_stats


def test_validation_and_versioning(tmp_path):
    settings = Settings(root=tmp_path)
    first = match()
    digest = save_snapshot(settings, [first, first])
    assert load_snapshot(settings)[0] == [first]
    assert save_snapshot(settings, [first]) == digest
    with pytest.raises(ValueError, match="Conflicting"):
        validate_records([first, first.model_copy(update={"home_goals": 3})])


def test_invalid_goal_and_identity():
    with pytest.raises(ValueError):
        match(hg=-1)
    assert match_key("2020/2021", "A", "B") == match_key("2020/2021", "A", "B")
    assert match_key("2021/2022", "A", "B") != match_key("2020/2021", "A", "B")
