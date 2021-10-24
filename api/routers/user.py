from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from ..config import get_settings
from ..exceptions import NotFoundHTTPException, BadRequestHTTPException
from .auth import is_connected, get_password_hash, auth_responses, Permission, get_active_principals
from ..fastapi_permissions import has_permission
from ..models.user import User, Role
from ..schemas.user import UserSchema, UserResponse, UsersResponse, UserFilters

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
    count, page = await User.search(
        username, UserFilters(role=role, email=email, id=user_id), limit, offset
    )

    return {
        "offset": offset,
        "limit": limit,
        "results": page,
        "total": count,
    }
