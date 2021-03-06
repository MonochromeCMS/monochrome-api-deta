from typing import ClassVar, Optional, Union
from uuid import UUID

from ..exceptions import NotFoundHTTPException
from ..fastapi_permissions import Allow
from .base import DetaBase


class UploadedBlob(DetaBase):
    name: str
    session_id: UUID
    db_name: ClassVar = "blobs"

    @classmethod
    async def from_session(cls, session_id: UUID):
        return await UploadedBlob.fetch({"session_id": str(session_id)})


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
        blobs = await UploadedBlob.fetch({"session_id": str(self.id)})
        await DetaBase.delete_many(blobs)
        await super().delete()

    @classmethod
    async def flush(cls):
        sessions = await cls.fetch({})
        return await DetaBase.delete_many(sessions)


class UploadSessionBlobs(UploadSession):
    blobs: list[UploadedBlob]

    @classmethod
    async def find(cls, _id: Union[UUID, str], exception=NotFoundHTTPException()):
        session = await UploadSession.find(_id, exception)
        blobs = await UploadedBlob.fetch({"session_id": str(_id)})
        return cls(**session.dict(), blobs=blobs)
