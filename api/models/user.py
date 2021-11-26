from enum import Enum
from typing import ClassVar, Optional, Union
from uuid import UUID

from pydantic import BaseModel, EmailStr

from ..fastapi_permissions import Allow, Everyone
from .base import DetaBase


class Role(str, Enum):
    admin = "admin"
    uploader = "uploader"
    user = "user"


class User(DetaBase):
    role: Role = Role.admin
    username: str
    email: Optional[EmailStr]
    hashed_password: str
    db_name: ClassVar = "users"

    @property
    def __acl__(self):
        return (
            *self.__class_acl__(),
            (Allow, [f"user:{self.id}"], "view"),
            (Allow, [f"user:{self.id}"], "edit"),
        )

    @classmethod
    def __class_acl__(cls):
        return (
            (Allow, [Everyone], "register"),
            (Allow, ["role:admin"], "create"),
            (Allow, ["role:admin"], "view"),
            (Allow, ["role:admin"], "edit"),
        )

    @property
    def principals(self):
        return [f"user:{self.id}", f"role:{self.role}"]

    async def delete(self):
        from .comment import Comment

        chapters = await Comment.fetch({"author_id": str(self.id)})

        await DetaBase.delete_many(chapters)
        await super().delete()

    @classmethod
    async def from_username_email(cls, username_email: str, mail: str = "", ignore_user: UUID = None):
        if mail == "":
            query = [{"username": username_email}, {"email": username_email}]
        elif mail is None:
            query = [{"username": username_email}]
        else:
            query = [{"username": username_email}, {"email": mail}]

        if ignore_user:
            query = [{**x, "id,ne": str(ignore_user)} for x in query]

        result = await cls.fetch(query, 3)

        if result:
            return result[0]
        else:
            return None

    @classmethod
    async def search(cls, name: str = "", filters: Union[BaseModel, None] = None, limit: int = 20, offset: int = 0):
        if filters is not None:
            filters = {k: v for k, v in filters.dict().items() if v}
        else:
            filters = {}
        if name:
            filters["username?contains"] = name
        return await cls.pagination(filters, limit, offset, lambda x: getattr(x, "username"))
