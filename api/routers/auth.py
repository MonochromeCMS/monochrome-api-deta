from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from fastapi import Depends, APIRouter, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt, ExpiredSignatureError
from passlib.context import CryptContext

from ..app import limiter
from ..config import get_settings
from ..exceptions import AuthFailedHTTPException
from ..schemas.user import TokenResponse
from ..models.user import User


auth_responses = {
    401: {
        "description": "User isn't authenticated",
        **AuthFailedHTTPException.open_api(),
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


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return encoded_jwt


async def get_connected_user(token: str = Depends(oauth2_scheme)):
    if not token:
        return None
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        _id: str = payload.get("sub")
        if _id is None:
            return None
    except ExpiredSignatureError:
        return None
    except JWTError:
        return None
    user = await User.find(UUID(_id), None)
    return user


async def is_connected(user: User = Depends(get_connected_user)):
    if user:
        return user
    else:
        raise AuthFailedHTTPException()


token_responses = {
    200: {"description": "A token for the logged in user", "model": TokenResponse},
    401: {
        "description": "Credentials don't match",
        **AuthFailedHTTPException.open_api("Wrong username/password"),
    },
}


@router.post("/token", response_model=TokenResponse, responses=token_responses)
@limiter.limit("3/minute")
async def login_for_access_token(request: Request, form_data: OAuth2PasswordRequestForm = Depends()):
    """Provides an OAuth2 token if the credentials are right."""
    user = await authenticate_user(form_data.username, form_data.password)
    if not user:
        raise AuthFailedHTTPException("Wrong username/password")
    access_token_expires = timedelta(minutes=settings.jwt_access_token_expire_minutes)
    access_token = create_access_token(data={"sub": str(user.id)}, expires_delta=access_token_expires)
    return {"access_token": access_token, "token_type": "bearer"}
