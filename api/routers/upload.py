from typing import List, Tuple, Iterable
from shutil import rmtree
from os import path, makedirs, remove, listdir
from tempfile import TemporaryFile
from aiofiles import open
from pyunpack import Archive
from PIL import Image

from uuid import UUID
from fastapi import APIRouter, Depends, File, UploadFile, status, BackgroundTasks
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder

from .auth import is_connected, auth_responses, Permission, get_active_principals
from ..fastapi_permissions import has_permission, permission_exception
from ..fs import media
from ..exceptions import BadRequestHTTPException, NotFoundHTTPException
from ..config import get_settings
from ..models.user import User
from ..models.manga import Manga
from ..models.chapter import Chapter
from ..models.upload import UploadSession, UploadedBlob, UploadSessionBlobs
from ..schemas.chapter import ChapterResponse
from ..schemas.upload import UploadSessionSchema, CommitUploadSession, UploadSessionResponse, UploadedBlobResponse

global_settings = get_settings()

router = APIRouter(prefix="/upload", tags=["Upload"])


async def _get_upload_session(session_id: UUID):
    return await UploadSession.find(session_id, NotFoundHTTPException("Session not found"))


async def _get_upload_session_blobs(session_id: UUID):
    return await UploadSessionBlobs.find(session_id, NotFoundHTTPException("Session not found"))


def copy_chapter_to_session(chapter: Chapter, blobs: List[UUID]):
    chapter_path = path.join(str(chapter.manga_id), str(chapter.id))
    for i in range(chapter.length):
        media.copy(path.join(chapter_path, f"{i + 1}.jpg"), path.join("blobs", f"{blobs[i]}.jpg"))


post_responses = {
    **auth_responses,
    404: {
        "description": "The manga/chapter couldn't be found",
        **NotFoundHTTPException.open_api("Manga/Chapter not found"),
    },
    400: {
        "description": "The chapter doesn't belong to that manga",
        **BadRequestHTTPException.open_api("The provided chapter doesn't belong to this manga"),
    },
    201: {
        "description": "The created session",
        "model": UploadSessionResponse,
    },
}


@router.post(
    "/begin", status_code=status.HTTP_201_CREATED, response_model=UploadSessionResponse, responses=post_responses
)
async def begin_upload_session(
    payload: UploadSessionSchema,
    user: User = Depends(is_connected),
    user_principals=Depends(get_active_principals),
    _: UploadSession = Permission("create", UploadSession.__class_acl__),
):
    await Manga.find(payload.manga_id, NotFoundHTTPException("Manga not found"))
    if payload.chapter_id:
        chapter = await Chapter.find(payload.chapter_id, NotFoundHTTPException("Chapter not found"))
        if chapter.manga_id != payload.manga_id:
            raise BadRequestHTTPException("The provided chapter doesn't belong to this manga")
        elif not await has_permission(user_principals, "edit", chapter):
            raise permission_exception
    else:
        chapter = None

    session = UploadSession(**payload.dict(), owner_id=user.id)
    await session.save()

    session_path = path.join(global_settings.temp_path, str(session.id))
    makedirs(path.join(session_path, "zip"))
    makedirs(path.join(session_path, "files"))

    if chapter:
        blobs = []
        for i in range(1, chapter.length + 1):
            blob = UploadedBlob(session_id=session.id, name=f"{i}.jpg")
            await blob.save()
            blobs.append(blob.id)
        copy_chapter_to_session(chapter, blobs)

    return await UploadSessionBlobs.find(session.id)


get_responses = {
    **auth_responses,
    404: {
        "description": "The upload session couldn't be found",
        **NotFoundHTTPException.open_api("Session not found"),
    },
    200: {
        "description": "The requested upload session",
        "model": UploadSessionResponse,
    },
}


@router.get("/{session_id}", response_model=UploadSessionResponse, responses=get_responses)
async def get_upload_session(upload_session: UploadSessionBlobs = Permission("view", _get_upload_session_blobs)):
    return upload_session


def save_session_image(files: Iterable[Tuple[UUID, str]]):
    for blob_id, file in files:
        im = Image.open(file)
        with TemporaryFile() as f:
            im.convert("RGB").save(f, "JPEG")
            f.seek(0)
            media.put(path.join("blobs", f"{blob_id}.jpg"), f)
        remove(file)


post_blobs_responses = {
    **auth_responses,
    400: {"description": "An image isn't valid", **BadRequestHTTPException.open_api("file_name is not an image")},
    404: {
        "description": "The upload session couldn't be found",
        **NotFoundHTTPException.open_api("Session not found"),
    },
    201: {
        "description": "The created blobs",
        "model": List[UploadedBlobResponse],
    },
}


def validate_image_extension(name: str):
    extensions = (".jpeg", ".jpg", ".png", ".bmp", ".webp")
    return any((name.lower().endswith(ext) for ext in extensions))


@router.post(
    "/{session_id}",
    status_code=status.HTTP_201_CREATED,
    response_model=List[UploadedBlobResponse],
    responses=post_blobs_responses,
)
async def upload_pages_to_upload_session(
    session: UploadSession = Permission("edit", _get_upload_session), payload: List[UploadFile] = File(...)
):
    compressed_formats = (
        "application/x-7z-compressed",
        "application/x-xz",
        "application/zip",
        "application/x-zip-compressed",
        "application/x-rar-compressed",
        "application/vnd.rar",
    )

    for file in payload:
        if file.content_type not in compressed_formats and not file.content_type.startswith("image/"):
            raise BadRequestHTTPException(f"'{file.filename}'s format is not supported")

    session_path = path.join(global_settings.temp_path, str(session.id))

    files_path = path.join(session_path, "files")

    blobs = []

    for file in payload:
        if file.content_type in compressed_formats:
            zip_path = path.join(session_path, f"zip/{file.filename}")
            async with open(zip_path, "wb") as out_file:
                content = await file.read()
                await out_file.write(content)

            Archive(zip_path).extractall(files_path, True)
            remove(zip_path)
            _files = listdir(files_path)
            files = [f for f in _files if path.isfile(path.join(files_path, f)) and validate_image_extension(f)]
        else:
            async with open(path.join(files_path, file.filename), "wb") as out_file:
                content = await file.read()
                await out_file.write(content)
            files = (file.filename,)

        file_blobs = []
        for f in files:
            file_blob = UploadedBlob(session_id=session.id, name=f)
            await file_blob.save()
            blobs.append(file_blob)
            file_blobs.append(file_blob.id)

        save_session_image(zip(file_blobs, (path.join(files_path, f) for f in files)))

    return blobs


def delete_session_images(ids: List[UUID]):
    media.remove([path.join("blobs", f"{blob_id}.jpg") for blob_id in ids])


delete_responses = {
    **get_responses,
    200: {
        "description": "The upload session was deleted",
        "content": {
            "application/json": {
                "example": "OK",
            },
        },
    },
}


@router.delete("/{session_id}", responses=delete_responses)
async def delete_upload_session(
    tasks: BackgroundTasks, session: UploadSessionBlobs = Permission("edit", _get_upload_session_blobs)
):
    session_images = (b.id for b in session.blobs)
    await session.delete()
    session_path = path.join(global_settings.temp_path, str(session.id))
    tasks.add_task(rmtree, session_path, True)
    tasks.add_task(delete_session_images, session_images)
    return "OK"


def commit_session_images(chapter: Chapter, pages: List[UUID], edit: bool):
    chapter_path = path.join(str(chapter.manga_id), str(chapter.id))

    if edit:
        media.rmtree(chapter_path, True)

    page_number = 1
    for page in pages:
        media.move(path.join("blobs", f"{page}.jpg"), path.join(chapter_path, f"{page_number}.jpg"))
        page_number += 1


post_commit_responses = {
    **auth_responses,
    400: {
        "description": "There is a problem with the provided page order",
        **BadRequestHTTPException.open_api("Some pages don't belong to this session"),
    },
    404: {
        "description": "The session/chapter couldn't be found",
        **NotFoundHTTPException.open_api("Session/chapter not found"),
    },
    200: {
        "description": "The edited chapter",
        "model": ChapterResponse,
    },
    201: {
        "description": "The created chapter",
        "model": ChapterResponse,
    },
}


@router.post("/{session_id}/commit", response_model=ChapterResponse, responses=post_commit_responses)
async def commit_upload_session(
    payload: CommitUploadSession, tasks: BackgroundTasks, session=Permission("edit", _get_upload_session_blobs)
):
    blobs = [b.id for b in session.blobs]
    edit = session.chapter_id is not None
    if not len(payload.page_order) > 0:
        raise BadRequestHTTPException("At least one page needs to be provided")
    if len(set(payload.page_order).difference(blobs)) > 0:
        raise BadRequestHTTPException("Some pages don't belong to this session")

    if session.chapter_id:
        chapter = await Chapter.find(session.chapter_id, NotFoundHTTPException("Chapter not found"))
        await chapter.update(length=len(payload.page_order), **payload.chapter_draft.dict())
    else:
        chapter = Chapter(
            manga_id=session.manga_id,
            length=len(payload.page_order),
            owner_id=session.owner_id,
            **payload.chapter_draft.dict(),
        )
        await chapter.save()

    session_path = path.join(global_settings.temp_path, str(session.id))
    tasks.add_task(rmtree, session_path, True)

    await session.delete()

    commit_session_images(chapter, payload.page_order, edit)
    tasks.add_task(delete_session_images, set(blobs).difference(payload.page_order))
    content = jsonable_encoder(ChapterResponse.from_orm(chapter))
    return JSONResponse(status_code=(200 if edit else 201), content=content)


delete_all_blobs_responses = {
    **get_responses,
    200: {
        "description": "All the uploaded images were deleted",
        "content": {
            "application/json": {
                "example": "OK",
            },
        },
    },
}


@router.delete("/{session_id}/files", responses=delete_all_blobs_responses)
async def delete_all_pages_from_upload_session(
    tasks: BackgroundTasks, session: UploadSessionBlobs = Permission("edit", _get_upload_session_blobs)
):
    session_images = (b.id for b in session.blobs)
    tasks.add_task(delete_session_images, session_images)

    await UploadedBlob.delete_many(session.blobs)

    return "OK"


delete_blob_responses = {
    **get_responses,
    400: {
        "description": "That file doesn't exist in the provided upload session",
        **BadRequestHTTPException.open_api("The blob doesn't exist in the session"),
    },
    200: {
        "description": "The uploaded image was deleted",
        "content": {
            "application/json": {
                "example": "OK",
            },
        },
    },
}


@router.delete("/{session_id}/{file_id}", responses=delete_blob_responses)
async def delete_page_from_upload_session(
    file_id: UUID, tasks: BackgroundTasks, session: UploadSessionBlobs = Permission("edit", _get_upload_session_blobs)
):
    if file_id not in (b.id for b in session.blobs):
        raise BadRequestHTTPException("The blob doesn't exist in the session")

    blob = await UploadedBlob.find(file_id, NotFoundHTTPException("Blob not found"))
    await blob.delete()
    tasks.add_task(delete_session_images, (file_id,))
    return "OK"


def concat_and_cut_images(blob_ids: Iterable[UUID]):
    images = [Image.open(path.join("blobs", f"{blob_id}.jpg")) for blob_id in blob_ids]
    height = sum(image.height for image in images)

    if not all((images[0].width == image.width for image in images)):
        raise BadRequestHTTPException("All the images should have the same width")

    joined = Image.new('RGB', (images[0].width, height))
    running_height = 0
    for image in images:
        joined.paste(image, (0, running_height))
        image.close()
        running_height += image.height

    amount_parts = joined.height // (2 * joined.width) + 1
    parts = []
    for i in range(amount_parts):
        end_y = min(height, 2* joined.width * (i + 1))
        part = joined.crop((0, 2 * joined.width * i, joined.width, end_y))
        parts.append(part)

    return parts


slice_blobs_responses = {
    **auth_responses,
    400: {
        "description": "There is a problem with the provided page order",
        **BadRequestHTTPException.open_api("Some pages don't belong to this session")
    },
    404: {
        "description": "The upload session couldn't be found",
        **NotFoundHTTPException.open_api("Session not found"),
    },
    201: {
        "description": "The created blobs",
        "model": List[UploadedBlobResponse],
    },
}


@router.post(
    "/{session_id}/slice",
    status_code=status.HTTP_201_CREATED,
    response_model=List[UploadedBlobResponse],
    responses=slice_blobs_responses,
)
async def slice_pages_in_upload_session(
    payload: List[UUID],
    tasks: BackgroundTasks,
    session=Permission("edit", _get_upload_session_blobs),
):
    blobs = [b.id for b in session.blobs]

    if not len(payload) > 0:
        raise BadRequestHTTPException("At least one page needs to be provided")
    if len(set(payload).difference(blobs)) > 0:
        raise BadRequestHTTPException("Some pages don't belong to this session")

    parts = concat_and_cut_images(payload)

    for i, part in enumerate(parts):
        file_blob = UploadedBlob(session_id=session.id, name=f"slice_{i+1}.jpg")
        await file_blob.save()

        with TemporaryFile() as f:
            part.save(f, "JPEG")
            f.seek(0)
            media.put(path.join("blobs", f"{file_blob.id}.jpg"), f)

        part.close()

    for blob_id in payload:
        blob: UploadedBlob = await UploadedBlob.find(blob_id)
        await blob.delete()

    tasks.add_task(delete_session_images, payload)

    return await UploadedBlob.from_session(session.id)
