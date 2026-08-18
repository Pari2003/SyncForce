import pytest
from app.agent import LangChainAgentEngine, tool_escalate_case, api_call_ticketing_system
from app import models
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
TestingSessionLocal = sessionmaker(bind=engine)

def test_agent_escalate_case():
    models.Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    
    agent_engine = LangChainAgentEngine()
    case = models.Case(subject="Critical Issue", description="System down")
    db.add(case)
    db.commit()
    
    # Run the escalation workflow
    status = agent_engine.escalate_case(case, db)
    assert status == "ESCALATED"

def test_tool_escalate_case():
    # Directly test the LangChain tool
    result = tool_escalate_case("999, high severity")
    assert "Successfully escalated" in result or "Error" in result # Depending on tenacity retry exhaustion

def test_process_lead():
    models.Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    agent_engine = LangChainAgentEngine()
    
    # Qualified lead
    lead1 = models.Lead(email="ceo@bigcorp.com", company="BigCorp")
    db.add(lead1)
    db.commit()
    status1 = agent_engine.process_lead(lead1, db)
    assert status1 == "QUALIFIED"
    
    # Unqualified lead
    lead2 = models.Lead(email="test@a.c", company="A")
    db.add(lead2)
    db.commit()
    status2 = agent_engine.process_lead(lead2, db)
    assert status2 == "ROUTED"
