from fastapi import APIRouter, Depends

from .auth import is_connected, auth_responses
from ..models.settings import Settings
from ..schemas.settings import SettingsSchema

router = APIRouter(prefix="/settings", tags=["Settings"])


@router.get("", response_model=SettingsSchema)
async def get_site_settings():
    return await Settings.get()


put_responses = {
    **auth_responses,
    200: {
        "description": "The website settings",
        "model": SettingsSchema,
    },
}


@router.put("", dependencies=[Depends(is_connected)], response_model=SettingsSchema, responses=put_responses)
async def edit_site_settings(settings: SettingsSchema):
    await Settings.set(**settings.dict())
    return settings
