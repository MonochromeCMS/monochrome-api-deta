import logging
from functools import lru_cache

from pydantic import BaseSettings, Field

log = logging.getLogger(__name__)


class Settings(BaseSettings):
    deta_project_key: str
    cors_origins: str = ""

    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 60

    temp_path: str = "/tmp"

    max_page_limit: int = Field(50, gt=0)


@lru_cache()
def get_settings():
    log.info("Loading config settings from the environment...")
    return Settings()
