import re

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy import or_, select
from sqlalchemy.orm import Session, selectinload

from app.db.session import get_db
from app.models import ClassSchedule, Client, Subscription
from app.schemas.client import (
    ClientCreate, ClientDetail, ClientOut, ClientUpdate, MembershipState,
)
from app.services import client_service as svc

router = APIRouter(prefix="/clients", tags=["Clientes"])


def _load(db: Session, client_id: int) -> Client:
    stmt = (
        select(Client)
        .where(Client.id == client_id)
        .options(
            selectinload(Client.subscriptions).selectinload(Subscription.plan),
            selectinload(Client.schedules),
        )
    )
    client = db.scalar(stmt)
    if client is None:
        raise HTTPException(404, "Cliente no encontrado")
    return client


def _schedules(db: Session, ids: list[int]) -> list[ClassSchedule]:
    unique = set(ids)
    if not unique:
        return []
    found = list(db.scalars(select(ClassSchedule).where(ClassSchedule.id.in_(unique))))
    if len(found) != len(unique):
        raise HTTPException(422, "Alguno de los horarios no existe")
    return found


def _check_phone_free(db: Session, phone: str, exclude_id: int | None = None) -> None:
    stmt = select(Client).where(Client.phone == phone)
    if exclude_id:
        stmt = stmt.where(Client.id != exclude_id)
    existing = db.scalar(stmt)
    if existing is None:
        return
    if not existing.is_active:
        raise HTTPException(
            409,
            f"Ese número pertenece a {existing.full_name}, que está archivado. "
            "Restáuralo en lugar de registrarlo de nuevo.",
        )
    raise HTTPException(409, f"Ya existe un cliente con ese número: {existing.full_name}")


@router.get("", response_model=list[ClientOut])
def list_clients(
    q: str | None = Query(None, description="Nombre, apellido o teléfono"),
    membership: MembershipState | None = None,
    include_archived: bool = False,
    limit: int = Query(200, ge=1, le=500),
    db: Session = Depends(get_db),
):
    """Lista y busca clientes. Los vencidos también aparecen: nunca se pierden sus datos."""
    stmt = select(Client).options(
        selectinload(Client.subscriptions).selectinload(Subscription.plan)
    )
    if not include_archived:
        stmt = stmt.where(Client.is_active.is_(True))

    for token in (q or "").split():
        conditions = [
            Client.first_name.ilike(f"%{token}%"),
            Client.last_name.ilike(f"%{token}%"),
        ]
        digits = re.sub(r"\D", "", token)
        if digits:
            conditions.append(Client.phone.like(f"%{digits}%"))
        stmt = stmt.where(or_(*conditions))

    stmt = stmt.order_by(Client.first_name, Client.last_name)
    results = [svc.to_out(c) for c in db.scalars(stmt)]
    if membership:  # el estado se calcula con las fechas, por eso se filtra aquí
        results = [c for c in results if c.membership.status == membership]
    return results[:limit]


@router.post("", response_model=ClientDetail, status_code=201)
def create_client(data: ClientCreate, db: Session = Depends(get_db)):
    _check_phone_free(db, data.phone)
    client = Client(**data.model_dump(exclude={"schedule_ids"}))
    client.schedules = _schedules(db, data.schedule_ids)
    db.add(client)
    db.commit()
    return svc.to_detail(_load(db, client.id))


@router.get("/{client_id}", response_model=ClientDetail)
def get_client(client_id: int, db: Session = Depends(get_db)):
    return svc.to_detail(_load(db, client_id))


@router.patch("/{client_id}", response_model=ClientDetail)
def update_client(client_id: int, data: ClientUpdate, db: Session = Depends(get_db)):
    client = _load(db, client_id)
    changes = data.model_dump(exclude_unset=True)
    schedule_ids = changes.pop("schedule_ids", None)

    for field in ("first_name", "last_name", "phone", "is_active"):
        if field in changes and changes[field] is None:
            raise HTTPException(422, f"El campo {field} no puede quedar vacío")
    if "phone" in changes:
        _check_phone_free(db, changes["phone"], exclude_id=client_id)

    for field, value in changes.items():
        setattr(client, field, value)
    if schedule_ids is not None:
        client.schedules = _schedules(db, schedule_ids)

    db.commit()
    return svc.to_detail(_load(db, client_id))


@router.post("/{client_id}/photo", response_model=ClientDetail)
async def upload_photo(
    client_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)
):
    client = _load(db, client_id)
    client.photo_path = await svc.save_photo(client, file)
    db.commit()
    return svc.to_detail(_load(db, client_id))


@router.delete("/{client_id}/photo", response_model=ClientDetail)
def delete_photo(client_id: int, db: Session = Depends(get_db)):
    client = _load(db, client_id)
    svc.remove_photo_file(client.photo_path)
    client.photo_path = None
    db.commit()
    return svc.to_detail(_load(db, client_id))