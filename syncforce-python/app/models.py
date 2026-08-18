from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from .database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)

class Lead(Base):
    __tablename__ = "leads"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    name = Column(String)
    company = Column(String)
    status = Column(String, default="NEW") # NEW, ROUTED, QUALIFIED
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class Case(Base):
    __tablename__ = "cases"
    id = Column(Integer, primary_key=True, index=True)
    subject = Column(String)
    description = Column(Text)
    status = Column(String, default="OPEN") # OPEN, ESCALATED, RESOLVED
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class Contract(Base):
    __tablename__ = "contracts"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    value = Column(Integer)
    status = Column(String, default="DRAFT") # DRAFT, PENDING_APPROVAL, APPROVED, REJECTED
    encrypted_details = Column(Text) # To demonstrate field-level encryption
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True, index=True)
    entity_type = Column(String)
    entity_id = Column(Integer)
    action = Column(String)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    user_id = Column(Integer, ForeignKey("users.id"))
