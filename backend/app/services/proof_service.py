import uuid
from datetime import datetime, timezone
from io import BytesIO

from fastapi import HTTPException
from PIL import Image, ImageOps, UnidentifiedImageError
from sqlalchemy.orm import Session

from app.models import Client, PaymentProof, Plan, ProofStatus
from app.schemas.client import MembershipOut
from app.schemas.proof import ProofClient, ProofOut
from app.schemas.subscription import PlanOut
from app.services import subscription_service
from app.services.client_service import UPLOAD_ROOT, photo_url
from app.services.status import membership_status

PROOFS_DIR = UPLOAD_ROOT / "comprobantes"
MAX_PROOF_BYTES = 10 * 1024 * 1024


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def save_image_bytes(data: bytes) -> str:
    """Valida la imagen, la reduce a 1600 px como máximo y la guarda como JPEG.
    Sirve igual para las subidas manuales y, más adelante, para las de WhatsApp."""
    if len(data) > MAX_PROOF_BYTES:
        raise HTTPException(413, "La imagen pesa más de 10 MB")
    try:
        img = ImageOps.exif_transpose(Image.open(BytesIO(data))).convert("RGB")
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError):
        raise HTTPException(400, "El archivo no es una imagen válida (usa JPG o PNG)")

    img.thumbnail((1600, 1600))
    PROOFS_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"proof_{uuid.uuid4().hex}.jpg"
    img.save(PROOFS_DIR / filename, "JPEG", quality=85)
    return f"comprobantes/{filename}"


def to_out(proof: PaymentProof) -> ProofOut:
    client = proof.client
    return ProofOut(
        id=proof.id,
        status=proof.status,
        source=proof.source,
        sender_phone=proof.sender_phone,
        image_url=f"/api/proofs/{proof.id}/image",
        received_at=proof.received_at,
        reviewed_at=proof.reviewed_at,
        rejection_reason=proof.rejection_reason,
        subscription_id=proof.subscription_id,
        client=ProofClient(
            id=client.id,
            full_name=client.full_name,
            phone=client.phone,
            photo_url=photo_url(client.photo_path),
            membership=MembershipOut(**membership_status(client.subscriptions)),
        ) if client else None,
        plan=PlanOut.model_validate(proof.plan) if proof.plan else None,
    )


def ensure_pending(proof: PaymentProof) -> None:
    if proof.status != ProofStatus.PENDING:
        raise HTTPException(409, "Este comprobante ya fue revisado")


def approve(db: Session, proof: PaymentProof, client: Client, plan: Plan) -> None:
    """Aprobar = activar la suscripción: el botón único que pidió el cliente."""
    sub = subscription_service.renew(db, client, plan)
    proof.client_id = client.id
    proof.plan_id = plan.id
    proof.subscription_id = sub.id
    proof.status = ProofStatus.APPROVED
    proof.reviewed_at = _utcnow()


def reject(proof: PaymentProof, reason: str | None) -> None:
    proof.status = ProofStatus.REJECTED
    proof.rejection_reason = reason
    proof.reviewed_at = _utcnow()