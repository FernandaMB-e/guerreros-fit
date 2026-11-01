import enum
from datetime import time

from sqlalchemy import JSON, Boolean, Column, Enum, ForeignKey, Table, Time
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.client import Client

class Discipline(str, enum.Enum):
    CROSSFIT = "crossfit"
    KARATE = "karate"


# Alumnos inscritos en cada bloque de horario
enrollments = Table(
    "enrollments",
    Base.metadata,
    Column("client_id", ForeignKey("clients.id", ondelete="CASCADE"), primary_key=True),
    Column("schedule_id", ForeignKey("class_schedules.id", ondelete="CASCADE"), primary_key=True),
)


class ClassSchedule(Base):
    """Un bloque de clase, por ejemplo Karate 16:00-17:00 de lunes a viernes."""
    __tablename__ = "class_schedules"

    id: Mapped[int] = mapped_column(primary_key=True)
    discipline: Mapped[Discipline] = mapped_column(Enum(Discipline, native_enum=False, length=20))
    start_time: Mapped[time] = mapped_column(Time)
    end_time: Mapped[time] = mapped_column(Time)
    weekdays: Mapped[list[int]] = mapped_column(JSON)  # 0 = lunes ... 6 = domingo
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    clients: Mapped[list["Client"]] = relationship(secondary=enrollments, back_populates="schedules")