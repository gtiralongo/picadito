import uuid
from datetime import datetime

from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship

from app.database import Base


def uuid4_hex():
    return uuid.uuid4().hex


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=uuid4_hex)
    email = Column(String(200), unique=True, nullable=False, index=True)
    password_hash = Column(String(128), nullable=False)
    name = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    events = relationship("Event", back_populates="creator")


class Event(Base):
    __tablename__ = "events"

    id = Column(String, primary_key=True, default=uuid4_hex)
    title = Column(String(200), nullable=False)
    description = Column(Text, default="")
    date = Column(DateTime, nullable=False)
    location = Column(String(300), default="")
    max_participants = Column(Integer, default=0)
    creator_name = Column(String(100), nullable=False)
    creator_token = Column(String(64), nullable=False, unique=True)
    creator_id = Column(String, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String(20), default="active")
    series_id = Column(String(64), nullable=True, index=True)
    recurrence = Column(String(20), default="none")

    creator = relationship("User", back_populates="events")
    participants = relationship("Participant", back_populates="event", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="event", cascade="all, delete-orphan")


class Participant(Base):
    __tablename__ = "participants"

    id = Column(String, primary_key=True, default=uuid4_hex)
    event_id = Column(String, ForeignKey("events.id"), nullable=False)
    name = Column(String(100), nullable=False)
    phone = Column(String(30), default="")
    token = Column(String(64), nullable=False, unique=True)
    status = Column(String(20), default="confirmed")
    guests = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)

    event = relationship("Event", back_populates="participants")


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(String, primary_key=True, default=uuid4_hex)
    event_id = Column(String, ForeignKey("events.id"), nullable=False)
    message = Column(String(300), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    read = Column(Boolean, default=False)

    event = relationship("Event", back_populates="notifications")
