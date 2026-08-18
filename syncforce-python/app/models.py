from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text, Float
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from .database import Base

# 1. User
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)

# 2. Account
class Account(Base):
    __tablename__ = "accounts"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    industry = Column(String)
    website = Column(String)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

# 3. Contact
class Contact(Base):
    __tablename__ = "contacts"
    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("accounts.id"))
    first_name = Column(String)
    last_name = Column(String)
    email = Column(String, unique=True, index=True)
    phone = Column(String)

# 4. Lead
class Lead(Base):
    __tablename__ = "leads"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    name = Column(String)
    company = Column(String)
    status = Column(String, default="NEW") # NEW, ROUTED, QUALIFIED
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

# 5. Opportunity
class Opportunity(Base):
    __tablename__ = "opportunities"
    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("accounts.id"))
    name = Column(String)
    amount = Column(Float)
    stage = Column(String)
    close_date = Column(DateTime)

# 6. Case (Ticket)
class Case(Base):
    __tablename__ = "cases"
    id = Column(Integer, primary_key=True, index=True)
    subject = Column(String)
    description = Column(Text)
    status = Column(String, default="OPEN") # OPEN, ESCALATED, RESOLVED
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

# 7. Contract
class Contract(Base):
    __tablename__ = "contracts"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    value = Column(Integer)
    status = Column(String, default="DRAFT") # DRAFT, PENDING_APPROVAL, APPROVED, REJECTED
    encrypted_details = Column(Text) # Field-level encryption
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

# 8. Task
class Task(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True, index=True)
    subject = Column(String)
    due_date = Column(DateTime)
    status = Column(String)

# 9. Event
class Event(Base):
    __tablename__ = "events"
    id = Column(Integer, primary_key=True, index=True)
    subject = Column(String)
    start_time = Column(DateTime)
    end_time = Column(DateTime)

# 10. Campaign
class Campaign(Base):
    __tablename__ = "campaigns"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    status = Column(String)
    budget = Column(Float)

# 11. Product
class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    product_code = Column(String, unique=True)
    price = Column(Float)

# 12. Order
class Order(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("accounts.id"))
    total_amount = Column(Float)
    status = Column(String)

# 13. Invoice
class Invoice(Base):
    __tablename__ = "invoices"
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"))
    amount_due = Column(Float)
    status = Column(String)

# 14. Note
class Note(Base):
    __tablename__ = "notes"
    id = Column(Integer, primary_key=True, index=True)
    parent_id = Column(Integer) # Polymorphic parent
    parent_type = Column(String)
    body = Column(Text)

# 15. Attachment
class Attachment(Base):
    __tablename__ = "attachments"
    id = Column(Integer, primary_key=True, index=True)
    parent_id = Column(Integer)
    parent_type = Column(String)
    filename = Column(String)
    file_url = Column(String)

# 16. AuditLog
class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True, index=True)
    entity_type = Column(String)
    entity_id = Column(Integer)
    action = Column(String)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    user_id = Column(Integer, ForeignKey("users.id"))
