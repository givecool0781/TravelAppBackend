from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from .. import models, schemas
from ..auth import get_current_user
from ..database import get_db

router = APIRouter(prefix="/trips", tags=["trips"])

def _build_trip(body: schemas.TripCreate, user_id: str) -> models.Trip:
    trip = models.Trip(
        id=body.id,
        user_id=user_id,
        name=body.name,
        destination=body.destination,
        country=body.country,
        start_date=body.start_date,
        end_date=body.end_date,
        emoji=body.emoji,
    )
    for d in body.days:
        day = models.TripDay(id=d.id, trip_id=trip.id, date=d.date, label=d.label)
        for e in d.events:
            loc = e.location
            day.events.append(models.TripEvent(
                id=e.id, day_id=day.id,
                time=e.time, title=e.title, category=e.category,
                lat=loc.lat if loc else None,
                lng=loc.lng if loc else None,
                address=loc.address if loc else None,
                place_id=loc.placeId if loc else None,
                notes=e.notes, duration=e.duration,
                website=e.website, phone=e.phone,
            ))
        trip.days.append(day)
    return trip

def _trip_to_out(trip: models.Trip) -> schemas.TripOut:
    return schemas.TripOut(
        id=trip.id,
        name=trip.name,
        destination=trip.destination,
        country=trip.country,
        start_date=trip.start_date,
        end_date=trip.end_date,
        emoji=trip.emoji,
        days=[
            schemas.DayOut(
                id=d.id, date=d.date, label=d.label,
                events=[
                    schemas.EventOut(
                        id=e.id, time=e.time, title=e.title, category=e.category,
                        location=schemas.LocationSchema(lat=e.lat, lng=e.lng, address=e.address, placeId=e.place_id)
                            if e.lat is not None else None,
                        notes=e.notes, duration=e.duration,
                        website=e.website, phone=e.phone,
                    ) for e in d.events
                ]
            ) for d in trip.days
        ]
    )

# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("", response_model=List[schemas.TripOut])
def list_trips(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return [_trip_to_out(t) for t in current_user.trips]

@router.post("", response_model=schemas.TripOut, status_code=201)
def create_trip(
    body: schemas.TripCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if db.get(models.Trip, body.id):
        raise HTTPException(400, "Trip ID 已存在")
    trip = _build_trip(body, current_user.id)
    db.add(trip)
    db.commit()
    db.refresh(trip)
    return _trip_to_out(trip)

@router.get("/{trip_id}", response_model=schemas.TripOut)
def get_trip(
    trip_id: str,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    trip = db.get(models.Trip, trip_id)
    if not trip or trip.user_id != current_user.id:
        raise HTTPException(404, "找不到旅行")
    return _trip_to_out(trip)

@router.put("/{trip_id}", response_model=schemas.TripOut)
def update_trip(
    trip_id: str,
    body: schemas.TripUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    trip = db.get(models.Trip, trip_id)
    if not trip or trip.user_id != current_user.id:
        raise HTTPException(404, "找不到旅行")

    # Update fields
    trip.name = body.name
    trip.destination = body.destination
    trip.country = body.country
    trip.start_date = body.start_date
    trip.end_date = body.end_date
    trip.emoji = body.emoji

    # Replace all days/events
    for day in trip.days:
        db.delete(day)
    db.flush()

    for d in body.days:
        day = models.TripDay(id=d.id, trip_id=trip.id, date=d.date, label=d.label)
        for e in d.events:
            loc = e.location
            day.events.append(models.TripEvent(
                id=e.id, day_id=day.id,
                time=e.time, title=e.title, category=e.category,
                lat=loc.lat if loc else None,
                lng=loc.lng if loc else None,
                address=loc.address if loc else None,
                place_id=loc.placeId if loc else None,
                notes=e.notes, duration=e.duration,
                website=e.website, phone=e.phone,
            ))
        trip.days.append(day)

    db.commit()
    db.refresh(trip)
    return _trip_to_out(trip)

@router.delete("/{trip_id}", status_code=204)
def delete_trip(
    trip_id: str,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    trip = db.get(models.Trip, trip_id)
    if not trip or trip.user_id != current_user.id:
        raise HTTPException(404, "找不到旅行")
    db.delete(trip)
    db.commit()
