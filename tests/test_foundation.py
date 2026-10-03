from football_ai.config import Settings


def test_config():
    settings = Settings()
    assert settings.load("training")["profiles"]["LIGHT"]["threads"] == 2
    assert settings.load("features")["windows"] == [3, 5, 10]


def test_database_path(tmp_path):
    assert (
        Settings(root=tmp_path).db_url()
        == "sqlite:///" + (tmp_path / "data/football.db").as_posix()
    )
