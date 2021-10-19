from uuid import UUID
from typing import Optional, List

from fastapi_camelcase import CamelModel
from pydantic import Field, EmailStr, BaseModel

from .base import PaginationResponse
from ..models.user import Role


class TokenResponse(BaseModel):
    access_token: str = Field(description="JWT Auth token")
    token_type = Field(
        "bearer",
        const=True,
    )


class User(CamelModel):
    username: str = Field(max_length=15)
    email: Optional[EmailStr]


class UserSchema(User):
    password: str
    role: Role


class UserResponse(User):
    id: UUID = Field(title="ID", description="ID of the user")
    version: int = Field(description="Version of the user")
    role: Role = Field(description="Role of the user")

    class Config:
        orm_mode = True
        schema_extra = {
            "example": {
                "id": "6901d7f6-c4e1-4200-9dd0-a6fccc065978",
                "username": "user",
                "email": "user@example.com",
                "version": 2,
                "role": "admin",
            }
        }


class UsersResponse(PaginationResponse):
    results: List[UserResponse]
