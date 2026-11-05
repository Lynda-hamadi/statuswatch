from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class TargetCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    url: HttpUrl
    interval_seconds: int = Field(default=60, ge=30, le=3600)


class TargetOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    url: str
    interval_seconds: int
    created_at: datetime


class CheckOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    target_id: int
    checked_at: datetime
    status_code: int | None
    response_ms: int | None
    is_up: bool
    error: str | None