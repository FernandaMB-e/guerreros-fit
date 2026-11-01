from datetime import date, timedelta

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models import ClassSchedule, Client, Discipline, Plan, Reminder, Subscription

# (nombre, apellido, disciplina, plan, días para vencer; negativo = ya venció; None = sin suscripción)
DEMO = [
    ("Ximena", "Santiago", "karate", "Mensual", -2),
    ("Daniel", "Gómez", "crossfit", "15 días", -1),
    ("Laura", "Pérez", "crossfit", "Mensual", -10),
    ("Jorge", "Silva", "crossfit", "15 días", 0),
    ("Andrea", "Cruz", "crossfit", "15 días", 1),
    ("Mateo", "López", "karate", "Mensual", 2),
    ("Paola", "Jiménez", "crossfit", "Mensual", 3),
    ("Sofía", "Ramírez", "karate", "Mensual", 12),
    ("Valeria", "Torres", "crossfit", "15 días", 9),
    ("Carlos", "Pérez", "crossfit", "Mensual", 18),
    ("Emiliano", "Cruz", "karate", "Mensual", 21),
    ("Renata", "Vásquez", "crossfit", "Mensual", 25),
    ("Diego", "Martínez", "karate", None, None),
]


def run() -> None:
    with SessionLocal() as db:
        plans = {p.name: p for p in db.scalars(select(Plan))}
        blocks = {
            d: list(db.scalars(
                select(ClassSchedule).where(ClassSchedule.discipline == d).order_by(ClassSchedule.start_time)
            ))
            for d in Discipline
        }
        today = date.today()
        created = 0

        for i, (first, last, disc, plan_name, days) in enumerate(DEMO, start=1):
            phone = f"52971555{i:04d}"
            if db.scalar(select(Client).where(Client.phone == phone)):
                continue

            client = Client(first_name=first, last_name=last, phone=phone)
            options = blocks[Discipline(disc)]
            client.schedules = [options[i % len(options)]]
            db.add(client)

            if days is not None:
                plan = plans[plan_name]
                end = today + timedelta(days=days)
                sub = Subscription(
                    client=client, plan=plan,
                    start_date=end - timedelta(days=plan.duration_days), end_date=end,
                )
                if days == 3:
                    sub.reminders.append(Reminder())  # ya se le avisó por WhatsApp
                db.add(sub)
            created += 1

        db.commit()
    print(f"Clientes de prueba creados: {created}")


if __name__ == "__main__":
    run()