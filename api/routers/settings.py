from os import path
from fastapi import APIRouter, Depends

from .auth import is_connected, auth_responses
from ..config import get_settings
from ..models.settings import Settings
from ..schemas.settings import SettingsSchema


global_settings = get_settings()
settings_path = path.join(global_settings.media_path, "settings.json")

router = APIRouter(prefix="/settings", tags=["Settings"])

custom_settings = Settings()


@router.get("", response_model=SettingsSchema)
async def get_site_settings():
    return await custom_settings.get()


put_responses = {
    **auth_responses,
    200: {
        "description": "The website settings",
        "model": SettingsSchema,
    },
}


@router.put("", dependencies=[Depends(is_connected)], response_model=SettingsSchema, responses=put_responses)
async def edit_site_settings(settings: SettingsSchema):
    await custom_settings.set(**settings.dict())
    return settings
