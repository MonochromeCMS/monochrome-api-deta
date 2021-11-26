import logging
from os import getenv

from fastapi import FastAPI, Request
from prometheus_fastapi_instrumentator import Instrumentator
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from .config import get_settings
from .exceptions import rate_limit_exceeded_handler
from .fs import media
from .models.upload import UploadSession

global_settings = get_settings()

log = logging.getLogger(__name__)

app = FastAPI(title="Monochrome", version="1.4.3")

Instrumentator(excluded_handlers=["/metrics"]).instrument(app).expose(app, tags=["Status"])

if getenv("DETA_RUNTIME"):
    from deta import App

    app = App(app)

    @app.lib.cron()
    async def setup_media(event):
        print("Cleaning up the lingering sessions...")
        await UploadSession.flush()
        media.rmtree("blobs")
        print("Done with the clean up.")


def get_remote_address(request: Request):
    ip = (
        request.headers.get("CF-CONNECTING-IP")
        or request.headers.get("X-REAL-IP")
        or request.headers.get("X-FORWARDED-FOR")
        or request.client.host
        or "127.0.0.1"
    )
    return ip


limiter = Limiter(key_func=get_remote_address, default_limits=["60/minute"])
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)


@app.on_event("startup")
async def startup_event():
    log.info("Starting up...")


@app.on_event("shutdown")
async def shutdown_event():
    log.info("Shutting down...")
