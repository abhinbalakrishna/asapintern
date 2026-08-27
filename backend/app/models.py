import datetime

from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey
from sqlalchemy.orm import relationship

from .database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    sessions = relationship(
        "TrackingSession", back_populates="user", cascade="all, delete-orphan"
    )


class TrackingSession(Base):
    __tablename__ = "tracking_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    started_at = Column(DateTime, default=datetime.datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)
    average_score = Column(Float, nullable=True)
    label = Column(String, default="Untitled session")

    user = relationship("User", back_populates="sessions")
    readings = relationship(
        "AttentionReading", back_populates="session", cascade="all, delete-orphan"
    )


class AttentionReading(Base):
    __tablename__ = "attention_readings"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("tracking_sessions.id"), nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    score = Column(Float, nullable=False)
    status = Column(String, nullable=False)
    yaw = Column(Float, nullable=True)
    pitch = Column(Float, nullable=True)
    eyes_closed = Column(Integer, default=0)

    session = relationship("TrackingSession", back_populates="readings")
