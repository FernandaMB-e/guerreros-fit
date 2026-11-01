from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Guerreros Fit API"
    database_url: str = "sqlite:///./guerreros.db"
    secret_key: str = "cambia-esto"
    access_token_expire_minutes: int = 480
    upload_dir: str = "uploads"
    admin_email: str = "admin@guerrerosfit.local"
    admin_password: str = "Cambiar123!"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()