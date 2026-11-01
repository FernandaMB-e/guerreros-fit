from datetime import date, timedelta

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models import Client, Plan, Subscription
from app.services.status import current_subscription


def get_active_plan(db: Session, plan_id: int) -> Plan:
    plan = db.get(Plan, plan_id)
    if plan is None or not plan.is_active:
        raise HTTPException(404, "El plan no existe o está desactivado")
    return plan


def renew(db: Session, client: Client, plan: Plan, today: date | None = None) -> Subscription:
    """Nueva suscripción a continuación de la actual, o desde hoy si ya venció."""
    if not client.is_active:
        raise HTTPException(409, "El cliente está archivado. Restáuralo antes de renovar.")

    today = today or date.today()
    current = current_subscription(client.subscriptions)
    start = max(today, current.end_date) if current else today

    sub = Subscription(
        client_id=client.id,
        plan_id=plan.id,
        start_date=start,
        end_date=start + timedelta(days=plan.duration_days),
    )
    db.add(sub)
    db.flush()  # el commit lo hace quien llama, para poder agrupar varias operaciones
    return sub


def change_plan(db: Session, client: Client, new_plan: Plan, today: date | None = None) -> Subscription:
    """Cambia el plan de la suscripción vigente (por ejemplo, de 15 días a mensual)."""
    today = today or date.today()
    current = current_subscription(client.subscriptions)

    if current is None or current.end_date < today:
        raise HTTPException(409, "El cliente no tiene una suscripción vigente. Usa renovar.")
    if current.plan_id == new_plan.id:
        raise HTTPException(409, "El cliente ya tiene ese plan")

    new_end = current.start_date + timedelta(days=new_plan.duration_days)
    if new_end < today:
        raise HTTPException(422, "Con ese plan la suscripción ya habría terminado. Renueva en su lugar.")

    current.plan = new_plan
    current.end_date = new_end
    db.flush()
    return current