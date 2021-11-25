from typing import Optional
from uuid import UUID
from os import path
from fastapi import APIRouter, Depends, Query

from .auth import is_connected, auth_responses, Permission, get_active_principals
from ..fastapi_permissions import has_permission, permission_exception
from ..fs import media
from ..exceptions import NotFoundHTTPException
from ..config import get_settings
from ..models.chapter import Chapter, DetailedChapter
from ..models.comment import DetailedComment
from ..schemas.chapter import ChapterSchema, ChapterResponse, LatestChaptersResponse, DetailedChapterResponse
from ..schemas.comment import ChapterCommentsResponse

settings = get_settings()

router = APIRouter(prefix="/chapter", tags=["Chapter"])


async def _get_chapter(chapter_id: UUID):
    return await Chapter.find(chapter_id, NotFoundHTTPException("Chapter not found"))


async def _get_detailed_chapter(chapter_id: UUID):
    return await DetailedChapter.find(chapter_id, NotFoundHTTPException("Chapter not found"))


@router.get("", response_model=LatestChaptersResponse, dependencies=[Permission("view", Chapter.__class_acl__)])
async def get_latest_chapters(
    limit: Optional[int] = Query(10, ge=1, le=settings.max_page_limit),
    offset: Optional[int] = Query(0, ge=0),
):
    count, page = await Chapter.latest(limit, offset)
    return {
        "offset": offset,
        "limit": limit,
        "results": page,
        "total": count,
    }


get_responses = {
    200: {
        "description": "The requested chapter",
        "model": DetailedChapterResponse,
    },
    404: {
        "description": "The chapter couldn't be found",
        **NotFoundHTTPException.open_api("Chapter not found"),
    },
}


@router.get("/{chapter_id}", response_model=DetailedChapterResponse, responses=get_responses)
async def get_chapter(chapter: DetailedChapter = Permission("view", _get_detailed_chapter)):
    return chapter


delete_responses = {
    **auth_responses,
    **get_responses,
    200: {
        "description": "The chapter was deleted",
        "content": {
            "application/json": {
                "example": "OK",
            },
        },
    },
}


@router.delete("/{chapter_id}", dependencies=[Depends(is_connected)], responses=delete_responses)
async def delete_chapter(chapter: Chapter = Permission("edit", _get_chapter)):
    media.rmtree(path.join(str(chapter.manga_id), str(chapter.id)))
    return await chapter.delete()


put_responses = {
    **auth_responses,
    **get_responses,
    200: {
        "description": "The edited chapter",
        "model": ChapterResponse,
    },
}


@router.put(
    "/{chapter_id}", response_model=ChapterResponse, dependencies=[Depends(is_connected)], responses=put_responses
)
async def update_chapter(
    payload: ChapterSchema,
    chapter: Chapter = Permission("edit", _get_chapter),
):
    await chapter.update(**payload.dict())
    return chapter


get_comments_responses = {
    **get_responses,
    200: {
        "description": "The chapter's comments",
        "model": ChapterCommentsResponse,
    },
}


@router.get("/{chapter_id}/comments", response_model=ChapterCommentsResponse, responses=get_comments_responses)
async def get_chapter_comments(
    limit: Optional[int] = Query(10, ge=1, le=settings.max_page_limit),
    offset: Optional[int] = Query(0, ge=0),
    chapter: Chapter = Permission("view", _get_chapter),
    user_principals=Depends(get_active_principals),
):
    if await has_permission(user_principals, "view", Chapter.__class_acl__()):
        count, page = await DetailedComment.from_chapter(chapter.id, limit, offset)
        return {
            "offset": offset,
            "limit": limit,
            "results": page,
            "total": count,
        }
    else:
        raise permission_exception
