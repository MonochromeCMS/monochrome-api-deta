from typing import Optional, ClassVar, List
from uuid import UUID

from .base import DetaBase


class UploadedBlob(DetaBase):
    name: str
    session_id: UUID
    db_name: ClassVar = "blobs"


class UploadSession(DetaBase):
    owner_id: Optional[UUID]
    chapter_id: Optional[UUID]
    manga_id: UUID
    db_name: ClassVar = "sessions"

    async def delete(self):
        blobs = await self.get_blobs()
        await DetaBase.delete_many(blobs)
        await super().delete()

    async def get_blobs(self):
        return await UploadedBlob.fetch({"session_id": str(self.id)})

    @classmethod
    async def find(cls, *args, **kwargs):
        session = await super().find(*args, **kwargs)
        blobs = await session.get_blobs()
        return session, blobs

    @classmethod
    async def flush(cls):
        sessions = await cls.fetch({})
        return await DetaBase.delete_many(sessions)
