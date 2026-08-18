import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app

SQLALCHEMY_DATABASE_URL = "sqlite://"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}, poolclass=StaticPool)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

def test_webhook_missing_signature():
    response = client.post("/webhooks/salesforce", json={"event_type": "test"})
    assert response.status_code == 401

def test_webhook_invalid_payload():
    response = client.post("/webhooks/salesforce", data="not-json", headers={"x-salesforce-signature": "valid"})
    assert response.status_code == 400

def test_webhook_case_escalated():
    response = client.post(
        "/webhooks/salesforce", 
        json={"event_type": "case_escalated", "data": "critical issue"},
        headers={"x-salesforce-signature": "valid"}
    )
    assert response.status_code == 200
    assert response.json()["status"] == "acknowledged"
