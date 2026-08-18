import os
import logging
from typing import Dict, Any
from sqlalchemy.orm import Session
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import requests

from langchain.agents import initialize_agent, AgentType, Tool
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.language_models.fake import FakeListLLM

from . import models

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Mock External Systems ---
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type(requests.exceptions.RequestException)
)
def api_call_ticketing_system(action: str, payload: Dict[str, Any]) -> str:
    """Mock API call to external ticketing system with self-correcting retry logic."""
    logger.info(f"Calling Ticketing System API: {action} with {payload}")
    # Simulate network flakiness (would raise requests.exceptions.RequestException in real life)
    return f"Ticketing action '{action}' successful for {payload.get('case_id')}"

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=5),
)
def api_call_notification_system(user_id: int, message: str) -> str:
    """Mock API call to notification system."""
    logger.info(f"Calling Notification API for user {user_id}: {message}")
    return "Notification sent."

# --- LangChain Tools ---
def tool_escalate_case(case_info: str) -> str:
    """Tool for the agent to escalate a case."""
    # Expected format: "case_id, reason"
    try:
        case_id_str, reason = case_info.split(",", 1)
        case_id = int(case_id_str.strip())
        api_call_ticketing_system("escalate", {"case_id": case_id, "reason": reason.strip()})
        api_call_notification_system(1, f"Case {case_id} escalated: {reason}")
        return f"Successfully escalated case {case_id}"
    except Exception as e:
        return f"Error escalating case: {str(e)}"

tools = [
    Tool(
        name="EscalateCase",
        func=tool_escalate_case,
        description="Useful for escalating a case to tier 2 support. Input should be a comma separated string: 'case_id, reason'."
    ),
]

# --- LangChain Workflow Engine ---
class LangChainAgentEngine:
    def __init__(self):
        self.logger = logging.getLogger("LangChainAgentEngine")
        
        # Check for OpenAI Key, fallback to Fake LLM to ensure it runs without crashing
        if os.getenv("OPENAI_API_KEY"):
            self.llm = ChatOpenAI(temperature=0)
        else:
            self.logger.warning("No OPENAI_API_KEY found. Falling back to FakeListLLM for demonstration.")
            self.llm = FakeListLLM(responses=[
                "Action: EscalateCase\nAction Input: 1, High priority issue",
                "I have successfully escalated the case."
            ])
            
        self.agent_executor = initialize_agent(
            tools, 
            self.llm, 
            agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION, 
            verbose=True,
            handle_parsing_errors=True
        )

    def process_lead(self, lead: models.Lead, db: Session):
        """Processes a lead. (Simplified logic to demonstrate architecture)"""
        self.logger.info(f"LangChain Agent analyzing Lead {lead.id}")
        
        if "@" in lead.email and len(lead.company) > 2:
            lead.status = "QUALIFIED"
        else:
            lead.status = "ROUTED"
            
        audit = models.AuditLog(entity_type="Lead", entity_id=lead.id, action=f"LangChain Agent evaluated to {lead.status}", user_id=1)
        db.add(audit)
        db.commit()
        return lead.status

    def escalate_case(self, case_record: models.Case, db: Session):
        """Uses LangChain agent to decide and execute case escalation."""
        self.logger.info(f"Agent reviewing Case {case_record.id}")
        
        prompt = f"Review case {case_record.id}. Subject: '{case_record.subject}'. Description: '{case_record.description}'. If the issue sounds critical, escalate it."
        
        try:
            # LangChain Agent Execution
            response = self.agent_executor.invoke({"input": prompt})
            self.logger.info(f"Agent response: {response['output']}")
            
            case_record.status = "ESCALATED"
            audit = models.AuditLog(entity_type="Case", entity_id=case_record.id, action=f"Agent executed workflow. Result: {response['output']}", user_id=1)
            db.add(audit)
            db.commit()
            
        except Exception as e:
            self.logger.error(f"Agentic workflow failed: {e}")
            
        return case_record.status

agent_engine = LangChainAgentEngine()
