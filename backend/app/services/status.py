from datetime import date

from app.models import Subscription, SubscriptionStatus

# Coincide con el recordatorio de WhatsApp: 3 días antes del vencimiento
EXPIRING_DAYS = 3


def current_subscription(subscriptions: list[Subscription]) -> Subscription | None:
    """La suscripción más reciente que no esté cancelada."""
    valid = [s for s in subscriptions if s.status == SubscriptionStatus.ACTIVE]
    return max(valid, key=lambda s: s.end_date, default=None)


def membership_status(subscriptions: list[Subscription], today: date | None = None) -> dict:
    today = today or date.today()
    sub = current_subscription(subscriptions)

    if sub is None:
        return {"status": "sin_suscripcion", "plan": None, "end_date": None, "days_left": None}

    days_left = (sub.end_date - today).days
    if days_left < 0:
        state = "vencida"
    elif days_left <= EXPIRING_DAYS:
        state = "por_vencer"
    else:
        state = "activa"

    return {"status": state, "plan": sub.plan.name, "end_date": sub.end_date, "days_left": days_left}