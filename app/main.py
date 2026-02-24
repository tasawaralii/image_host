from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from .config import RESOLUTIONS, UPLOAD_DIR
from .db import init_db
from .routes.backup import router as backup_router
from .routes.health import router as health_router
from .routes.images import router as images_router
from .services.storage_service import ensure_upload_dirs

app = FastAPI(title="Anime Image Service", version="1.0.0")

init_db()
ensure_upload_dirs(UPLOAD_DIR, RESOLUTIONS)

app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

app.include_router(health_router)
app.include_router(images_router)
app.include_router(backup_router)