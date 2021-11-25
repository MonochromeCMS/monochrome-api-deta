from uuid import UUID
from datetime import datetime
from pydantic import Field
from typing import ClassVar

from .base import DetaBase
from ..fastapi_permissions import Allow, Everyone, Authenticated


class Comment(DetaBase):
    author_id: UUID
    content: str
    chapter_id: UUID
    reply_to: UUID
    create_time: datetime = Field(default_factory=datetime.now)
    db_name: ClassVar = "comment"

    @property
    def __acl__(self):
        return (
            *self.__class_acl__(),
            (Allow, [f"user:{self.author_id}"], "edit"),
        )

    @classmethod
    def __class_acl__(cls):
        return (
            (Allow, [Everyone], "view"),
            (Allow, [Authenticated], "create"),
            (Allow, ["role:uploader"], "edit"),
            (Allow, ["role:admin"], "edit"),
        )

    @classmethod
    async def from_chapter(cls, chapter_id: UUID, limit: int = 20, offset: int = 0):
        query = {"chapter_id": str(chapter_id)}
        return await cls.pagination(query, limit, offset, lambda x: getattr(x, "create_time"))
