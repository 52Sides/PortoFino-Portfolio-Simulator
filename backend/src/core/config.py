from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Global app configuration (loads from .env and .env_secret if available)"""

    # === Security ===
    SECRET_KEY: str = "change-me"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # === Database ===
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@postgres:5432/portofino_db"

    # === Redis / Celery ===
    REDIS_URL: str = "redis://redis:6379/0"
    CELERY_BROKER_URL: str = "redis://redis:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://redis:6379/0"

    # === Kafka ===
    KAFKA_BROKER: str = "kafka:9092"
    KAFKA_SIMULATION_TOPIC: str = "simulation-events"
    KAFKA_HISTORY_TOPIC: str = "history-events"
    KAFKA_REPORT_TOPIC: str = "report-events"

    # === WebSocket / Redis pub-sub ===
    REDIS_PUBSUB_CHANNEL: str = "sim_progress"

    # === App ===
    APP_ENV: str = "dev"
    APP_PORT: int = 8000
    API_BASE_URL: str = "http://localhost:8000"
    FRONTEND_URL: str = "http://localhost:5173"

    # === OAuth ===
    GOOGLE_CLIENT_ID: str | None = None
    GOOGLE_CLIENT_SECRET: str | None = None
    SESSION_SECRET: str | None = None

    model_config = SettingsConfigDict(
        env_file=(".env", ".env_secret"),
        env_prefix="",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()
