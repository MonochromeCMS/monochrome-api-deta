from typing import ClassVar, Optional

from ..config import get_settings
from ..fastapi_permissions import Allow, Everyone
from .base import DetaBase

global_settings = get_settings()


class Settings(DetaBase):
    id: str = "settings"
    title1: Optional[str]
    title2: Optional[str]
    about: Optional[str]
    db_name: ClassVar = "settings"

    __acl__ = (
        (Allow, [Everyone], "view"),
        (Allow, ["role:admin"], "edit"),
    )

    @classmethod
    async def set(cls, **kwargs):
        await cls(**kwargs).save()

    @classmethod
    async def get(cls):
        return await cls.find("settings", None) or cls()
