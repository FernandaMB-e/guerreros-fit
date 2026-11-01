from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.db.session import get_db
from app.models import ClassSchedule, Client, Subscription, enrollments
from app.routers.clients import _load as load_client
from app.schemas.schedule import (
    EnrollRequest, ScheduleCreate, ScheduleDetail, ScheduleOut, ScheduleUpdate,
)
from app.services import client_service

router = APIRouter(prefix="/schedules", tags=["Horarios"])


def _student_counts(db: Session) -> dict[int, int]:
    """Alumnos activos por bloque."""
    stmt = (
        select(enrollments.c.schedule_id, func.count())
        .join(Client, Client.id == enrollments.c.client_id)
        .where(Client.is_active.is_(True))
        .group_by(enrollments.c.schedule_id)
    )
    return dict(db.execute(stmt).all())


def _out(schedule: ClassSchedule, count: int) -> ScheduleOut:
    return ScheduleOut(
        id=schedule.id,
        discipline=schedule.discipline,
        start_time=schedule.start_time,
        end_time=schedule.end_time,
        weekdays=schedule.weekdays,
        is_active=schedule.is_active,
        student_count=count,
    )


def _load(db: Session, schedule_id: int) -> ClassSchedule:
    stmt = (
        select(ClassSchedule)
        .where(ClassSchedule.id == schedule_id)
        .options(
            selectinload(ClassSchedule.clients)
            .selectinload(Client.subscriptions)
            .selectinload(Subscription.plan)
        )
    )
    schedule = db.scalar(stmt)
    if schedule is None:
        raise HTTPException(404, "Horario no encontrado")
    return schedule


def _detail(schedule: ClassSchedule) -> ScheduleDetail:
    students = sorted(
        (c for c in schedule.clients if c.is_active),
        key=lambda c: (c.first_name, c.last_name),
    )
    return ScheduleDetail(
        **_out(schedule, len(students)).model_dump(),
        students=[client_service.to_out(c) for c in students],
    )


@router.get("", response_model=list[ScheduleOut])
def list_schedules(include_inactive: bool = False, db: Session = Depends(get_db)):
    stmt = select(ClassSchedule).order_by(ClassSchedule.start_time, ClassSchedule.discipline)
    if not include_inactive:
        stmt = stmt.where(ClassSchedule.is_active.is_(True))
    counts = _student_counts(db)
    return [_out(s, counts.get(s.id, 0)) for s in db.scalars(stmt)]


@router.post("", response_model=ScheduleOut, status_code=201)
def create_schedule(data: ScheduleCreate, db: Session = Depends(get_db)):
    schedule = ClassSchedule(**data.model_dump())
    db.add(schedule)
    db.commit()
    return _out(schedule, 0)


@router.get("/{schedule_id}", response_model=ScheduleDetail)
def get_schedule(schedule_id: int, db: Session = Depends(get_db)):
    return _detail(_load(db, schedule_id))


@router.patch("/{schedule_id}", response_model=ScheduleOut)
def update_schedule(schedule_id: int, data: ScheduleUpdate, db: Session = Depends(get_db)):
    schedule = db.get(ClassSchedule, schedule_id)
    if schedule is None:
        raise HTTPException(404, "Horario no encontrado")

    for field, value in data.model_dump(exclude_unset=True, exclude_none=True).items():
        setattr(schedule, field, value)
    if schedule.end_time <= schedule.start_time:
        raise HTTPException(422, "La hora de fin debe ser posterior a la de inicio")

    db.commit()
    return _out(schedule, _student_counts(db).get(schedule.id, 0))


@router.post("/{schedule_id}/students", response_model=ScheduleDetail)
def enroll_student(schedule_id: int, data: EnrollRequest, db: Session = Depends(get_db)):
    schedule = _load(db, schedule_id)
    client = load_client(db, data.client_id)

    if not schedule.is_active:
        raise HTTPException(409, "Este horario está desactivado")
    if not client.is_active:
        raise HTTPException(409, "El cliente está archivado")
    if any(c.id == client.id for c in schedule.clients):
        raise HTTPException(409, "El cliente ya está inscrito en este horario")

    schedule.clients.append(client)
    db.commit()
    return _detail(_load(db, schedule_id))


@router.delete("/{schedule_id}/students/{client_id}", response_model=ScheduleDetail)
def remove_student(schedule_id: int, client_id: int, db: Session = Depends(get_db)):
    schedule = _load(db, schedule_id)
    enrolled = next((c for c in schedule.clients if c.id == client_id), None)
    if enrolled is None:
        raise HTTPException(404, "El cliente no está inscrito en este horario")

    schedule.clients.remove(enrolled)
    db.commit()
    return _detail(_load(db, schedule_id))