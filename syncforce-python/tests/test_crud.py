import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app, ENTITY_MAP
from app.oauth2 import get_password_hash
from app.models import User

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

@pytest.fixture(scope="module")
def setup_database():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    hashed_password = get_password_hash("testpassword")
    user = User(username="admin", hashed_password=hashed_password)
    db.add(user)
    db.commit()
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="module")
def token(setup_database):
    response = client.post("/token", data={"username": "admin", "password": "testpassword"})
    return response.json()["access_token"]

# Parameterized test for all entities
@pytest.mark.parametrize("entity_type", list(ENTITY_MAP.keys()))
def test_generic_crud(entity_type, token):
    headers = {"Authorization": f"Bearer {token}"}
    
    # Payload depends on required fields. For sqlite testing, we can usually pass an empty dict 
    # if there are no NOT NULL constraints without defaults, but let's pass dummy data just in case.
    # We will pass a dummy string for any typical required field.
    dummy_payload = {
        "account": {"name": "Test Account"},
        "contact": {"first_name": "John", "email": "j@c.com"},
        "lead": {"name": "L", "email": "l@c.com", "company": "C"},
        "opportunity": {"name": "Opp"},
        "case": {"subject": "Test"},
        "contract": {"title": "Doc"},
        "task": {"subject": "Task"},
        "event": {"subject": "Event"},
        "campaign": {"name": "Camp"},
        "product": {"name": "Prod", "product_code": "P1"},
        "order": {"status": "New"},
        "invoice": {"status": "Unpaid"},
        "note": {"body": "Test"},
        "attachment": {"filename": "test.pdf"}
    }
    
    payload = dummy_payload.get(entity_type, {})
    
    # 1. CREATE
    res_create = client.post(f"/api/{entity_type}", json=payload, headers=headers)
    assert res_create.status_code == 200, f"Failed to create {entity_type}: {res_create.json()}"
    entity_id = res_create.json()["id"]
    
    # 2. READ
    res_read = client.get(f"/api/{entity_type}/{entity_id}", headers=headers)
    assert res_read.status_code == 200
    
    # 3. Invalid READ
    res_invalid = client.get(f"/api/{entity_type}/99999", headers=headers)
    assert res_invalid.status_code == 404

def test_invalid_entity_type(token):
    headers = {"Authorization": f"Bearer {token}"}
    res = client.post("/api/invalid_entity", json={}, headers=headers)
    assert res.status_code == 400
    
    res2 = client.get("/api/invalid_entity/1", headers=headers)
    assert res2.status_code == 400
