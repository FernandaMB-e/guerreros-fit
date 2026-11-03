from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Guerreros Fit API"
    database_url: str = "sqlite:///./guerreros.db"
    secret_key: str = "cambia-esto"
    access_token_expire_minutes: int = 480
    upload_dir: str = "uploads"
    admin_email: str = "admin@guerrerosfit.local"
    admin_password: str = "Cambiar123!"
    cookie_secure: bool = False  # poner True cuando haya HTTPS
    whatsapp_verify_token: str = "123456789"   # lo inventas tú; Meta lo manda al verificar el webhook
    whatsapp_app_secret: str = ""     # clave secreta de la app; firma los mensajes que llegan
    whatsapp_access_token: str = ""
    whatsapp_phone_number_id: str = ""
    whatsapp_api_version: str = "v23.0"
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()