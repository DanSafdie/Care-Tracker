"""
Authentication utilities for Care-Tracker.

Provides:
- Bcrypt password hashing and verification via passlib
- JWT token creation and decoding via PyJWT (SEC-15: replaced python-jose)
- FastAPI dependency for extracting the current user from a JWT cookie
- Password strength validation

JWT tokens are stored in HTTP-only cookies (not localStorage) for XSS protection.
The SECRET_KEY should be set via the AUTH_SECRET_KEY environment variable in production.
"""
import os
import secrets
from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from passlib.context import CryptContext
import jwt

from database import get_db
from models import User

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Generate a random key if none is provided (fine for single-instance deploys;
# set AUTH_SECRET_KEY in .env file for sessions to survive container restarts).
# Use `or` instead of dict-default so an empty string also triggers the fallback.
SECRET_KEY = os.environ.get("AUTH_SECRET_KEY") or secrets.token_urlsafe(64)
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_DAYS = 30  # Household app – long-lived sessions are fine
COOKIE_NAME = "care_tracker_session"

# SECURE_COOKIES=true  → cookies are Secure-flagged (required for HTTPS/Caddy production)
# SECURE_COOKIES=false → cookies work over plain HTTP (dev or direct-port access)
# Default True so production is safe; override to false in docker-compose.override.yml for dev
SECURE_COOKIES = os.environ.get("SECURE_COOKIES", "true").lower() == "true"

# Minimum password length (SEC-11: raised from 6 for future health data)
MIN_PASSWORD_LENGTH = 8

# ---------------------------------------------------------------------------
# Password hashing (bcrypt via passlib)
# ---------------------------------------------------------------------------

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain_password: str) -> str:
    """Hash a plaintext password with bcrypt."""
    return pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against a bcrypt hash."""
    return pwd_context.verify(plain_password, hashed_password)


# ---------------------------------------------------------------------------
# Password validation
# ---------------------------------------------------------------------------

def validate_password_strength(password: str) -> Optional[str]:
    """
    Validate password meets minimum security requirements.
    Returns an error message string if invalid, or None if OK.
    """
    if len(password) < MIN_PASSWORD_LENGTH:
        return f"Password must be at least {MIN_PASSWORD_LENGTH} characters long."
    return None


# ---------------------------------------------------------------------------
# JWT token helpers
# ---------------------------------------------------------------------------

def create_access_token(user_id: int, username: str) -> str:
    """Create a signed JWT containing the user's id and name."""
    expire = datetime.utcnow() + timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
    payload = {
        "sub": str(user_id),
        "name": username,
        "exp": expire,
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> Optional[dict]:
    """Decode and validate a JWT. Returns the payload dict or None."""
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except (jwt.InvalidTokenError, Exception):
        return None


# ---------------------------------------------------------------------------
# FastAPI dependencies
# ---------------------------------------------------------------------------

def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    """
    Extract the current authenticated user from the JWT session cookie.
    Raises 401 if the cookie is missing/invalid or the user no longer exists.
    """
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session",
        )

    user_id = int(payload["sub"])
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User no longer exists",
        )

    return user


def get_optional_user(request: Request, db: Session = Depends(get_db)) -> Optional[User]:
    """
    Like get_current_user but returns None instead of raising if not authenticated.
    Useful for pages that work both logged-in and logged-out (e.g. login page).
    """
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        return None

    payload = decode_access_token(token)
    if payload is None:
        return None

    user_id = int(payload["sub"])
    return db.query(User).filter(User.id == user_id).first()
