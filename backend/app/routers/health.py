from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db import get_db

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict:
    """Liveness: the process is up and able to answer HTTP."""
    return {"status": "ok"}


@router.get("/ready")
def ready(db: Session = Depends(get_db)):
    """Readiness: only report READY when the database answers."""
    try:
        db.execute(text("SELECT 1"))
    except Exception as exc:  # noqa: BLE001 - any DB failure means not ready
        return JSONResponse(status_code=503, content={"status": "not_ready", "detail": str(exc)[:200]})
    return {"status": "ready", "database": "ok"}
