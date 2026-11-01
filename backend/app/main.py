from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.routers import clients, plans, proofs, subscriptions
from app.services.client_service import PHOTOS_DIR

app = FastAPI(title=settings.app_name)

app.include_router(clients.router, prefix="/api")
app.include_router(plans.router, prefix="/api")
app.include_router(subscriptions.router, prefix="/api")
app.include_router(proofs.router, prefix="/api")
# Solo se sirven las fotos. Los comprobantes irán detrás del login más adelante.
PHOTOS_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/api/uploads/fotos", StaticFiles(directory=PHOTOS_DIR), name="fotos")


@app.get("/api/health")
def health():
    return {"status": "ok"}