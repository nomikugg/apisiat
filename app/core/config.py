from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    database_url: str = "postgresql+psycopg://apisiat:apisiat@localhost:5432/apisiat"
    redis_url: str = "redis://localhost:6379/0"
    siat_env: str = "sandbox"

    # TODO: completar con las URLs reales del WSDL de piloto/producción del SIN (ver docs/04-adapter-siat.md)
    siat_wsdl_autenticacion: str = ""
    siat_wsdl_facturacion: str = ""
    siat_wsdl_codigos: str = ""


settings = Settings()
