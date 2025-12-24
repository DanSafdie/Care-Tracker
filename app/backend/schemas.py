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

    class Config:
        from_attributes = True


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
