import enum
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Boolean, Date, DateTime, Enum, ForeignKey, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.client import Client
    from app.models.payment_proof import PaymentProof

class SubscriptionStatus(str, enum.Enum):
    ACTIVE = "active"
    CANCELLED = "cancelled"


class Plan(Base):
    __tablename__ = "plans"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True)
    duration_days: Mapped[int]
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)  # solo informativo
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    subscriptions: Mapped[list["Subscription"]] = relationship(back_populates="plan")


class Subscription(Base):
    __tablename__ = "subscriptions"

    id: Mapped[int] = mapped_column(primary_key=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id"), index=True)
    plan_id: Mapped[int] = mapped_column(ForeignKey("plans.id"))
    start_date: Mapped[date] = mapped_column(Date)
    end_date: Mapped[date] = mapped_column(Date, index=True)
    status: Mapped[SubscriptionStatus] = mapped_column(
        Enum(SubscriptionStatus, native_enum=False, length=20), default=SubscriptionStatus.ACTIVE
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    client: Mapped["Client"] = relationship(back_populates="subscriptions")
    plan: Mapped["Plan"] = relationship(back_populates="subscriptions")
    reminders: Mapped[list["Reminder"]] = relationship(back_populates="subscription")
    proofs: Mapped[list["PaymentProof"]] = relationship(back_populates="subscription")

    @property
    def is_expired(self) -> bool:
        return self.end_date < date.today()

    @property
    def days_left(self) -> int:
        return (self.end_date - date.today()).days


class Reminder(Base):
    """Registro de cada recordatorio de WhatsApp enviado (para mostrar 'recordatorio enviado')."""
    __tablename__ = "reminders"

    id: Mapped[int] = mapped_column(primary_key=True)
    subscription_id: Mapped[int] = mapped_column(ForeignKey("subscriptions.id"), index=True)
    sent_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    channel: Mapped[str] = mapped_column(String(20), default="whatsapp")
    status: Mapped[str] = mapped_column(String(20), default="sent")
    whatsapp_message_id: Mapped[str | None] = mapped_column(String(100))

    subscription: Mapped["Subscription"] = relationship(back_populates="reminders")