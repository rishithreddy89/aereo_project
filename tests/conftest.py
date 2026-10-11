import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session

from app.db.base import Base
from app.db.session import get_db
from app.main import app

TEST_DB_URL = os.getenv(
    "TEST_DB_URL",
    "mysql+pymysql://cert_user:cert_password_123@localhost:3306/certificate_test_db",
)

test_engine = create_engine(TEST_DB_URL, pool_pre_ping=True)
TestSessionLocal = sessionmaker(bind=test_engine, autocommit=False, autoflush=False)


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture()
def db(setup_test_db) -> Session:
    """
    Each test gets a fresh session. Data is committed to the DB during the test
    (so the worker's savepoints work correctly), then cleaned up after.
    We use a simple approach: truncate tables after each test.
    """
    session = TestSessionLocal()
    yield session
    session.close()
    # Clean up all test data after each test
    with test_engine.connect() as conn:
        conn.execute(__import__("sqlalchemy").text("SET FOREIGN_KEY_CHECKS=0"))
        conn.execute(__import__("sqlalchemy").text("TRUNCATE TABLE certificates"))
        conn.execute(__import__("sqlalchemy").text("TRUNCATE TABLE certificate_jobs"))
        conn.execute(__import__("sqlalchemy").text("SET FOREIGN_KEY_CHECKS=1"))
        conn.commit()


@pytest.fixture()
def client(db) -> TestClient:
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
