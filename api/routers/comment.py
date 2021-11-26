from uuid import UUID
from fastapi import APIRouter, Depends, status
from .auth import auth_responses, Permission, get_connected_user
from ..exceptions import NotFoundHTTPException, BadRequestHTTPException
from ..models.user import User
from ..models.comment import Comment
from ..schemas.comment import CommentSchema, CommentEditSchema, CommentResponse


router = APIRouter(prefix="/comment", tags=["Comment"])


async def _get_comment(comment_id: UUID):
    return await Comment.find(comment_id, NotFoundHTTPException("Comment not found"))


post_responses = {
    **auth_responses,
    400: {
        "description": "The replied comment is not valid",
        **BadRequestHTTPException.open_api("Comment to reply to not valid"),
    },
    201: {
        "description": "The created comment",
        "model": CommentResponse,
    },
}


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=CommentResponse,
    responses=post_responses,
)
async def create_comment(
    payload: CommentSchema,
    user: User = Depends(get_connected_user),
    _: Comment = Permission("create", Comment.__class_acl__),
):
    if payload.reply_to:
        reply_comment = await Comment.find(payload.reply_to, None)
        if not reply_comment or reply_comment.chapter_id != payload.chapter_id:
            raise BadRequestHTTPException("Comment to reply to not valid")
    comment = Comment(**payload.dict(), author_id=user.id)
    await comment.save()
    return comment


get_responses = {
    200: {
        "description": "The requested comment",
        "model": CommentResponse,
    },
    404: {
        "description": "The chapter couldn't be found",
        **NotFoundHTTPException.open_api("Chapter not found"),
    },
}


@router.get("/{comment_id}", response_model=CommentResponse, responses=get_responses)
async def get_comment(comment: Comment = Permission("view", _get_comment)):
    return comment


delete_responses = {
    **auth_responses,
    **get_responses,
    200: {
        "description": "The comment was deleted",
        "content": {
            "application/json": {
                "example": "OK",
            },
        },
    },
}


@router.delete("/{comment_id}", responses=delete_responses)
async def delete_comment(comment: Comment = Permission("edit", _get_comment)):
    return await comment.delete()


put_responses = {
    **auth_responses,
    **get_responses,
    200: {
        "description": "The edited comment",
        "model": CommentResponse,
    },
}


@router.put("/{comment_id}", response_model=CommentResponse, responses=put_responses)
async def update_comment(
    payload: CommentEditSchema,
    comment: Comment = Permission("edit", _get_comment),
):
    await comment.update(**payload.dict())
    return comment
