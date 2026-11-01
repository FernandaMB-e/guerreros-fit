from datetime import time

from pydantic import BaseModel, field_validator, model_validator

from app.models import Discipline
from app.schemas.client import ClientOut


def _check_weekdays(value: list[int] | None) -> list[int] | None:
    if value is None:
        return value
    days = sorted(set(value))
    if not days:
        raise ValueError("Elige al menos un día")
    if days[0] < 0 or days[-1] > 6:
        raise ValueError("Los días van de 0 (lunes) a 6 (domingo)")
    return days


class ScheduleCreate(BaseModel):
    discipline: Discipline
    start_time: time
    end_time: time
    weekdays: list[int]

    _weekdays = field_validator("weekdays")(_check_weekdays)

    @model_validator(mode="after")
    def _check_times(self):
        if self.end_time <= self.start_time:
            raise ValueError("La hora de fin debe ser posterior a la de inicio")
        return self


class ScheduleUpdate(BaseModel):
    discipline: Discipline | None = None
    start_time: time | None = None
    end_time: time | None = None
    weekdays: list[int] | None = None
    is_active: bool | None = None

    _weekdays = field_validator("weekdays")(_check_weekdays)


class ScheduleOut(BaseModel):
    id: int
    discipline: Discipline
    start_time: time
    end_time: time
    weekdays: list[int]
    is_active: bool
    student_count: int


class ScheduleDetail(ScheduleOut):
    students: list[ClientOut]


class EnrollRequest(BaseModel):
    client_id: int