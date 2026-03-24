"""
Database configuration and session management for Care-Tracker.
Uses SQLite for simplicity and local storage.
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# Database file location - stored in /data for persistence (useful for Docker volumes later)
# Default to a local data directory relative to this file
DEFAULT_DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data"))
DATA_DIR = os.environ.get("DATA_DIR", DEFAULT_DATA_DIR)

# Ensure the directory exists
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR, exist_ok=True)

DATABASE_URL = f"sqlite:///{os.path.join(DATA_DIR, 'pet_care.db')}"

# Create engine with SQLite-specific settings
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}  # Needed for SQLite with FastAPI
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for all models
Base = declarative_base()


def get_db():
    """
    Dependency that provides a database session.
    Ensures proper cleanup after each request.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Initialize the database by creating all tables.
    Handles lightweight column migration for SQLite (adds missing columns).
    Called on application startup.
    """
    Base.metadata.create_all(bind=engine)
    _migrate_columns()


def _migrate_columns():
    """
    Add columns that may be missing from older schema versions.
    SQLAlchemy's create_all won't add columns to existing tables,
    so we check and ALTER TABLE as needed.
    """
    from sqlalchemy import text, inspect
    inspector = inspect(engine)

    migrations = [
        ("pets", "created_by", "INTEGER"),
        ("pets", "is_public", "BOOLEAN DEFAULT 1"),
    ]

    with engine.connect() as conn:
        for table, column, col_type in migrations:
            existing_cols = [c["name"] for c in inspector.get_columns(table)]
            if column not in existing_cols:
                conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}"))
                conn.commit()
