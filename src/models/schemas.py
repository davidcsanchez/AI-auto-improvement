from enum import Enum
from pydantic import BaseModel, Field

class TicketIntent(str, Enum):
    bug_report = "bug_report"
    feature_request = "feature_request"
    access_issue = "access_issue"
    billing_issue = "billing_issue"
    other = "other"

class TicketUrgency(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"

class AffectedComponent(str, Enum):
    frontend = "frontend"
    backend_api = "backend_api"
    database = "database"
    hardware = "hardware"
    unknown = "unknown"

class SupportTicketResponse(BaseModel):
    intent: TicketIntent 
    urgency: TicketUrgency
    affected_component: AffectedComponent 
    requires_manager_escalation: bool 