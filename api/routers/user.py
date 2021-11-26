from os import path
from tempfile import TemporaryFile
from typing import Optional
from uuid import UUID

from fastapi import (APIRouter, Depends, File, Query, Request, UploadFile,
                     status)
from PIL import Image

from ..app import limiter
from ..config import get_settings
from ..exceptions import BadRequestHTTPException, NotFoundHTTPException
from ..fastapi_permissions import has_permission
from ..fs import media
from ..models.user import Role, User
from ..schemas.user import (UserFilters, UserRegisterSchema, UserResponse,
                            UserSchema, UsersResponse)
from .auth import (Permission, auth_responses, get_active_principals,
                   get_password_hash, is_connected)

settings = get_settings()

router = APIRouter(prefix="/user", tags=["User"])


async def _get_user(user_id: UUID):
    return await User.find(user_id, NotFoundHTTPException("User not found"))


get_me_responses = {
    **auth_responses,
    200: {
        "description": "The current user",
        "model": UserResponse,
    },
}


@router.get("/me", response_model=UserResponse, responses=get_me_responses)
async def get_current_user(user: User = Depends(is_connected)):
    """Provides information about the user logged in."""
    return user


get_responses = {
    **auth_responses,
    404: {
        "description": "The user couldn't be found",
        **NotFoundHTTPException.open_api("User not found"),
    },
    200: {
        "description": "The requested user",
        "model": UserResponse,
    },
}


@router.get("/{user_id}", response_model=UserResponse, responses=get_responses)
async def get_user(user: User = Permission("view", _get_user)):
    """Provides information about a user."""
    return user


put_responses = {
    **get_responses,
    400: {
        "description": "Existing user",
        **BadRequestHTTPException.open_api("That username or email is already in use"),
    },
    200: {
        "description": "The edited user",
        "model": UserResponse,
    },
}


@router.put("/{user_id}", response_model=UserResponse, responses=put_responses)
async def update_user(
    payload: UserSchema,
    user: User = Permission("edit", _get_user),
    user_principals=Depends(get_active_principals),
):
    hashed_pwd = get_password_hash(payload.password)

    if await User.from_username_email(payload.username, payload.email, user.id):
        raise BadRequestHTTPException("That username or email is already in use")

    data = payload.dict()
    data.pop("password")

    if not await has_permission(user_principals, "edit", User.__class_acl__()):
        data.pop("role")

    await user.update(**data, hashed_password=hashed_pwd)

    return user


delete_responses = {
    **get_responses,
    400: {
        "description": "Own user",
        **BadRequestHTTPException.open_api("You can't delete your own user"),
    },
    200: {
        "description": "The user was deleted",
        "content": {
            "application/json": {
                "example": "OK",
            },
        },
    },
}


@router.delete("/{user_id}", responses=delete_responses)
async def delete_user(user: User = Permission("edit", _get_user)):
    return await user.delete()


post_responses = {
    **auth_responses,
    400: {
        "description": "Existing user",
        **BadRequestHTTPException.open_api("That username or email is already in use"),
    },
    201: {
        "description": "The created user",
        "model": UserResponse,
    },
}


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED, responses=post_responses)
async def create_user(payload: UserSchema, _: User = Permission("create", User.__class_acl__)):
    hashed_pwd = get_password_hash(payload.password)

    if await User.from_username_email(payload.username, payload.email):
        raise BadRequestHTTPException("That username or email is already in use")

    data = payload.dict()
    data.pop("password")
    user = User(**data, hashed_password=hashed_pwd)
    await user.save()

    return user


if settings.allow_registration:
    register_responses = {
        400: {
            "description": "Existing user",
            **BadRequestHTTPException.open_api("That username or email is already in use"),
        },
        201: {
            "description": "The created user",
            "model": UserResponse,
        },
    }

    @router.post(
        "/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED, responses=register_responses
    )
    @limiter.limit("1/minute")
    async def register_user(
        request: Request,
        payload: UserRegisterSchema,
        _: User = Permission("register", User.__class_acl__),
    ):
        hashed_pwd = get_password_hash(payload.password)

        if await User.from_username_email(payload.username, payload.email):
            raise BadRequestHTTPException("That username or email is already in use")

        data = payload.dict()
        data.pop("password")
        user = User(**data, role=Role.user, hashed_password=hashed_pwd)
        await user.save()

        return user


get_all_responses = {
    **auth_responses,
    200: {
        "description": "The created user",
        "model": UsersResponse,
    },
}


@router.get("", response_model=UsersResponse, responses=get_all_responses, dependencies=[])
async def search_users(
    limit: Optional[int] = Query(10, ge=1, le=settings.max_page_limit),
    offset: Optional[int] = Query(0, ge=0),
    username: str = "",
    role: Optional[Role] = None,
    email: Optional[str] = None,
    user_id: Optional[UUID] = None,
    _: User = Permission("view", User.__class_acl__),
):
    count, page = await User.search(username, UserFilters(role=role, email=email, id=user_id), limit, offset)

    return {
        "offset": offset,
        "limit": limit,
        "results": page,
        "total": count,
    }


def save_avatar(user_id: UUID, file: File):
    im = Image.open(file)
    with TemporaryFile() as f:
        im.convert("RGB").save(f, "JPEG")
        f.seek(0)
        media.put(path.join("users", f"{user_id}.jpg"), f)


put_avatar_responses = {
    **get_responses,
    400: {
        "description": "The avatar isn't a valid image",
        **BadRequestHTTPException.open_api("<image_name> is not an image"),
    },
    200: {
        "description": "The edited user",
        "model": UserResponse,
    },
}


@router.put("/{user_id}/avatar", responses=put_avatar_responses)
async def set_avatar(
    payload: UploadFile = File(...),
    user: User = Permission("edit", _get_user),
):
    if not payload.content_type.startswith("image/"):
        raise BadRequestHTTPException(f"'{payload.filename}' is not an image")

    save_avatar(user.id, payload.file)
    await user.save()

    return user
