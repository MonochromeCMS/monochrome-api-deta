from typing import Optional, ClassVar
from uuid import UUID

from .base import DetaBase
from ..fastapi_permissions import Allow


class UploadedBlob(DetaBase):
    name: str
    session_id: UUID
    db_name: ClassVar = "blobs"


class UploadSession(DetaBase):
    owner_id: Optional[UUID]
    chapter_id: Optional[UUID]
    manga_id: UUID
    db_name: ClassVar = "sessions"

    @property
    def __acl__(self):
        return (
            *self.__class_acl__(),
            (Allow, ["role:uploader", f"user:{self.owner_id}"], "view"),
            (Allow, ["role:uploader", f"user:{self.owner_id}"], "edit"),
        )

    @classmethod
    def __class_acl__(cls):
        return (
            (Allow, ["role:admin"], "create"),
            (Allow, ["role:uploader"], "create"),
            (Allow, ["role:admin"], "view"),
            (Allow, ["role:admin"], "edit"),
        )

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
