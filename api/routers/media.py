from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from ..exceptions import NotFoundHTTPException
from ..fs import media

router = APIRouter(prefix="/media", tags=["Media"])


@router.get("/{file:path}")
async def get_media_file(file: str):
    """Get the media files from Deta Drive"""
    headers = {"Cache-Control": "max-age=1728000"}

    try:
        res = media.get(file)
    except FileNotFoundError:
        raise NotFoundHTTPException()
    return StreamingResponse(res.iter_chunks(1024), media_type="image/png", headers=headers)
