"""
CRUD (Create, Read, Update, Delete) operations for Pet Care Tracker.
Database operations separated from API routes for cleaner code.
"""
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
from datetime import date, datetime
from typing import List, Optional

from models import Pet, CareItem, TaskLog
from schemas import PetCreate, CareItemCreate
from utils import get_care_day


# ============== Pet Operations ==============

def get_pets(db: Session, include_inactive: bool = False) -> List[Pet]:
    """Get all pets, optionally including inactive ones."""
    query = db.query(Pet)
    if not include_inactive:
        query = query.filter(Pet.is_active == True)
    return query.all()


def get_pet(db: Session, pet_id: int) -> Optional[Pet]:
    """Get a single pet by ID."""
    return db.query(Pet).filter(Pet.id == pet_id).first()


def create_pet(db: Session, pet: PetCreate) -> Pet:
    """Create a new pet."""
    db_pet = Pet(**pet.model_dump())
    db.add(db_pet)
    db.commit()
    db.refresh(db_pet)
    return db_pet


# ============== CareItem Operations ==============

def get_care_items(db: Session, pet_id: int = None, include_inactive: bool = False) -> List[CareItem]:
    """Get care items, optionally filtered by pet."""
    query = db.query(CareItem)
    if pet_id:
        query = query.filter(CareItem.pet_id == pet_id)
    if not include_inactive:
        query = query.filter(CareItem.is_active == True)
    return query.order_by(CareItem.display_order, CareItem.id).all()


def get_care_item(db: Session, care_item_id: int) -> Optional[CareItem]:
    """Get a single care item by ID."""
    return db.query(CareItem).filter(CareItem.id == care_item_id).first()


def create_care_item(db: Session, care_item: CareItemCreate) -> CareItem:
    """Create a new care item."""
    db_item = CareItem(**care_item.model_dump())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item


# ============== TaskLog Operations ==============

def get_task_status_for_day(db: Session, care_item_id: int, care_day: date) -> bool:
    """
    Determine if a task is completed for a given care day.
    
    Looks at the most recent action for that care_item on that day.
    Returns True if the last action was 'completed', False otherwise.
    """
    last_log = db.query(TaskLog).filter(
        and_(
            TaskLog.care_item_id == care_item_id,
            TaskLog.care_day == care_day
        )
    ).order_by(desc(TaskLog.timestamp)).first()
    
    if last_log is None:
        return False
    
    return last_log.action == "completed"


def get_last_completion_for_day(db: Session, care_item_id: int, care_day: date) -> Optional[TaskLog]:
    """
    Get the last 'completed' log entry for a care item on a given day.
    Returns None if not completed.
    """
    # First check if currently completed
    if not get_task_status_for_day(db, care_item_id, care_day):
        return None
    
    # Get the last 'completed' action
    return db.query(TaskLog).filter(
        and_(
            TaskLog.care_item_id == care_item_id,
            TaskLog.care_day == care_day,
            TaskLog.action == "completed"
        )
    ).order_by(desc(TaskLog.timestamp)).first()


def complete_task(db: Session, care_item_id: int, completed_by: str = None, notes: str = None) -> TaskLog:
    """
    Mark a task as completed for today's care day.
    Creates a new log entry with action='completed'.
    """
    care_day = get_care_day()
    
    log = TaskLog(
        care_item_id=care_item_id,
        care_day=care_day,
        action="completed",
        completed_by=completed_by,
        notes=notes
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


def undo_task(db: Session, care_item_id: int, completed_by: str = None, notes: str = None) -> TaskLog:
    """
    Undo a completed task for today's care day.
    Creates a new log entry with action='undone'.
    """
    care_day = get_care_day()
    
    log = TaskLog(
        care_item_id=care_item_id,
        care_day=care_day,
        action="undone",
        completed_by=completed_by,
        notes=notes
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


def get_history(
    db: Session,
    start_date: date = None,
    end_date: date = None,
    pet_id: int = None,
    care_item_id: int = None,
    limit: int = 100
) -> List[TaskLog]:
    """
    Get task history with optional filters.
    Returns most recent entries first.
    """
    query = db.query(TaskLog).join(CareItem)
    
    if start_date:
        query = query.filter(TaskLog.care_day >= start_date)
    if end_date:
        query = query.filter(TaskLog.care_day <= end_date)
    if pet_id:
        query = query.filter(CareItem.pet_id == pet_id)
    if care_item_id:
        query = query.filter(TaskLog.care_item_id == care_item_id)
    
    return query.order_by(desc(TaskLog.timestamp)).limit(limit).all()


def get_daily_summary(db: Session, care_day: date = None) -> dict:
    """
    Get a summary of all tasks for a given day.
    Returns dict with pet info and task statuses.
    """
    if care_day is None:
        care_day = get_care_day()
    
    pets = get_pets(db)
    result = []
    
    for pet in pets:
        care_items = get_care_items(db, pet_id=pet.id)
        tasks = []
        
        for item in care_items:
            is_completed = get_task_status_for_day(db, item.id, care_day)
            last_completion = get_last_completion_for_day(db, item.id, care_day) if is_completed else None
            
            tasks.append({
                "care_item": item,
                "is_completed": is_completed,
                "completed_at": last_completion.timestamp if last_completion else None,
                "completed_by": last_completion.completed_by if last_completion else None
            })
        
        result.append({
            "pet": pet,
            "care_day": care_day,
            "tasks": tasks
        })
    
    return result
