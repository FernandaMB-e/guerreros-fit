from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import Subscription, SubscriptionStatus
from app.routers.clients import _load as load_client
from app.schemas.subscription import PlanChoice, SubscriptionOut
from app.services import subscription_service as svc

router = APIRouter(tags=["Suscripciones"])


@router.get("/clients/{client_id}/subscriptions", response_model=list[SubscriptionOut])
def list_subscriptions(client_id: int, db: Session = Depends(get_db)):
    """Historial del cliente, de la más reciente a la más antigua."""
    return load_client(db, client_id).subscriptions


@router.post("/clients/{client_id}/subscriptions/renew", response_model=SubscriptionOut, status_code=201)
def renew_subscription(client_id: int, data: PlanChoice, db: Session = Depends(get_db)):
    client = load_client(db, client_id)
    plan = svc.get_active_plan(db, data.plan_id)
    sub = svc.renew(db, client, plan)
    db.commit()
    db.refresh(sub)
    return sub


@router.post("/clients/{client_id}/subscriptions/change-plan", response_model=SubscriptionOut)
def change_subscription_plan(client_id: int, data: PlanChoice, db: Session = Depends(get_db)):
    client = load_client(db, client_id)
    plan = svc.get_active_plan(db, data.plan_id)
    sub = svc.change_plan(db, client, plan)
    db.commit()
    db.refresh(sub)
    return sub


@router.post("/subscriptions/{subscription_id}/cancel", response_model=SubscriptionOut)
def cancel_subscription(subscription_id: int, db: Session = Depends(get_db)):
    sub = db.get(Subscription, subscription_id)
    if sub is None:
        raise HTTPException(404, "Suscripción no encontrada")
    sub.status = SubscriptionStatus.CANCELLED
    db.commit()
    db.refresh(sub)
    return sub