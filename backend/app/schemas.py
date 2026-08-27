import datetime
from pydantic import BaseModel, EmailStr, Field


# --- Auth ---

class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=32)
    email: EmailStr
    password: str = Field(min_length=6)


class UserLogin(BaseModel):
    username: str
    password: str


class UserOut(BaseModel):
    id: int
    username: str
    email: EmailStr
    created_at: datetime.datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


# --- Sessions ---

class SessionCreate(BaseModel):
    label: str = "Untitled session"


class ReadingCreate(BaseModel):
    score: float
    status: str
    yaw: float | None = None
    pitch: float | None = None
    eyes_closed: bool = False


class ReadingOut(BaseModel):
    id: int
    timestamp: datetime.datetime
    score: float
    status: str
    yaw: float | None
    pitch: float | None
    eyes_closed: int

    class Config:
        from_attributes = True


class SessionOut(BaseModel):
    id: int
    started_at: datetime.datetime
    ended_at: datetime.datetime | None
    average_score: float | None
    label: str

    class Config:
        from_attributes = True


class SessionDetailOut(SessionOut):
    readings: list[ReadingOut] = []


# --- Attention analysis (single frame) ---

class FrameAnalysisOut(BaseModel):
    score: float
    status: str
    yaw: float | None
    pitch: float | None
    eyes_closed: bool
    face_detected: bool
