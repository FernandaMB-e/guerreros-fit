from sqlalchemy import select

from app.core.config import settings
from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models import User


def run() -> None:
    with SessionLocal() as db:
        user = db.scalar(select(User).order_by(User.id).limit(1))
        if user is None:
            print("No hay administrador. Corre primero: python -m app.db.seed")
            return
        user.email = settings.admin_email
        user.password_hash = hash_password(settings.admin_password)
        user.is_active = True
        db.commit()
        print(f"Administrador actualizado: {user.email}")


if __name__ == "__main__":
    run()
