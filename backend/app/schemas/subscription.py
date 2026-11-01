from datetime import date
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

from app.models import SubscriptionStatus

PlanName = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=50)]


class PlanOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    duration_days: int
    price: float
    is_active: bool


class PlanCreate(BaseModel):
    name: PlanName
    duration_days: int = Field(gt=0, le=366)
    price: float = Field(default=0, ge=0)


class PlanUpdate(BaseModel):
    name: PlanName | None = None
    duration_days: int | None = Field(default=None, gt=0, le=366)
    price: float | None = Field(default=None, ge=0)
    is_active: bool | None = None


class PlanChoice(BaseModel):
    """Sirve para renovar y para cambiar de plan."""
    plan_id: int


class SubscriptionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    client_id: int
    plan: PlanOut
    start_date: date
    end_date: date
    status: SubscriptionStatus
    is_expired: bool
    days_left: int