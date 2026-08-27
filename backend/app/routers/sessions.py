import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from .. import models, schemas
from ..auth import get_current_user
from ..database import get_db
from .attention import clear_calibration

router = APIRouter(prefix="/sessions", tags=["sessions"])


def _get_owned_session(db: Session, session_id: int, user: models.User) -> models.TrackingSession:
    session = (
        db.query(models.TrackingSession)
        .filter(models.TrackingSession.id == session_id, models.TrackingSession.user_id == user.id)
        .first()
    )
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.post("", response_model=schemas.SessionOut, status_code=201)
def start_session(
    payload: schemas.SessionCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    session = models.TrackingSession(user_id=current_user.id, label=payload.label)
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


@router.post("/{session_id}/readings", response_model=schemas.ReadingOut, status_code=201)
def add_reading(
    session_id: int,
    payload: schemas.ReadingCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    session = _get_owned_session(db, session_id, current_user)
    if session.ended_at is not None:
        raise HTTPException(status_code=400, detail="Session already ended")

    reading = models.AttentionReading(
        session_id=session.id,
        score=payload.score,
        status=payload.status,
        yaw=payload.yaw,
        pitch=payload.pitch,
        eyes_closed=int(payload.eyes_closed),
    )
    db.add(reading)
    db.commit()
    db.refresh(reading)
    return reading


@router.post("/{session_id}/end", response_model=schemas.SessionDetailOut)
def end_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    session = _get_owned_session(db, session_id, current_user)
    readings = (
        db.query(models.AttentionReading)
        .filter(models.AttentionReading.session_id == session.id)
        .all()
    )
    session.ended_at = datetime.datetime.utcnow()
    session.average_score = (
        sum(r.score for r in readings) / len(readings) if readings else None
    )
    db.commit()
    db.refresh(session)
    clear_calibration(session.id)
    return session


@router.get("", response_model=list[schemas.SessionOut])
def list_sessions(
    db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)
):
    return (
        db.query(models.TrackingSession)
        .filter(models.TrackingSession.user_id == current_user.id)
        .order_by(models.TrackingSession.started_at.desc())
        .all()
    )


@router.get("/{session_id}", response_model=schemas.SessionDetailOut)
def get_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    session = (
        db.query(models.TrackingSession)
        .options(joinedload(models.TrackingSession.readings))
        .filter(models.TrackingSession.id == session_id, models.TrackingSession.user_id == current_user.id)
        .first()
    )
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session
