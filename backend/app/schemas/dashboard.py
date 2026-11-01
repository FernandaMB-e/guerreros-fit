from datetime import date
from typing import Literal

from pydantic import BaseModel

from app.models import Discipline
from app.schemas.client import MembershipState


class DashboardSummary(BaseModel):
    total_clients: int
    up_to_date: int        # al corriente: activas y por vencer
    pending_payment: int   # vencidas
    expiring_soon: int     # vencen en 3 días o menos
    no_subscription: int
    proofs_pending: int    # comprobantes por revisar


class DashboardClient(BaseModel):
    client_id: int
    full_name: str
    photo_url: str | None
    disciplines: list[Discipline]
    plan: str | None
    status: MembershipState
    end_date: date | None
    days_left: int | None  # negativo si ya venció
    urgency: Literal["urgente", "proximo"] | None  # solo en los próximos a vencer
    reminder_sent: bool


class MembershipSlice(BaseModel):
    label: str
    count: int


class DashboardOut(BaseModel):
    summary: DashboardSummary
    overdue: list[DashboardClient]
    upcoming: list[DashboardClient]
    memberships: list[MembershipSlice]