from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.db.session import get_db
from app.models import Client, PaymentProof, ProofStatus, Subscription
from app.routers.clients import _load as load_client
from app.schemas.proof import ProofApprove, ProofCounts, ProofOut, ProofReject
from app.services import proof_service as svc
from app.services.subscription_service import get_active_plan

router = APIRouter(prefix="/proofs", tags=["Comprobantes"])


def _options():
    return (
        selectinload(PaymentProof.client)
        .selectinload(Client.subscriptions)
        .selectinload(Subscription.plan),
        selectinload(PaymentProof.plan),
    )


def _load(db: Session, proof_id: int) -> PaymentProof:
    stmt = select(PaymentProof).where(PaymentProof.id == proof_id).options(*_options())
    proof = db.scalar(stmt)
    if proof is None:
        raise HTTPException(404, "Comprobante no encontrado")
    return proof


# Esta ruta va antes que /{proof_id} para que "summary" no se confunda con un id
@router.get("/summary", response_model=ProofCounts)
def summary(db: Session = Depends(get_db)):
    rows = db.execute(select(PaymentProof.status, func.count()).group_by(PaymentProof.status)).all()
    counts = {status.value: total for status, total in rows}
    return ProofCounts(
        pending=counts.get("pending", 0),
        approved=counts.get("approved", 0),
        rejected=counts.get("rejected", 0),
    )


@router.get("", response_model=list[ProofOut])
def list_proofs(
    status: ProofStatus = ProofStatus.PENDING,
    limit: int = Query(100, ge=1, le=300),
    db: Session = Depends(get_db),
):
    """Los pendientes salen del más antiguo al más nuevo; los demás, al revés."""
    order = (
        PaymentProof.received_at.asc()
        if status == ProofStatus.PENDING
        else PaymentProof.received_at.desc()
    )
    stmt = select(PaymentProof).where(PaymentProof.status == status).options(*_options())
    stmt = stmt.order_by(order).limit(limit)
    return [svc.to_out(p) for p in db.scalars(stmt)]


@router.post("", response_model=ProofOut, status_code=201)
async def create_proof(
    file: UploadFile = File(...),
    client_id: int | None = Form(None),
    plan_id: int | None = Form(None),
    db: Session = Depends(get_db),
):
    """Subida manual de un comprobante (respaldo cuando no llegue por WhatsApp)."""
    client = load_client(db, client_id) if client_id else None
    if plan_id:
        get_active_plan(db, plan_id)

    path = svc.save_image_bytes(await file.read())
    proof = PaymentProof(
        client_id=client_id,
        plan_id=plan_id,
        sender_phone=client.phone if client else None,
        image_path=path,
        source="manual",
    )
    db.add(proof)
    db.commit()
    return svc.to_out(_load(db, proof.id))


@router.get("/{proof_id}", response_model=ProofOut)
def get_proof(proof_id: int, db: Session = Depends(get_db)):
    return svc.to_out(_load(db, proof_id))


@router.get("/{proof_id}/image")
def proof_image(proof_id: int, db: Session = Depends(get_db)):
    proof = db.get(PaymentProof, proof_id)
    if proof is None:
        raise HTTPException(404, "Comprobante no encontrado")
    path = svc.UPLOAD_ROOT / proof.image_path
    if not path.is_file():
        raise HTTPException(404, "La imagen ya no existe en el servidor")
    return FileResponse(path, media_type="image/jpeg", headers={"Cache-Control": "private, max-age=3600"})


@router.post("/{proof_id}/approve", response_model=ProofOut)
def approve_proof(proof_id: int, data: ProofApprove, db: Session = Depends(get_db)):
    proof = _load(db, proof_id)
    svc.ensure_pending(proof)

    client_id = data.client_id or proof.client_id
    plan_id = data.plan_id or proof.plan_id
    if not client_id:
        raise HTTPException(422, "Indica a qué cliente pertenece el comprobante")
    if not plan_id:
        raise HTTPException(422, "Indica qué plan pagó el cliente")

    svc.approve(db, proof, load_client(db, client_id), get_active_plan(db, plan_id))
    db.commit()
    return svc.to_out(_load(db, proof_id))


@router.post("/{proof_id}/reject", response_model=ProofOut)
def reject_proof(proof_id: int, data: ProofReject, db: Session = Depends(get_db)):
    proof = _load(db, proof_id)
    svc.ensure_pending(proof)
    svc.reject(proof, data.reason)
    db.commit()
    return svc.to_out(_load(db, proof_id))