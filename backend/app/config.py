from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "DeskFlow API"
    environment: str = "local"
    database_url: str = "postgresql+psycopg://deskflow:deskflow@localhost:5432/deskflow"
    cors_origins: str = "http://localhost:3000,http://localhost:5173"


settings = Settings()
