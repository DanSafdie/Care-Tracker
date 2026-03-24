"""
CRUD (Create, Read, Update, Delete) operations for Care-Tracker.
Database operations separated from API routes for cleaner code.
"""
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, asc
from datetime import date, datetime, timedelta
from typing import List, Optional, Dict, Any

from models import Pet, CareItem, TaskLog, User
from schemas import PetCreate, PetUpdate, CareItemCreate, CareItemUpdate, UserCreate, UserUpdate
from utils import get_care_day
from auth import hash_password, verify_password


# ============== Pet Operations ==============

def get_pets(db: Session, include_inactive: bool = False, current_user_id: int = None) -> List[Pet]:
    """
    Get pets visible to the current user.
    Visibility rules:
    - Public entities with care items: visible to everyone
    - Public entities with NO care items: only visible to creator
    - Private entities: only visible to creator
    - Legacy entities (created_by=None): visible to everyone (backward compat)
    """
    query = db.query(Pet)
    if not include_inactive:
        query = query.filter(Pet.is_active == True)
    
    all_pets = query.all()
    
    if current_user_id is None:
        return all_pets
    
    visible = []
    for pet in all_pets:
        is_owner = (pet.created_by is None or pet.created_by == current_user_id)
        
        if is_owner:
            # Owners always see their own entities
            visible.append(pet)
        elif pet.is_public:
            # Non-owners only see public entities that have care items
            has_items = any(ci.is_active for ci in pet.care_items)
            if has_items:
                visible.append(pet)
        # Private entities are invisible to non-owners (skip)
    
    return visible


def get_pet(db: Session, pet_id: int) -> Optional[Pet]:
    """Get a single pet by ID."""
    return db.query(Pet).filter(Pet.id == pet_id).first()


def create_pet(db: Session, pet: PetCreate, created_by: int = None) -> Pet:
    """Create a new care entity."""
    db_pet = Pet(
        name=pet.name,
        species=pet.species,
        notes=pet.notes,
        is_public=pet.is_public,
        created_by=created_by,
    )
    db.add(db_pet)
    db.commit()
    db.refresh(db_pet)
    return db_pet


def update_pet(db: Session, pet_id: int, pet_update: PetUpdate) -> Optional[Pet]:
    """Update a care entity's details."""
    db_pet = get_pet(db, pet_id)
    if not db_pet:
        return None
    
    update_data = pet_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_pet, key, value)
    
    db.commit()
    db.refresh(db_pet)
    return db_pet

def clear_all_expired_timers(db: Session) -> int:
    now = datetime.now()
    expired_pets = db.query(Pet).filter(Pet.timer_end_time != None, Pet.timer_end_time <= now, Pet.timer_alert_sent == True).all()
    count = len(expired_pets)
    for pet in expired_pets:
        pet.timer_end_time = None
        pet.timer_label = None
        pet.timer_alert_sent = False
    db.commit()
    return count



def set_pet_timer(db: Session, pet_id: int, hours: float, label: str) -> Optional[Pet]:
    """Set a timer for a pet."""
    db_pet = get_pet(db, pet_id)
    if not db_pet:
        return None
    
    # Use local time (not UTC) so frontend JavaScript can parse it correctly
    end_time = datetime.now() + timedelta(hours=hours)
    db_pet.timer_end_time = end_time
    db_pet.timer_label = label
    db_pet.timer_alert_sent = False
    
    db.commit()
    db.refresh(db_pet)
    return db_pet


def clear_pet_timer(db: Session, pet_id: int) -> Optional[Pet]:
    """Clear a timer for a pet."""
    db_pet = get_pet(db, pet_id)
    if not db_pet:
        return None
    
    db_pet.timer_end_time = None
    db_pet.timer_label = None
    db_pet.timer_alert_sent = False
    
    db.commit()
    db.refresh(db_pet)
    return db_pet


def get_active_timers_count(db: Session) -> int:
    """Get the count of pets with a running (not yet expired) timer."""
    now = datetime.now()
    return db.query(Pet).filter(
        Pet.timer_end_time != None,
        Pet.timer_end_time > now
    ).count()


def get_expired_timers_count(db: Session) -> int:
    """Get the count of pets with an expired timer that hasn't been cleared."""
    now = datetime.now()
    return db.query(Pet).filter(
        Pet.timer_end_time != None,
        Pet.timer_end_time <= now
    ).count()


# ============== User Operations ==============

def get_user(db: Session, user_id: int) -> Optional[User]:
    """Get a user by ID."""
    return db.query(User).filter(User.id == user_id).first()


def get_user_by_name(db: Session, name: str) -> Optional[User]:
    """Get a user by name."""
    return db.query(User).filter(User.name == name).first()


def get_or_create_user(
    db: Session, 
    name: str, 
    phone_number: str = None, 
    wants_alerts: bool = False,
    alert_expiry_date: date = None
) -> tuple[User, bool]:
    """
    Get an existing user or create a new one.
    When auto-creating (e.g. from task completion), a random placeholder password
    is assigned; the user should sign up properly or be given the generated creds.
    """
    import secrets as _secrets

    db_user = get_user_by_name(db, name)
    is_new = False
    if not db_user:
        placeholder_pw = _secrets.token_urlsafe(16)
        db_user = User(
            name=name,
            password_hash=hash_password(placeholder_pw),
            phone_number=phone_number,
            wants_alerts=wants_alerts,
            alert_expiry_date=alert_expiry_date
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        is_new = True
    else:
        # Update last_seen
        db_user.last_seen = datetime.now()
        # Only update phone/alerts if they were provided in this call (onboarding flow)
        if phone_number is not None:
            db_user.phone_number = phone_number
        if wants_alerts:
            db_user.wants_alerts = wants_alerts
        if alert_expiry_date is not None:
            db_user.alert_expiry_date = alert_expiry_date
            
        db.commit()
        db.refresh(db_user)
    return db_user, is_new


def create_user_with_password(db: Session, name: str, password: str) -> User:
    """Create a new user with a hashed password (signup flow)."""
    db_user = User(
        name=name,
        password_hash=hash_password(password),
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def authenticate_user(db: Session, name: str, password: str) -> Optional[User]:
    """Verify credentials. Returns the User if valid, None otherwise."""
    db_user = get_user_by_name(db, name)
    if not db_user:
        return None
    if not verify_password(password, db_user.password_hash):
        return None
    # Bump last_seen on successful login
    db_user.last_seen = datetime.now()
    db.commit()
    db.refresh(db_user)
    return db_user


def change_user_password(db: Session, user_id: int, new_password: str) -> User:
    """Set a new hashed password for the given user."""
    db_user = get_user(db, user_id)
    if not db_user:
        return None
    db_user.password_hash = hash_password(new_password)
    db.commit()
    db.refresh(db_user)
    return db_user


def update_user(db: Session, user_id: int, user_update: UserUpdate) -> Optional[User]:
    """Update a user's details."""
    db_user = get_user(db, user_id)
    if not db_user:
        return None
    
    update_data = user_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_user, key, value)
    
    db.commit()
    db.refresh(db_user)
    return db_user


def search_users(db: Session, query: str, limit: int = 5) -> List[User]:
    """Search for users by name prefix."""
    if not query:
        return []
    return db.query(User).filter(
        User.name.ilike(f"{query}%")
    ).order_by(User.name).limit(limit).all()


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


def update_care_item(db: Session, care_item_id: int, item_update: CareItemUpdate) -> Optional[CareItem]:
    """Update a care item's details."""
    db_item = get_care_item(db, care_item_id)
    if not db_item:
        return None
    
    update_data = item_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_item, key, value)
    
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
    ).order_by(desc(TaskLog.timestamp), desc(TaskLog.id)).first()
    
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
    ).order_by(desc(TaskLog.timestamp), desc(TaskLog.id)).first()


def complete_task(db: Session, care_item_id: int, completed_by: str = None, notes: str = None) -> TaskLog:
    """
    Mark a task as completed for today's care day.
    Creates a new log entry with action='completed'.
    """
    care_day = get_care_day()
    
    # If a name is provided, ensure the user exists in the registry
    if completed_by:
        get_or_create_user(db, completed_by)
    
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
    
    return query.order_by(desc(TaskLog.timestamp), desc(TaskLog.id)).limit(limit).all()


def get_grid_history(db: Session, page: int = 1, page_size: int = 30) -> Dict[str, Any]:
    """
    Get history in a grid-friendly format for the UI.
    Rows: Dates (most recent first)
    Columns: Active Care Items
    
    Args:
        db: Database session
        page: Page number (1-indexed)
        page_size: Number of days per page
        
    Returns:
        Dict containing columns (items), rows (dates and statuses), and pagination info
    """
    today = get_care_day()
    start_offset = (page - 1) * page_size
    
    # Generate the dates for this page
    dates = []
    for i in range(page_size):
        target_date = today - timedelta(days=start_offset + i)
        dates.append(target_date)
        
    # Get all active care items to serve as columns, ordered by pet then display_order
    pets = get_pets(db)
    columns = []
    for pet in pets:
        items = get_care_items(db, pet_id=pet.id)
        for item in items:
            columns.append({
                "id": item.id,
                "name": item.name,
                "pet_name": pet.name,
                "created_at": item.created_at
            })
            
    if not columns:
        return {"columns": [], "rows": [], "page": page, "has_next": False}

    # Fetch all logs for the date range and the items we care about
    min_date = dates[-1]
    max_date = dates[0]
    
    logs = db.query(TaskLog).filter(
        and_(
            TaskLog.care_day >= min_date,
            TaskLog.care_day <= max_date
        )
    ).order_by(asc(TaskLog.timestamp), asc(TaskLog.id)).all()
    
    # Organize logs by (date, care_item_id) - last status wins
    status_map = {}
    for log in logs:
        status_map[(log.care_day, log.care_item_id)] = log.action == "completed"

    # Build the rows
    rows = []
    for d in dates:
        row_items = {}
        for col in columns:
            is_completed = status_map.get((d, col["id"]), False)
            
            # Simplified check: if date is before item was created, it's not applicable
            # We use get_care_day on created_at for consistency
            item_start_date = get_care_day(col["created_at"])
            
            if d < item_start_date:
                status = "n/a"
            elif is_completed:
                status = "given"
            else:
                status = "missed"
                
            row_items[col["id"]] = status
            
        rows.append({
            "date": d,
            "column_values": row_items
        })
        
    # Check if there's history older than our current range for 'has_next'
    oldest_log = db.query(TaskLog).order_by(asc(TaskLog.care_day)).first()
    has_next = False
    if oldest_log and oldest_log.care_day < min_date:
        has_next = True
    elif not oldest_log:
        # If no logs, maybe check pet creation dates? 
        # For now, let's just say has_next is true if the next page of dates
        # would still be after the oldest pet's creation date.
        first_pet = db.query(Pet).order_by(asc(Pet.created_at)).first()
        if first_pet and get_care_day(first_pet.created_at) < min_date:
            has_next = True

    return {
        "columns": columns,
        "rows": rows,
        "page": page,
        "page_size": page_size,
        "has_next": has_next,
        "has_prev": page > 1
    }


def get_daily_summary(db: Session, care_day: date = None, current_user_id: int = None) -> dict:
    """
    Get a summary of all tasks for a given day, filtered by visibility.
    Returns dict with pet info and task statuses.
    """
    if care_day is None:
        care_day = get_care_day()
    
    pets = get_pets(db, current_user_id=current_user_id)
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
