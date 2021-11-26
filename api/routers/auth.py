from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import ExpiredSignatureError, JWTError, jwt
from passlib.context import CryptContext

from ..app import limiter
from ..config import get_settings
from ..exceptions import AuthFailedHTTPException, PermissionsHTTPException
from ..fastapi_permissions import (Authenticated, Everyone,
                                   configure_permissions)
from ..models.user import User
from ..schemas.user import RefreshToken, TokenContent, TokenResponse

auth_responses = {
    401: {
        "description": "User isn't authenticated",
        **AuthFailedHTTPException.open_api(),
    },
    403: {
        "description": "User doesn't have the permission to perform this action",
        **PermissionsHTTPException.open_api(),
    },
}

settings = get_settings()

router = APIRouter(tags=["Auth"], prefix="/auth")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token", auto_error=False)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password):
    return pwd_context.hash(password)


async def authenticate_user(username_mail: str, password: str):
    user = await User.from_username_email(username_mail)
    if user and pwd_context.verify(password, user.hashed_password):
        return user


def create_token(sub: UUID, typ: str, expires_delta: Optional[timedelta] = None):
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode = TokenContent(sub=str(sub), exp=expire, iat=datetime.utcnow(), typ=typ).dict()
    encoded_jwt = jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return encoded_jwt


async def get_connected_user(token: str = Depends(oauth2_scheme)):
    if not token:
        return None
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        _id: str = payload.get("sub")
        _type: str = payload.get("typ")
        if _id is None or _type != "session":
            return None
    except ExpiredSignatureError:
        return None
    except JWTError:
        return None
    user = await User.find(UUID(_id), None)
    return user


async def validate_refresh_token(token: str):
    if not token:
        return None
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        _id: str = payload.get("sub")
        _type: str = payload.get("typ")
        if _id is None or _type != "refresh":
            raise AuthFailedHTTPException("Invalid token")
    except ExpiredSignatureError:
        raise AuthFailedHTTPException("Expired token")
    except JWTError:
        raise AuthFailedHTTPException("Invalid token")
    user = await User.find(UUID(_id), None)
    return user


async def is_connected(user: User = Depends(get_connected_user)):
    if user:
        return user
    else:
        raise AuthFailedHTTPException()


async def get_active_principals(user: User = Depends(get_connected_user)):
    if user:
        principals = [Everyone, Authenticated]
        principals.extend(getattr(user, "principals", []))
    else:
        principals = [Everyone]
    return principals


Permission = configure_permissions(get_active_principals)


def token_response(user: User):
    access_token_expires = timedelta(minutes=settings.jwt_access_token_expire_minutes)
    refresh_token_expires = timedelta(days=15)

    access_token = create_token(sub=user.id, typ="session", expires_delta=access_token_expires)
    refresh_token = create_token(sub=user.id, typ="refresh", expires_delta=refresh_token_expires)
    return {
        "token_type": "bearer",
        "access_token": access_token,
        "refresh_token": refresh_token,
    }


token_responses = {
    200: {"description": "A token for the logged in user", "model": TokenResponse},
    401: {
        "description": "Credentials don't match",
        **AuthFailedHTTPException.open_api("Wrong username/password"),
    },
}


@router.post("/token", response_model=TokenResponse, responses=token_responses)
@limiter.limit("10/minute")
async def login_for_access_token(request: Request, form_data: OAuth2PasswordRequestForm = Depends()):
    """Provides an OAuth2 token if the credentials are right."""
    user = await authenticate_user(form_data.username, form_data.password)
    if not user:
        raise AuthFailedHTTPException("Wrong username/password")
    return token_response(user)


@router.post("/refresh", response_model=TokenResponse, responses=token_responses)
@limiter.limit("1/minute")
async def refresh_access_token(request: Request, body: RefreshToken):
    user = await validate_refresh_token(body.token)
    return token_response(user)
