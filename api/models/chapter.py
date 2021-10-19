from uuid import UUID
from datetime import datetime
from typing import Optional, ClassVar
from pydantic import Field, PrivateAttr

from .base import DetaBase
from .manga import Manga


class ScanGroup(DetaBase):
    id: str
    db_name: ClassVar = "scan_groups"


class Chapter(DetaBase):
    owner_id: Optional[UUID]
    name: str
    scan_group: str
    volume: Optional[int]
    number: float
    length: int
    webtoon: bool = False
    upload_time: datetime = Field(default_factory=datetime.now)
    manga_id: UUID
    db_name: ClassVar = "chapters"

    async def save(self):
        await ScanGroup(id=self.scan_group).save()
        await super().save()

    @classmethod
    async def find_detailed(cls, *args, **kwargs):
        chapter = await cls.find(*args, **kwargs)
        chapter = chapter.dict()
        chapter["manga"] = await Manga.find(chapter["manga_id"])
        return chapter

    @classmethod
    async def latest(cls, limit: int = 20, offset: int = 0):
        count, results = await cls.pagination({}, limit, offset, lambda x: x.upload_time, True)

        dict_results = [result.dict() for result in results]

        cache = {}
        for result in dict_results:
            if result["manga_id"] not in cache:
                cache[result["manga_id"]] = await Manga.find(result["manga_id"])
            result["manga"] = cache[result["manga_id"]]
        return count, dict_results

    @classmethod
    async def from_manga(cls, manga_id: UUID):
        query = {"manga_id": str(manga_id)}
        results = await cls.fetch(query)
        return sorted(results, key=lambda x: x.number, reverse=True)

    @classmethod
    async def get_groups(cls):
        groups = await ScanGroup.fetch({})
        return [group.id for group in groups]
