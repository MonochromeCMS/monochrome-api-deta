from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Query

from .auth import is_connected, auth_responses
from ..fs import media, path
from ..exceptions import NotFoundHTTPException
from ..config import get_settings
from ..models.chapter import Chapter
from ..schemas.chapter import ChapterSchema, ChapterResponse, LatestChaptersResponse, DetailedChapterResponse


settings = get_settings()

router = APIRouter(prefix="/chapter", tags=["Chapter"])


@router.get("", response_model=LatestChaptersResponse)
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


@router.get("/{id}", response_model=DetailedChapterResponse, responses=get_responses)
async def get_chapter(id: UUID):
    return await Chapter.find_detailed(id, NotFoundHTTPException("Chapter not found"))


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


@router.delete("/{id}", dependencies=[Depends(is_connected)], responses=delete_responses)
async def delete_chapter(id: UUID):
    chapter = await Chapter.find(id, NotFoundHTTPException("Chapter not found"))
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


@router.put("/{id}", response_model=ChapterResponse, dependencies=[Depends(is_connected)], responses=put_responses)
async def update_chapter(
    payload: ChapterSchema,
    id: UUID,
):
    chapter = await Chapter.find(id, NotFoundHTTPException("Chapter not found"))
    await chapter.update(**payload.dict())
    return chapter
