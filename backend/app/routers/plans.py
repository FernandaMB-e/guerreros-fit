from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import Plan
from app.schemas.subscription import PlanCreate, PlanOut, PlanUpdate

router = APIRouter(prefix="/plans", tags=["Planes"])


def _name_free(db: Session, name: str, exclude_id: int | None = None) -> None:
    stmt = select(Plan).where(Plan.name == name)
    if exclude_id:
        stmt = stmt.where(Plan.id != exclude_id)
    if db.scalar(stmt):
        raise HTTPException(409, "Ya existe un plan con ese nombre")


@router.get("", response_model=list[PlanOut])
def list_plans(include_inactive: bool = False, db: Session = Depends(get_db)):
    stmt = select(Plan).order_by(Plan.duration_days)
    if not include_inactive:
        stmt = stmt.where(Plan.is_active.is_(True))
    return db.scalars(stmt).all()


@router.post("", response_model=PlanOut, status_code=201)
def create_plan(data: PlanCreate, db: Session = Depends(get_db)):
    _name_free(db, data.name)
    plan = Plan(**data.model_dump())
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return plan


@router.patch("/{plan_id}", response_model=PlanOut)
def update_plan(plan_id: int, data: PlanUpdate, db: Session = Depends(get_db)):
    plan = db.get(Plan, plan_id)
    if plan is None:
        raise HTTPException(404, "Plan no encontrado")

    changes = data.model_dump(exclude_unset=True, exclude_none=True)
    if "name" in changes:
        _name_free(db, changes["name"], exclude_id=plan_id)
    for field, value in changes.items():
        setattr(plan, field, value)

    db.commit()
    db.refresh(plan)
    return plan