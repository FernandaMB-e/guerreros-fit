from collections import Counter

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models import Client, PaymentProof, ProofStatus, Subscription
from app.schemas.dashboard import (
    DashboardClient, DashboardOut, DashboardSummary, MembershipSlice,
)
from app.services.client_service import photo_url
from app.services.status import current_subscription, membership_status


def _item(client: Client, sub: Subscription, info: dict) -> DashboardClient:
    state, days_left = info["status"], info["days_left"]
    urgency = None
    if state == "por_vencer":
        urgency = "urgente" if days_left <= 1 else "proximo"  # hoy o mañana = urgente

    return DashboardClient(
        client_id=client.id,
        full_name=client.full_name,
        photo_url=photo_url(client.photo_path),
        disciplines=sorted({s.discipline for s in client.schedules}, key=lambda d: d.value),
        plan=info["plan"],
        status=state,
        end_date=info["end_date"],
        days_left=days_left,
        urgency=urgency,
        reminder_sent=any(r.status == "sent" for r in sub.reminders),
    )


def build_dashboard(db: Session, limit: int = 5) -> DashboardOut:
    clients = db.scalars(
        select(Client)
        .where(Client.is_active.is_(True))
        .options(
            selectinload(Client.subscriptions).options(
                selectinload(Subscription.plan), selectinload(Subscription.reminders)
            ),
            selectinload(Client.schedules),
        )
    ).all()

    overdue, upcoming = [], []
    plan_counts: Counter[tuple[int, str]] = Counter()
    no_subscription = 0

    for client in clients:
        info = membership_status(client.subscriptions)
        state = info["status"]
        if state == "sin_suscripcion":
            no_subscription += 1
            continue

        sub = current_subscription(client.subscriptions)
        item = _item(client, sub, info)
        if state == "vencida":
            overdue.append(item)
        else:
            plan_counts[(sub.plan.duration_days, sub.plan.name)] += 1
            if state == "por_vencer":
                upcoming.append(item)

    # Primero los que llevan más días vencidos y los que vencen antes
    overdue.sort(key=lambda i: i.days_left)
    upcoming.sort(key=lambda i: i.days_left)

    proofs_pending = db.scalar(
        select(func.count()).select_from(PaymentProof).where(PaymentProof.status == ProofStatus.PENDING)
    )

    memberships = [
        MembershipSlice(label=name, count=n)
        for (_, name), n in sorted(plan_counts.items(), reverse=True)  # el plan más largo primero
    ]
    memberships.append(MembershipSlice(label="Vencidas", count=len(overdue)))
    if no_subscription:
        memberships.append(MembershipSlice(label="Sin suscripción", count=no_subscription))

    return DashboardOut(
        summary=DashboardSummary(
            total_clients=len(clients),
            up_to_date=len(clients) - len(overdue) - no_subscription,
            pending_payment=len(overdue),
            expiring_soon=len(upcoming),
            no_subscription=no_subscription,
            proofs_pending=proofs_pending or 0,
        ),
        overdue=overdue[:limit],
        upcoming=upcoming[:limit],
        memberships=memberships,
    )