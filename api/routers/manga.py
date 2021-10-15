import os
import shutil

from PIL import Image

from uuid import UUID
from typing import Optional, List
from fastapi import APIRouter, Depends, status, Query, File, UploadFile, BackgroundTasks

from .auth import is_connected, auth_responses
from ..exceptions import BadRequestHTTPException, NotFoundHTTPException
from ..config import get_settings
from ..models.chapter import Chapter
from ..models.manga import Manga
from ..schemas.chapter import ChapterResponse
from ..schemas.manga import MangaSchema, MangaResponse, MangaSearchResponse


settings = get_settings()

router = APIRouter(prefix="/manga", tags=["Manga"])


post_responses = {
    **auth_responses,
    201: {
        "description": "The created manga",
        "model": MangaResponse,
    },
}


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=MangaResponse,
    dependencies=[Depends(is_connected)],
    responses=post_responses,
)
async def create_manga(payload: MangaSchema):
    manga = Manga(**payload.dict())
    await manga.save()
    os.mkdir(os.path.join(settings.media_path, str(manga.id)))
    return manga


@router.get("", response_model=MangaSearchResponse)
async def search_manga(
    title: str = "",
    limit: Optional[int] = Query(10, ge=1, le=settings.max_page_limit),
    offset: Optional[int] = Query(0, ge=0),
):
    count, page = await Manga.search(title, limit, offset)
    return {
        "offset": offset,
        "limit": limit,
        "results": page,
        "total": count,
    }


get_responses = {
    404: {
        "description": "The manga couldn't be found",
        **NotFoundHTTPException.open_api("Manga not found"),
    },
    200: {
        "description": "The requested manga",
        "model": MangaResponse,
    },
}


@router.get("/{id}", response_model=MangaResponse, responses=get_responses)
async def get_manga(id: UUID):
    return await Manga.find(id, NotFoundHTTPException("Manga not found"))


get_chapters_responses = {
    **get_responses,
    200: {
        "description": "The requested chapters",
        "model": List[ChapterResponse],
    },
}


@router.get("/{id}/chapters", response_model=List[ChapterResponse], responses=get_chapters_responses)
async def get_manga_chapters(id: UUID):
    await Manga.find(id, NotFoundHTTPException("Manga not found"))
    return await Chapter.from_manga(id)


delete_responses = {
    **auth_responses,
    **get_responses,
    200: {
        "description": "The manga was deleted",
        "content": {
            "application/json": {
                "example": "OK",
            },
        },
    },
}


@router.delete("/{id}", dependencies=[Depends(is_connected)], responses=delete_responses)
async def delete_manga(id: UUID):
    manga = await Manga.find(id, NotFoundHTTPException("Manga not found"))
    shutil.rmtree(os.path.join(settings.media_path, str(manga.id)))
    return await manga.delete()


put_responses = {
    **auth_responses,
    **get_responses,
    200: {
        "description": "The edited manga",
        "model": MangaResponse,
    },
}


@router.put("/{id}", response_model=MangaResponse, dependencies=[Depends(is_connected)], responses=put_responses)
async def update_manga(payload: MangaSchema, id: UUID):
    manga = await Manga.find(id, NotFoundHTTPException("Manga not found"))
    await manga.update(**payload.dict())
    return manga


def save_cover(manga_id: UUID, file: File):
    im = Image.open(file)
    im.convert("RGB").save(os.path.join(settings.media_path, str(manga_id), "cover.jpg"))


put_cover_responses = {
    **auth_responses,
    **get_responses,
    400: {
        "description": "The cover isn't a valid image",
        **BadRequestHTTPException.open_api("image_name is not an image"),
    },
    200: {
        "description": "The edited manga",
        "model": MangaResponse,
    },
}


@router.put("/{id}/cover", dependencies=[Depends(is_connected)], responses=put_cover_responses)
async def set_manga_cover(id: UUID, tasks: BackgroundTasks, payload: UploadFile = File(...)):
    if not payload.content_type.startswith("image/"):
        raise BadRequestHTTPException(f"'{payload.filename}' is not an image")

    manga = await Manga.find(id, NotFoundHTTPException("Manga not found"))
    tasks.add_task(save_cover, manga.id, payload.file)
    return manga
