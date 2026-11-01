from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, StringConstraints

from app.models import ProofStatus
from app.schemas.client import MembershipOut
from app.schemas.subscription import PlanOut


class ProofClient(BaseModel):
    id: int
    full_name: str
    phone: str
    photo_url: str | None
    membership: MembershipOut


class ProofOut(BaseModel):
    id: int
    status: ProofStatus
    source: str  # whatsapp o manual
    sender_phone: str | None
    image_url: str
    received_at: datetime  # se guarda en UTC; el frontend la muestra en hora local
    reviewed_at: datetime | None
    rejection_reason: str | None
    subscription_id: int | None
    client: ProofClient | None  # vacío si el número no está registrado
    plan: PlanOut | None


class ProofApprove(BaseModel):
    """Solo hace falta cuando el comprobante no trae cliente o plan."""
    client_id: int | None = None
    plan_id: int | None = None


class ProofReject(BaseModel):
    reason: Annotated[str, StringConstraints(strip_whitespace=True, max_length=300)] | None = None


class ProofCounts(BaseModel):
    pending: int
    approved: int
    rejected: int