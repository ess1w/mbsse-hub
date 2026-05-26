from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)

    # App
    environment: str = "development"
    frontend_url: str = "http://localhost:5173"
    allowed_origins: str = "http://localhost:5173"

    # DB
    database_url: str

    # JWT
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 7

    # Storage
    storage_backend: str = "local"          # 'local' | 's3'
    local_upload_dir: str = "./uploads"
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    aws_s3_bucket: str = ""
    aws_region: str = "eu-west-1"
    s3_presigned_url_expiry: int = 3600

    # Email (SMTP)
    smtp_host: str = ""          # leave blank to use stdout in dev
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_use_tls: bool = True
    email_from: str = "noreply@mbsse.gov.sl"
    email_from_name: str = "MBSSE Coordination Hub"

    @property
    def async_database_url(self) -> str:
        """Return the DATABASE_URL with the asyncpg dialect prefix.

        Render (and Heroku) provide plain postgresql:// or postgres:// URLs.
        SQLAlchemy's async engine requires postgresql+asyncpg://.
        """
        url = self.database_url
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql://", 1)
        if url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        return url

    @property
    def origins(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",")]


@lru_cache
def get_settings() -> Settings:
    return Settings()
