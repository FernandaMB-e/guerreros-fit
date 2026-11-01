from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.dashboard import DashboardOut
from app.services.dashboard_service import build_dashboard

router = APIRouter(prefix="/dashboard", tags=["Inicio"])


@router.get("", response_model=DashboardOut)
def get_dashboard(limit: int = Query(5, ge=1, le=50), db: Session = Depends(get_db)):
    """Todo lo que muestra la pantalla de Inicio, en una sola llamada."""
    return build_dashboard(db, limit)