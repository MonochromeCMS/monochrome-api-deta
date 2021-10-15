from datetime import datetime
from enum import Enum
from typing import Optional, ClassVar

from .base import DetaBase, Field


class Status(str, Enum):
    ongoing = "ongoing"
    completed = "completed"
    hiatus = "hiatus"
    cancelled = "cancelled"


class Manga(DetaBase):
    title: str
    description: str
    author: str
    artist: str
    create_time: datetime = Field(default_factory=datetime.now)
    year: Optional[int] = Field(ge=1900, le=2100)
    status: Status
    db_name: ClassVar = "manga"

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
