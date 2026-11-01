from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.deps import COOKIE_NAME, get_current_user
from app.core.security import create_access_token, hash_password, verify_password
from app.db.session import get_db
from app.models import User
from app.schemas.auth import ChangePassword, LoginRequest, UserOut

router = APIRouter(prefix="/auth", tags=["Sesión"])


@router.post("/login", response_model=UserOut)
def login(data: LoginRequest, response: Response, db: Session = Depends(get_db)):
    stmt = select(User).where(func.lower(User.email) == data.email.strip().lower())
    user = db.scalar(stmt)
    # El mismo mensaje para correo o contraseña mal: no se revela cuál falló
    if user is None or not user.is_active or not verify_password(data.password, user.password_hash):
        raise HTTPException(401, "Correo o contraseña incorrectos")

    response.set_cookie(
        COOKIE_NAME,
        create_access_token(user.id),
        max_age=settings.access_token_expire_minutes * 60,
        httponly=True,   # ningún script de la página puede leerla
        samesite="lax",
        secure=settings.cookie_secure,
        path="/",
    )
    return user


@router.post("/logout")
def logout(response: Response):
    response.delete_cookie(COOKIE_NAME, path="/")
    return {"ok": True}


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user


@router.post("/change-password")
def change_password(
    data: ChangePassword,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not verify_password(data.current_password, user.password_hash):
        raise HTTPException(400, "La contraseña actual no es correcta")
    user.password_hash = hash_password(data.new_password)
    db.commit()
    return {"ok": True}