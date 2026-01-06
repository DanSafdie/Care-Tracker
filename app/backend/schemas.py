"""
Pydantic schemas for API request/response validation.
Separates API contract from database models for flexibility.
"""
from pydantic import BaseModel
from datetime import datetime, date
from typing import Optional, List


# ============== Pet Schemas ==============

class PetBase(BaseModel):
    name: str
    species: str
    notes: Optional[str] = None


class PetCreate(PetBase):
    pass


class PetResponse(PetBase):
    id: int
    is_active: bool
    created_at: datetime
    timer_end_time: Optional[datetime] = None
    timer_label: Optional[str] = None
    timer_alert_sent: bool = False

    class Config:
        from_attributes = True


# ============== User Schemas ==============

class UserBase(BaseModel):
    name: str
    phone_number: Optional[str] = None
    wants_alerts: bool = False
    alert_expiry_date: Optional[date] = None


class UserCreate(UserBase):
    pass


class UserUpdate(BaseModel):
    name: Optional[str] = None
    phone_number: Optional[str] = None
    wants_alerts: Optional[bool] = None
    alert_expiry_date: Optional[date] = None


class UserResponse(UserBase):
    id: int
    created_at: datetime
    last_seen: datetime

    class Config:
        from_attributes = True


class CheckInResponse(BaseModel):
    user: UserResponse
    is_new: bool


# ============== CareItem Schemas ==============

class CareItemBase(BaseModel):
    name: str
    description: Optional[str] = None
    notes: Optional[str] = None  # Timing/dependency notes
    category: Optional[str] = None
    display_order: int = 0


class CareItemCreate(CareItemBase):
    pet_id: int


class CareItemResponse(CareItemBase):
    id: int
    pet_id: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ============== TaskLog Schemas ==============

class TaskLogCreate(BaseModel):
    care_item_id: int
    completed_by: Optional[str] = None
    notes: Optional[str] = None


class TaskLogResponse(BaseModel):
    id: int
    care_item_id: int
    care_day: date
    action: str
    completed_by: Optional[str]
    timestamp: datetime
    notes: Optional[str]

    class Config:
        from_attributes = True


# ============== Task Status (for UI) ==============

class TaskStatus(BaseModel):
    """
    Current status of a care item for today.
    Combines care item info with completion state.
    """
    care_item: CareItemResponse
    is_completed: bool
    completed_at: Optional[datetime] = None
    completed_by: Optional[str] = None


class DailyStatus(BaseModel):
    """
    Full status for a pet for the current day.
    """
    pet: PetResponse
    care_day: date
    tasks: List[TaskStatus]


# ============== History Query ==============

class HistoryQuery(BaseModel):
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    pet_id: Optional[int] = None
    care_item_id: Optional[int] = None
    limit: int = 100


class HistoryEntry(BaseModel):
    """
    A single history entry with full context.
    """
    log: TaskLogResponse
    pet_name: str
    care_item_name: str
