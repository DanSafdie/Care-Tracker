"""
SQLAlchemy models for Care-Tracker.

Models:
- Pet: Represents a pet (dog, cat, etc.)
- CareItem: A care task associated with a pet (medication, feeding, etc.)
- TaskLog: Historical record of completed tasks

Designed for extensibility:
- Pets can have multiple care items
- Care items can have notes for timing/dependencies (human-readable, no enforcement)
- TaskLog tracks who completed what and when
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Boolean, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class Pet(Base):
    """
    A pet in the household.
    """
    __tablename__ = "pets"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    species = Column(String(50), nullable=False)  # dog, cat, bird, etc.
    notes = Column(Text, nullable=True)  # General notes about the pet
    created_at = Column(DateTime, server_default=func.now())
    is_active = Column(Boolean, default=True)  # Soft delete support
    
    # Timer fields (server-side tracking)
    timer_end_time = Column(DateTime, nullable=True)
    timer_label = Column(String(100), nullable=True)

    # Relationship to care items
    care_items = relationship("CareItem", back_populates="pet")


class User(Base):
    """
    A user/caretaker in the household.
    Used for identifying who completed tasks without full auth.
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    created_at = Column(DateTime, server_default=func.now())
    last_seen = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Notification fields
    phone_number = Column(String(20), nullable=True)
    wants_alerts = Column(Boolean, default=False)
    alert_expiry_date = Column(Date, nullable=True)


class CareItem(Base):
    """
    A care task/item for a pet.
    Examples: medication, feeding, grooming, exercise
    
    The 'notes' field can contain human-readable timing/dependency info
    (e.g., "Give on empty stomach", "30 min after breakfast")
    No rule enforcement in this version - just informational.
    """
    __tablename__ = "care_items"

    id = Column(Integer, primary_key=True, index=True)
    pet_id = Column(Integer, ForeignKey("pets.id"), nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)  # Timing/dependency notes (informational only)
    category = Column(String(50), nullable=True)  # medication, food, supplement, etc.
    display_order = Column(Integer, default=0)  # For UI ordering
    created_at = Column(DateTime, server_default=func.now())
    is_active = Column(Boolean, default=True)  # Soft delete support

    # Relationships
    pet = relationship("Pet", back_populates="care_items")
    task_logs = relationship("TaskLog", back_populates="care_item")


class TaskLog(Base):
    """
    Record of a completed (or undone) task.
    
    Each entry represents a state change:
    - action='completed': Task was marked done
    - action='undone': Task completion was reversed
    
    'care_day' is the logical day (resets at 4 AM) for tracking daily tasks.
    """
    __tablename__ = "task_logs"

    id = Column(Integer, primary_key=True, index=True)
    care_item_id = Column(Integer, ForeignKey("care_items.id"), nullable=False)
    care_day = Column(Date, nullable=False)  # The logical "day" (resets at 4 AM)
    action = Column(String(20), nullable=False)  # 'completed' or 'undone'
    completed_by = Column(String(100), nullable=True)  # Optional: who did it
    timestamp = Column(DateTime, server_default=func.now())
    notes = Column(Text, nullable=True)  # Optional notes for this specific completion

    # Relationships
    care_item = relationship("CareItem", back_populates="task_logs")
