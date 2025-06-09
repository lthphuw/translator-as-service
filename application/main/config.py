from pathlib import Path

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppConfig(BaseModel):
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
    SETTINGS_DIR: Path = BASE_DIR / "settings"
    LOGS_DIR: Path = BASE_DIR / "logs"
    MODELS_DIR: Path = BASE_DIR / "models"
    RESOURCES_DIR: Path = BASE_DIR / "resources"
    CACHE_DIR: Path = BASE_DIR / "cache"

    def __init__(self, **data):
        super().__init__(**data)
        self.SETTINGS_DIR.mkdir(parents=True, exist_ok=True)
        self.LOGS_DIR.mkdir(parents=True, exist_ok=True)
        self.MODELS_DIR.mkdir(parents=True, exist_ok=True)
        self.RESOURCES_DIR.mkdir(parents=True, exist_ok=True)
        self.CACHE_DIR.mkdir(parents=True, exist_ok=True)


class GlobalConfig(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="allow")

    APP_CONFIG: AppConfig = AppConfig()

    API_NAME: str = Field(default="Translator Service", validation_alias="API_NAME")
    API_DESCRIPTION: str = Field(
        default="Default description", validation_alias="API_DESCRIPTION"
    )
    API_VERSION: str = Field(default="0.1.0", validation_alias="API_VERSION")
    API_DEBUG_MODE: bool = Field(default=False, validation_alias="API_DEBUG_MODE")

    ENV_STATE: str = Field(default="dev", validation_alias="ENV_STATE")

    HOST: str = Field(default="127.0.0.1", validation_alias="HOST")
    PORT: int = Field(default=8080, validation_alias="PORT")
    LOG_LEVEL: str = Field(default="info", validation_alias="LOG_LEVEL")

    DB: str = Field(default="mongodb", validation_alias="DB")
    CACHE: str = Field(default="redis", validation_alias="CACHE")
    LOG_CONFIG_FILENAME: str = Field(
        default="logging_config.yaml", validation_alias="LOG_CONFIG_FILENAME"
    )


class DevConfig(GlobalConfig):
    model_config = SettingsConfigDict(env_prefix="DEV_", env_file=".env", extra="allow")


class ProdConfig(GlobalConfig):
    model_config = SettingsConfigDict(
        env_prefix="PROD_", env_file=".env", extra="allow"
    )


class FactoryConfig:
    def __init__(self, env_state: str):
        self.env_state = env_state.lower()

    def __call__(self):
        if self.env_state == "dev":
            return DevConfig()
        elif self.env_state == "prod":
            return ProdConfig()
        return GlobalConfig()


settings = FactoryConfig(GlobalConfig().ENV_STATE)()
