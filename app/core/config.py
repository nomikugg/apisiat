from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    database_url: str = "postgresql+psycopg://apisiat:apisiat@localhost:5432/apisiat"
    redis_url: str = "redis://localhost:6379/0"
    siat_env: str = "sandbox"


settings = Settings()
