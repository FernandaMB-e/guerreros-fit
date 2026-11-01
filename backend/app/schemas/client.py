import re
from datetime import date, datetime, time
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator

from app.models import Discipline

MembershipState = Literal["activa", "por_vencer", "vencida", "sin_suscripcion"]
Name = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=80)]


def normalize_phone(value: str) -> str:
    """Deja solo dígitos. Si son 10, asume México y antepone 52."""
    digits = re.sub(r"\D", "", value)
    if len(digits) == 10:
        digits = "52" + digits
    if not 11 <= len(digits) <= 15:
        raise ValueError("El teléfono debe tener 10 dígitos o incluir la lada del país")
    return digits


class _Limpieza(BaseModel):
    @field_validator("phone", check_fields=False)
    @classmethod
    def _telefono(cls, v):
        return None if v is None else normalize_phone(v)

    @field_validator("email", "guardian_name", "notes", check_fields=False, mode="before")
    @classmethod
    def _vacio_a_none(cls, v):
        return None if isinstance(v, str) and not v.strip() else v


class ClientCreate(_Limpieza):
    first_name: Name
    last_name: Name
    phone: str
    email: str | None = Field(default=None, max_length=120)
    guardian_name: str | None = Field(default=None, max_length=120)
    notes: str | None = None
    schedule_ids: list[int] = []


class ClientUpdate(_Limpieza):
    first_name: Name | None = None
    last_name: Name | None = None
    phone: str | None = None
    email: str | None = Field(default=None, max_length=120)
    guardian_name: str | None = Field(default=None, max_length=120)
    notes: str | None = None
    is_active: bool | None = None
    schedule_ids: list[int] | None = None


class MembershipOut(BaseModel):
    status: MembershipState
    plan: str | None
    end_date: date | None
    days_left: int | None  # negativo si ya venció


class ScheduleBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    discipline: Discipline
    start_time: time
    end_time: time
    weekdays: list[int]


class ClientOut(BaseModel):
    id: int
    first_name: str
    last_name: str
    full_name: str
    phone: str
    email: str | None
    guardian_name: str | None
    notes: str | None
    photo_url: str | None
    is_active: bool
    created_at: datetime
    membership: MembershipOut


class ClientDetail(ClientOut):
    schedules: list[ScheduleBrief] = []
    