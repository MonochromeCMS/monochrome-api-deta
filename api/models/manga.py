from datetime import datetime
from enum import Enum
from uuid import UUID
from typing import Optional, ClassVar

from .base import DetaBase, Field
from ..fastapi_permissions import Allow, Everyone


class Status(str, Enum):
    ongoing = "ongoing"
    completed = "completed"
    hiatus = "hiatus"
    cancelled = "cancelled"


class Manga(DetaBase):
    owner_id: Optional[UUID]
    title: str
    description: str
    author: str
    artist: str
    create_time: datetime = Field(default_factory=datetime.now)
    year: Optional[int] = Field(ge=1900, le=2100)
    status: Status
    db_name: ClassVar = "manga"

    @property
    def __acl__(self):
        return (
            *self.__class_acl__(),
            (Allow, ["role:uploader", f"user:{self.owner_id}"], "edit"),
        )

    @classmethod
    def __class_acl__(cls):
        return (
            (Allow, [Everyone], "view"),
            (Allow, ["role:admin"], "edit"),
            (Allow, ["role:admin"], "create"),
            (Allow, ["role:uploader"], "create"),
        )

    async def delete(self):
        from .chapter import Chapter

        chapters = await Chapter.fetch({"manga_id": str(self.id)})

        await DetaBase.delete_many(chapters)
        await super().delete()

    @classmethod
    async def search(cls, title: str, limit: int = 20, offset: int = 0):
        if title:
            query = {"title?contains": title}
        else:
            query = {}
        return await cls.pagination(query, limit, offset, lambda x: getattr(x, "create_time"))
