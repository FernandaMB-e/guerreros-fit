from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from app.services.client_service import PHOTOS_DIR

router = APIRouter(prefix="/uploads", tags=["Archivos"])


@router.get("/fotos/{filename}")
def get_photo(filename: str):
    path = PHOTOS_DIR / Path(filename).name  # .name descarta cualquier intento de salirse de la carpeta
    if not path.is_file():
        raise HTTPException(404, "Foto no encontrada")
    return FileResponse(path, media_type="image/jpeg", headers={"Cache-Control": "private, max-age=86400"})