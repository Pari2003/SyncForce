from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from . import models, database, oauth2, encryption, agent
import logging
from datetime import timedelta

models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(title="SyncForce Enterprise CRM Integration API", version="1.0.0")

# Setup logger
logger = logging.getLogger("syncforce")

# Dependency
def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/token")
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == form_data.username).first()
    if not user or not oauth2.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password")
    access_token_expires = timedelta(minutes=oauth2.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = oauth2.create_access_token(data={"sub": user.username}, expires_delta=access_token_expires)
    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/leads/", response_model=dict)
def create_lead(name: str, email: str, company: str, background_tasks: BackgroundTasks, db: Session = Depends(get_db), current_user: models.User = Depends(oauth2.get_current_user)):
    new_lead = models.Lead(name=name, email=email, company=company)
    db.add(new_lead)
    db.commit()
    db.refresh(new_lead)
    
    # Audit log
    audit = models.AuditLog(entity_type="Lead", entity_id=new_lead.id, action="Created", user_id=current_user.id)
    db.add(audit)
    db.commit()

    # Trigger agentic workflow engine
    background_tasks.add_task(agent.agent_engine.process_lead, new_lead, db)
    
    return {"status": "success", "lead_id": new_lead.id, "message": "Lead created and queued for agentic processing"}

@app.post("/contracts/", response_model=dict)
def create_contract(title: str, value: int, sensitive_details: str, db: Session = Depends(get_db), current_user: models.User = Depends(oauth2.get_current_user)):
    encrypted = encryption.encrypt_field(sensitive_details)
    new_contract = models.Contract(title=title, value=value, encrypted_details=encrypted)
    db.add(new_contract)
    db.commit()
    db.refresh(new_contract)
    
    # Audit log
    audit = models.AuditLog(entity_type="Contract", entity_id=new_contract.id, action="Created with field-level encryption", user_id=current_user.id)
    db.add(audit)
    db.commit()
    
    return {"status": "success", "contract_id": new_contract.id}

@app.get("/contracts/{contract_id}", response_model=dict)
def get_contract(contract_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(oauth2.get_current_user)):
    contract = db.query(models.Contract).filter(models.Contract.id == contract_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    
    decrypted_details = encryption.decrypt_field(contract.encrypted_details)
    
    # Audit log
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

@app.get("/health", status_code=status.HTTP_200_OK)
def health_check():
    return {"status": "ok", "message": "SyncForce is running."}
