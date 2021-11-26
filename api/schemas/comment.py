from typing import Optional
from uuid import UUID
from datetime import datetime
from fastapi_camelcase import CamelModel
from pydantic import Field
from .base import PaginationResponse
from .user import UserResponse


class CommentEditSchema(CamelModel):
    content: str = Field(description="Content of the comment")

    class Config:
        schema_extra = {
            "example": {
                "content": "I can't believe this cliffhanger!",
            }
        }


class CommentSchema(CommentEditSchema):
    chapter_id: UUID = Field(description="Chapter this comment is created for")
    reply_to: Optional[UUID] = Field(description="A comment this is a reply to")

    class Config:
        schema_extra = {
            "example": {
                "content": "I can't believe this cliffhanger!",
                "chapterId": "4abe53f4-0eaa-4f31-9210-a625fa665e23",
                "replyTo": "4f31d7f6-c4e1-4200-9dd0-a6fccc065978",
            }
        }


class CommentResponse(CommentSchema):
    id: UUID = Field(
        title="ID",
        description="ID of the comment",
    )
    version: int = Field(
        description="Version of the comment",
    )
    create_time: datetime = Field(
        description="Time this comment was created",
    )
    author_id: Optional[UUID] = Field(description="User that posted this comment")

    class Config:
        orm_mode = True
        schema_extra = {
            "example": {
                "content": "I can't believe this cliffhanger!",
                "chapterId": "4abe53f4-0eaa-4f31-9210-a625fa665e23",
                "replyTo": "4f31d7f6-c4e1-4200-9dd0-a6fccc065978",
                "version": 2,
                "id": "4abe53f4-0eaa-4f31-9210-a625fa665e23",
                "createTime": "2000-08-24 00:00:00",
                "authorId": "6901d7f6-c4e1-4200-9dd0-a6fccc065978",
            }
        }


class DetailedCommentResponse(CommentResponse):
    author: UserResponse


class ChapterCommentsResponse(PaginationResponse):
    results: list[DetailedCommentResponse]
