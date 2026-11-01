from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.schedule import enrollments

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.payment_proof import PaymentProof
    from app.models.schedule import ClassSchedule
    from app.models.subscription import Subscription


class Client(Base):
    __tablename__ = "clients"

    id: Mapped[int] = mapped_column(primary_key=True)
    first_name: Mapped[str] = mapped_column(String(80))
    last_name: Mapped[str] = mapped_column(String(80))
    # WhatsApp del cliente, guardado solo con dígitos y lada (ej. 529711234567)
    phone: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    email: Mapped[str | None] = mapped_column(String(120))
    photo_path: Mapped[str | None] = mapped_column(String(255))
    guardian_name: Mapped[str | None] = mapped_column(String(120))  # tutor, para los niños de karate
    notes: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)  # archivar en lugar de borrar
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    subscriptions: Mapped[list["Subscription"]] = relationship(
        back_populates="client", order_by="Subscription.end_date.desc()"
    )
    proofs: Mapped[list["PaymentProof"]] = relationship(back_populates="client")
    schedules: Mapped[list["ClassSchedule"]] = relationship(
        secondary=enrollments, back_populates="clients"
    )

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"