from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "Document Reader AI"
    APP_VERSION: str = "0.1.0"
    DATABASE_URL: str = "sqlite:///./reader_ai.db"
    UPLOAD_DIR: str = "uploads"

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"
    )


settings = Settings()