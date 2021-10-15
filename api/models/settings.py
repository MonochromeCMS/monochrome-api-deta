from typing import Optional, ClassVar

from .base import DetaBase
from ..config import get_settings

global_settings = get_settings()


class Settings(DetaBase):
    id: str = "settings"
    title1: Optional[str]
    title2: Optional[str]
    about: Optional[str]
    db_name: ClassVar = "settings"

    @classmethod
    async def set(cls, **kwargs):
        await cls(**kwargs).save()

    @classmethod
    async def get(cls):
        return await cls.find("settings", None) or cls()
