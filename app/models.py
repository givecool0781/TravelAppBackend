from sqlalchemy import Column, String, Float, Integer, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base

class User(Base):
    __tablename__ = "users"

    id       = Column(String, primary_key=True)
    email    = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    trips = relationship("Trip", back_populates="owner", cascade="all, delete-orphan")


class Trip(Base):
    __tablename__ = "trips"

    id          = Column(String, primary_key=True)
    user_id     = Column(String, ForeignKey("users.id"), nullable=False)
    name        = Column(String(80), nullable=False)
    destination = Column(String(60), nullable=False)
    country     = Column(String(60), nullable=False)
    start_date  = Column(String(10), nullable=False)
    end_date    = Column(String(10), nullable=False)
    emoji       = Column(String(10), default="✈️")
    created_at  = Column(DateTime, server_default=func.now())
    updated_at  = Column(DateTime, server_default=func.now(), onupdate=func.now())

    owner = relationship("User", back_populates="trips")
    days  = relationship("TripDay", back_populates="trip", cascade="all, delete-orphan", order_by="TripDay.date")


class TripDay(Base):
    __tablename__ = "trip_days"

    id      = Column(String, primary_key=True)
    trip_id = Column(String, ForeignKey("trips.id"), nullable=False)
    date    = Column(String(10), nullable=False)
    label   = Column(String(60), nullable=True)

    trip   = relationship("Trip", back_populates="days")
    events = relationship("TripEvent", back_populates="day", cascade="all, delete-orphan", order_by="TripEvent.time")


class TripEvent(Base):
    __tablename__ = "trip_events"

    id       = Column(String, primary_key=True)
    day_id   = Column(String, ForeignKey("trip_days.id"), nullable=False)
    time     = Column(String(5), nullable=False)
    title    = Column(String(100), nullable=False)
    category = Column(String(20), nullable=False, default="other")
    lat      = Column(Float, nullable=True)
    lng      = Column(Float, nullable=True)
    address  = Column(String(200), nullable=True)
    place_id = Column(String(200), nullable=True)
    notes    = Column(Text, nullable=True)
    duration = Column(String(40), nullable=True)
    website  = Column(String(300), nullable=True)
    phone    = Column(String(30), nullable=True)

    day = relationship("TripDay", back_populates="events")
