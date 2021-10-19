from PIL import Image

from uuid import UUID
from os import path
from tempfile import TemporaryFile
from typing import Optional, List
from fastapi import APIRouter, Depends, status, Query, File, UploadFile, BackgroundTasks

from .auth import get_connected_user, auth_responses, Permission, get_active_principals
from ..fastapi_permissions import has_permission, permission_exception
from ..fs import media
from ..exceptions import BadRequestHTTPException, NotFoundHTTPException
from ..config import get_settings
from ..models.user import User
from ..models.chapter import Chapter
from ..models.manga import Manga
from ..schemas.chapter import ChapterResponse
from ..schemas.manga import MangaSchema, MangaResponse, MangaSearchResponse


settings = get_settings()

router = APIRouter(prefix="/manga", tags=["Manga"])


async def _get_manga(manga_id: UUID):
    return await Manga.find(manga_id, NotFoundHTTPException("Manga not found"))


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
    dependencies=[Permission("create", Manga.__class_acl__)],
    responses=post_responses,
)
async def create_manga(payload: MangaSchema, user: User = Depends(get_connected_user)):
    manga = Manga(**payload.dict(), owner_id=user.id)
    await manga.save()
    return manga


@router.get("", response_model=MangaSearchResponse, dependencies=[Permission("view", Manga.__class_acl__)])
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


@router.get("/{manga_id}", response_model=MangaResponse, responses=get_responses)
async def get_manga(manga: Manga = Permission("view", _get_manga)):
    return manga


get_chapters_responses = {
    **get_responses,
    200: {
        "description": "The requested chapters",
        "model": List[ChapterResponse],
    },
}


@router.get("/{manga_id}/chapters", response_model=List[ChapterResponse], responses=get_chapters_responses)
async def get_manga_chapters(
    manga: Manga = Permission("view", _get_manga), user_principals=Depends(get_active_principals)
):
    if await has_permission(user_principals, "view", Chapter.__class_acl__()):
        return await Chapter.from_manga(manga.id)
    else:
        raise permission_exception


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


@router.delete("/{manga_id}", responses=delete_responses)
async def delete_manga(manga: Manga = Permission("edit", _get_manga)):
    media.rmtree(str(manga.id))
    return await manga.delete()


put_responses = {
    **auth_responses,
    **get_responses,
    200: {
        "description": "The edited manga",
        "model": MangaResponse,
    },
}


@router.put("/{manga_id}", response_model=MangaResponse, responses=put_responses)
async def update_manga(payload: MangaSchema, manga: Manga = Permission("edit", _get_manga)):
    await manga.update(**payload.dict())
    return manga


def save_cover(manga_id: UUID, file: File):
    im = Image.open(file)
    with TemporaryFile() as f:
        im.convert("RGB").save(f, "JPEG")
        f.seek(0)
        media.put(path.join(str(manga_id), "cover.jpg"), f)


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


@router.put("/{manga_id}/cover", responses=put_cover_responses)
async def set_manga_cover(
    tasks: BackgroundTasks, payload: UploadFile = File(...), manga: Manga = Permission("edit", _get_manga)
):
    if not payload.content_type.startswith("image/"):
        raise BadRequestHTTPException(f"'{payload.filename}' is not an image")

    tasks.add_task(save_cover, manga.id, payload.file)
    return manga
