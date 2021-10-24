from typing import List

from fastapi import APIRouter

from ..models.chapter import Chapter


router = APIRouter(prefix="/autocomplete", tags=["Autocomplete"])


@router.get("/groups", response_model=List[str])
async def get_scan_groups():
    groups = await Chapter.get_groups()
    if "no group" not in groups:
        groups.append("no group")
    return groups
