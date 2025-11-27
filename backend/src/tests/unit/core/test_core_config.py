import importlib
import pytest


@pytest.mark.unit
def test_settings_loads_with_defaults(monkeypatch):
    env_vars = {
        "DATABASE_URL": "postgresql+asyncpg://postgres:postgres@localhost:5432/test_db",
        "REDIS_URL": "redis://localhost:6379/0",
        "KAFKA_BROKER": "kafka:9092",
        "APP_ENV": "test",
        "APP_PORT": "9000",
    }

    for key, value in env_vars.items():
        monkeypatch.setenv(key, value)

    import core.config as config
    importlib.reload(config)

    settings = config.Settings()

    assert settings.DATABASE_URL == env_vars["DATABASE_URL"]
    assert settings.REDIS_URL == env_vars["REDIS_URL"]
    assert settings.KAFKA_BROKER == env_vars["KAFKA_BROKER"]
    assert settings.APP_ENV == "test"
    assert settings.APP_PORT == 9000
