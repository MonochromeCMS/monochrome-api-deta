from enum import Enum
from uuid import UUID
from typing import Optional, ClassVar
from pydantic import EmailStr

from .base import DetaBase
from ..fastapi_permissions import Allow


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
            (Allow, ["role:admin"], "create"),
            (Allow, ["role:admin"], "view"),
            (Allow, ["role:admin"], "edit"),
        )

    @property
    def principals(self):
        return [f"user:{self.id}", f"role:{self.role}"]

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
    async def all(cls, limit: int = 20, offset: int = 0):
        return await cls.pagination(None, limit, offset, lambda x: getattr(x, "username"))
