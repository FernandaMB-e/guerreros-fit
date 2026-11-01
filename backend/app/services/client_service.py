import uuid
from io import BytesIO
from pathlib import Path

from fastapi import HTTPException, UploadFile
from PIL import Image, ImageOps, UnidentifiedImageError

from app.core.config import settings
from app.models import Client
from app.schemas.client import ClientDetail, ClientOut, MembershipOut, ScheduleBrief
from app.services.status import membership_status

UPLOAD_ROOT = Path(settings.upload_dir)
PHOTOS_DIR = UPLOAD_ROOT / "fotos"
MAX_PHOTO_BYTES = 5 * 1024 * 1024


def photo_url(path: str | None) -> str | None:
    return f"/api/uploads/{path}" if path else None


def to_out(client: Client) -> ClientOut:
    return ClientOut(
        id=client.id,
        first_name=client.first_name,
        last_name=client.last_name,
        full_name=client.full_name,
        phone=client.phone,
        email=client.email,
        guardian_name=client.guardian_name,
        notes=client.notes,
        photo_url=photo_url(client.photo_path),
        is_active=client.is_active,
        created_at=client.created_at,
        membership=MembershipOut(**membership_status(client.subscriptions)),
    )


def to_detail(client: Client) -> ClientDetail:
    return ClientDetail(
        **to_out(client).model_dump(),
        schedules=[ScheduleBrief.model_validate(s) for s in client.schedules],
    )


def remove_photo_file(path: str | None) -> None:
    if path:
        (UPLOAD_ROOT / path).unlink(missing_ok=True)


async def save_photo(client: Client, upload: UploadFile) -> str:
    """Valida la imagen, la recorta a cuadrado de 400 px y la guarda como JPEG."""
    data = await upload.read()
    if len(data) > MAX_PHOTO_BYTES:
        raise HTTPException(413, "La foto pesa más de 5 MB")
    try:
        img = ImageOps.exif_transpose(Image.open(BytesIO(data))).convert("RGB")
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError):
        raise HTTPException(400, "El archivo no es una imagen válida (usa JPG o PNG)")

    img = ImageOps.fit(img, (400, 400))
    PHOTOS_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"client_{client.id}_{uuid.uuid4().hex[:8]}.jpg"
    img.save(PHOTOS_DIR / filename, "JPEG", quality=85)

    remove_photo_file(client.photo_path)  # borra la foto anterior
    return f"fotos/{filename}"