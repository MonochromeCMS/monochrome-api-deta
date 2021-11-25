from .app import app
from .config import get_settings

from fastapi import Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from .routers import auth, autocomplete, chapter, comment, manga, media, settings, upload, user

global_settings = get_settings()

app.include_router(auth.router)
app.include_router(autocomplete.router)
app.include_router(chapter.router)
app.include_router(comment.router)
app.include_router(manga.router)
app.include_router(media.router)
app.include_router(settings.router)
app.include_router(upload.router)
app.include_router(user.router)


origins = global_settings.cors_origins.split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", include_in_schema=False)
async def root(request: Request):
    return RedirectResponse(f"{request.scope.get('root_path')}/docs", status_code=301)


@app.get("/ping", tags=["Status"])
async def ping():
    """
    Ping the server
    """
    return "pong"
