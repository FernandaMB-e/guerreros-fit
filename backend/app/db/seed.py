from datetime import time

from sqlalchemy import select

from app.core.config import settings
from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models import ClassSchedule, Discipline, Plan, User


def run() -> None:
    with SessionLocal() as db:
        if not db.scalar(select(Plan).limit(1)):
            db.add_all([
                Plan(name="Mensual", duration_days=30),
                Plan(name="15 días", duration_days=15),
            ])

        if not db.scalar(select(User).limit(1)):
            db.add(User(
                email=settings.admin_email,
                full_name="Administrador",
                password_hash=hash_password(settings.admin_password),
            ))

        if not db.scalar(select(ClassSchedule).limit(1)):
            lunes_a_viernes = [0, 1, 2, 3, 4]
            db.add(ClassSchedule(
                discipline=Discipline.KARATE, start_time=time(16), end_time=time(17),
                weekdays=lunes_a_viernes,
            ))
            # Horas de ejemplo: se reemplazan con los horarios reales del gimnasio
            for hora in (6, 7, 8, 17, 18, 19):
                db.add(ClassSchedule(
                    discipline=Discipline.CROSSFIT, start_time=time(hora), end_time=time(hora + 1),
                    weekdays=lunes_a_viernes,
                ))

        db.commit()
    print("Datos iniciales listos.")


if __name__ == "__main__":
    run()