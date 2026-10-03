from football_ai.config import Settings


def test_config():
    settings = Settings()
    assert settings.load("training")["profiles"]["LIGHT"]["threads"] == 2
    assert settings.load("features")["windows"] == [3, 5, 10]


def test_api_token_can_be_read_without_disclosing_it(tmp_path):
    path = tmp_path / ".env"
    path.write_text("FOOTBALL_DATA_TOKEN=synthetic-token-for-test\n", encoding="utf-8")
    settings = Settings(_env_file=path)
    assert settings.football_data_token is not None
    assert settings.football_data_token.get_secret_value() == "synthetic-token-for-test"
    assert "synthetic-token-for-test" not in repr(settings)


def test_database_path(tmp_path):
    assert (
        Settings(root=tmp_path).db_url()
        == "sqlite:///" + (tmp_path / "data/football.db").as_posix()
    )
