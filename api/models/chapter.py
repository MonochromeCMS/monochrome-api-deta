from uuid import UUID
from datetime import datetime
from typing import Optional, ClassVar, Union
from pydantic import Field

from .base import DetaBase
from .manga import Manga
from ..exceptions import NotFoundHTTPException
from ..fastapi_permissions import Allow, Everyone


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
        )

    async def save(self):
        await ScanGroup(id=self.scan_group).save()
        await super().save()

    async def delete(self):
        from .comment import Comment

        chapters = await Comment.fetch({"chapter_id": str(self.id)})

        await DetaBase.delete_many(chapters)
        await super().delete()

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


class DetailedChapter(Chapter):
    manga: Manga

    @classmethod
    async def find(cls, _id: Union[UUID, str], exception=NotFoundHTTPException()):
        chapter = await Chapter.find(_id, exception)
        manga = await Manga.find(chapter.manga_id)
        return cls(**chapter.dict(), manga=manga)
