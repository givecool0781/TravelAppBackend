from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional, List
import re

# ── Auth ──────────────────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("密碼至少 8 個字元")
        return v

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class UserOut(BaseModel):
    id: str
    email: str

    model_config = {"from_attributes": True}

# ── Location ──────────────────────────────────────────────────────────────────

class LocationSchema(BaseModel):
    lat: float
    lng: float
    address: str
    placeId: Optional[str] = None

# ── Event ─────────────────────────────────────────────────────────────────────

SAFE_URL_RE = re.compile(r'^https?://', re.IGNORECASE)
SAFE_PHONE_RE = re.compile(r'^[\d\s+\-(). ]{0,30}$')

class EventCreate(BaseModel):
    id: str
    time: str
    title: str
    category: str = "other"
    location: Optional[LocationSchema] = None
    notes: Optional[str] = None
    duration: Optional[str] = None
    website: Optional[str] = None
    phone: Optional[str] = None

    @field_validator("title")
    @classmethod
    def title_len(cls, v: str) -> str:
        return v.strip()[:100]

    @field_validator("website")
    @classmethod
    def safe_url(cls, v: Optional[str]) -> Optional[str]:
        if v and not SAFE_URL_RE.match(v):
            raise ValueError("網址需以 http:// 或 https:// 開頭")
        return v

    @field_validator("phone")
    @classmethod
    def safe_phone(cls, v: Optional[str]) -> Optional[str]:
        if v and not SAFE_PHONE_RE.match(v):
            raise ValueError("電話格式不正確")
        return v

class EventOut(EventCreate):
    model_config = {"from_attributes": True}

# ── Day ───────────────────────────────────────────────────────────────────────

class DayCreate(BaseModel):
    id: str
    date: str
    label: Optional[str] = None
    events: List[EventCreate] = []

class DayOut(BaseModel):
    id: str
    date: str
    label: Optional[str] = None
    events: List[EventOut] = []

    model_config = {"from_attributes": True}

# ── Trip ──────────────────────────────────────────────────────────────────────

class TripCreate(BaseModel):
    id: str
    name: str
    destination: str
    country: str
    start_date: str
    end_date: str
    emoji: str = "✈️"
    days: List[DayCreate] = []

    @field_validator("name")
    @classmethod
    def name_len(cls, v: str) -> str:
        return v.strip()[:80]

class TripUpdate(TripCreate):
    pass

class TripOut(BaseModel):
    id: str
    name: str
    destination: str
    country: str
    start_date: str
    end_date: str
    emoji: str
    days: List[DayOut] = []

    model_config = {"from_attributes": True}
