import sys
import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

# Add backend to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "app", "backend")))

from database import Base, get_db
from main import app
from auth import hash_password, create_access_token, COOKIE_NAME

# Create in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Default test password (used by helper fixtures)
TEST_PASSWORD = "testpass123"

@pytest.fixture(scope="function")
def db_session():
    """
    Creates a fresh database for each test function.
    """
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(db_session):
    """
    FastAPI TestClient with overridden database dependency.
    Not authenticated — good for testing login/signup flows and public endpoints.
    """
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
            
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def auth_client(db_session):
    """
    FastAPI TestClient pre-authenticated as a test user.
    Creates a user in the database and attaches a valid JWT session cookie.
    Returns (client, user) so tests can access the user object.
    """
    from models import User

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    # Create a test user with a known password
    user = User(
        name="Test User",
        password_hash=hash_password(TEST_PASSWORD),
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    # Build a TestClient with the session cookie pre-set
    token = create_access_token(user.id, user.name)
    c = TestClient(app, cookies={COOKIE_NAME: token})

    yield c, user

    app.dependency_overrides.clear()
