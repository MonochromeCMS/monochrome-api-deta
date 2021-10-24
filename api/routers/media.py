from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from ..fs import media

router = APIRouter(prefix="/media", tags=["Media"])


@router.get("/{file:path}")
async def get_media_file(file: str):
    """Get the media files from Deta Drive"""
    headers = {"Cache-Control": "max-age=1728000"}
    res = media.get(file)
    return StreamingResponse(res.iter_chunks(1024), media_type="image/png", headers=headers)
