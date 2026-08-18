from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import Any, Dict
from . import models, database, oauth2, encryption, agent
import logging
from datetime import timedelta
import json

models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(title="SyncForce Enterprise CRM Integration API", version="1.0.0")

logger = logging.getLogger("syncforce")

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Map string entity types to actual SQLAlchemy models
ENTITY_MAP = {
    "account": models.Account,
    "contact": models.Contact,
    "lead": models.Lead,
    "opportunity": models.Opportunity,
    "case": models.Case,
    "contract": models.Contract,
    "task": models.Task,
    "event": models.Event,
    "campaign": models.Campaign,
    "product": models.Product,
    "order": models.Order,
    "invoice": models.Invoice,
    "note": models.Note,
    "attachment": models.Attachment
}

@app.post("/token")
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == form_data.username).first()
    if not user or not oauth2.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password")
    access_token_expires = timedelta(minutes=oauth2.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = oauth2.create_access_token(data={"sub": user.username}, expires_delta=access_token_expires)
    return {"access_token": access_token, "token_type": "bearer"}

# --- Specific Endpoints with Logic ---
@app.post("/leads/")
def create_lead(payload: dict, background_tasks: BackgroundTasks, db: Session = Depends(get_db), current_user: models.User = Depends(oauth2.get_current_user)):
    new_lead = models.Lead(**payload)
    db.add(new_lead)
    db.commit()
    db.refresh(new_lead)
    
    # Audit log
    audit = models.AuditLog(entity_type="Lead", entity_id=new_lead.id, action="Created", user_id=current_user.id)
    db.add(audit)
    db.commit()

    # Trigger LangChain workflow engine
    background_tasks.add_task(agent.agent_engine.process_lead, new_lead, db)
    
    return {"status": "success", "id": new_lead.id, "message": "Lead created and queued for agentic processing"}

@app.post("/contracts/")
def create_contract(payload: dict, db: Session = Depends(get_db), current_user: models.User = Depends(oauth2.get_current_user)):
    if 'sensitive_details' in payload:
        payload['encrypted_details'] = encryption.encrypt_field(payload.pop('sensitive_details'))
    
    new_contract = models.Contract(**payload)
    db.add(new_contract)
    db.commit()
    db.refresh(new_contract)
    
    audit = models.AuditLog(entity_type="Contract", entity_id=new_contract.id, action="Created with field-level encryption", user_id=current_user.id)
    db.add(audit)
    db.commit()
    
    return {"status": "success", "id": new_contract.id}

@app.get("/contracts/{contract_id}")
def get_contract(contract_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(oauth2.get_current_user)):
    contract = db.query(models.Contract).filter(models.Contract.id == contract_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    
    decrypted_details = encryption.decrypt_field(contract.encrypted_details)
    
    audit = models.AuditLog(entity_type="Contract", entity_id=contract.id, action="Viewed decrypted details", user_id=current_user.id)
    db.add(audit)
    db.commit()
    
    return {
        "id": contract.id,
        "title": contract.title,
        "value": contract.value,
        "status": contract.status,
        "details": decrypted_details
    }

# --- Generic CRUD for 15+ Entities ---
@app.post("/api/{entity_type}")
def create_entity(entity_type: str, payload: dict, db: Session = Depends(get_db), current_user: models.User = Depends(oauth2.get_current_user)):
    if entity_type not in ENTITY_MAP:
        raise HTTPException(status_code=400, detail=f"Entity {entity_type} not supported")
    
    model_class = ENTITY_MAP[entity_type]
    try:
        new_entity = model_class(**payload)
        db.add(new_entity)
        db.commit()
        db.refresh(new_entity)
        return {"status": "success", "id": new_entity.id}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/{entity_type}/{entity_id}")
def get_entity(entity_type: str, entity_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(oauth2.get_current_user)):
    if entity_type not in ENTITY_MAP:
        raise HTTPException(status_code=400, detail=f"Entity {entity_type} not supported")
    
    entity = db.query(ENTITY_MAP[entity_type]).filter(ENTITY_MAP[entity_type].id == entity_id).first()
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")
        
    # Convert SQLAlchemy object to dict for response
    return {c.name: getattr(entity, c.name) for c in entity.__table__.columns}

# --- Webhook Pipeline ---
@app.post("/webhooks/salesforce")
async def receive_webhook(request: Request, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Receives event payloads from external CRM systems."""
    # Basic simulated security check
    signature = request.headers.get("x-salesforce-signature")
    if not signature:
        raise HTTPException(status_code=401, detail="Missing signature")
        
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    event_type = payload.get("event_type")
    
    # Audit log the webhook receipt
    audit = models.AuditLog(entity_type="Webhook", entity_id=0, action=f"Received {event_type}", user_id=1)
    db.add(audit)
    db.commit()

    if event_type == "case_escalated":
        # Create a mock case to pass to the agent
        case = models.Case(subject="Webhook Escalate", description=str(payload))
        db.add(case)
        db.commit()
        background_tasks.add_task(agent.agent_engine.escalate_case, case, db)
        
    return {"status": "acknowledged", "event": event_type}

@app.get("/health", status_code=status.HTTP_200_OK)
def health_check():
    return {"status": "ok", "message": "SyncForce is running."}
