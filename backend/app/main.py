from fastapi import Depends, FastAPI

from app.core.config import settings
from app.core.deps import get_current_user
from app.routers import (
    auth, clients, dashboard, files, plans, proofs, schedules, subscriptions,
)
from app.services.client_service import PHOTOS_DIR

app = FastAPI(title=settings.app_name)
PHOTOS_DIR.mkdir(parents=True, exist_ok=True)

# Solo el login queda abierto; todo lo demás exige sesión
app.include_router(auth.router, prefix="/api")

protected = [Depends(get_current_user)]
for module in (clients, plans, subscriptions, proofs, schedules, dashboard, files):
    app.include_router(module.router, prefix="/api", dependencies=protected)


@app.get("/api/health")
def health():
    return {"status": "ok"}