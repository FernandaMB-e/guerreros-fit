import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.client import Client
    from app.models.subscription import Plan, Subscription
    from app.models.user import User

class ProofStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class PaymentProof(Base):
    """Imagen del comprobante que llega por WhatsApp. No procesa pagos, solo se revisa."""
    __tablename__ = "payment_proofs"

    id: Mapped[int] = mapped_column(primary_key=True)
    # Puede quedar vacío si el número que escribió no está registrado
    client_id: Mapped[int | None] = mapped_column(ForeignKey("clients.id"), index=True)
    plan_id: Mapped[int | None] = mapped_column(ForeignKey("plans.id"))
    sender_phone: Mapped[str | None] = mapped_column(String(20))
    image_path: Mapped[str] = mapped_column(String(255))
    whatsapp_message_id: Mapped[str | None] = mapped_column(String(100), unique=True)
    source: Mapped[str] = mapped_column(String(20), default="whatsapp")  # whatsapp o manual
    status: Mapped[ProofStatus] = mapped_column(
        Enum(ProofStatus, native_enum=False, length=20), default=ProofStatus.PENDING, index=True
    )
    received_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime)
    reviewed_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    rejection_reason: Mapped[str | None] = mapped_column(Text)
    subscription_id: Mapped[int | None] = mapped_column(ForeignKey("subscriptions.id"))

    client: Mapped["Client | None"] = relationship(back_populates="proofs")
    plan: Mapped["Plan | None"] = relationship()
    subscription: Mapped["Subscription | None"] = relationship(back_populates="proofs")
    reviewed_by: Mapped["User | None"] = relationship()