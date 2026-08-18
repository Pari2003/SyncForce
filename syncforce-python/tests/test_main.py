import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.oauth2 import get_password_hash
from app.models import User, Lead, Contract

# In-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite://"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

@pytest.fixture(scope="module")
def setup_database():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    # Create test user
    hashed_password = get_password_hash("testpassword")
    user = User(username="testuser", hashed_password=hashed_password)
    db.add(user)
    db.commit()
    yield
    Base.metadata.drop_all(bind=engine)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "message": "SyncForce is running."}

def test_login_success(setup_database):
    response = client.post(
        "/token",
        data={"username": "testuser", "password": "testpassword"},
    )
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert response.json()["token_type"] == "bearer"

def test_login_failure(setup_database):
    response = client.post(
        "/token",
        data={"username": "testuser", "password": "wrongpassword"},
    )
    assert response.status_code == 401

def test_create_lead(setup_database):
    login_response = client.post("/token", data={"username": "testuser", "password": "testpassword"})
    token = login_response.json()["access_token"]
    
    response = client.post(
        "/leads/?name=John Doe&email=john@example.com&company=TechCorp",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    assert "lead_id" in response.json()

def test_create_and_get_contract(setup_database):
    login_response = client.post("/token", data={"username": "testuser", "password": "testpassword"})
    token = login_response.json()["access_token"]
    
    # Create Contract
    response = client.post(
        "/contracts/?title=Enterprise Agreement&value=50000&sensitive_details=Secret terms",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    contract_id = response.json()["contract_id"]
    
    # Get Contract
    response2 = client.get(
        f"/contracts/{contract_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response2.status_code == 200
    data = response2.json()
    assert data["title"] == "Enterprise Agreement"
    assert data["details"] == "Secret terms" # Decrypted
    
def test_get_nonexistent_contract(setup_database):
    login_response = client.post("/token", data={"username": "testuser", "password": "testpassword"})
    token = login_response.json()["access_token"]
    
    response = client.get(
        "/contracts/9999",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 404
