from enum import Enum
from pydantic import BaseModel, model_validator

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


class SampleEvaluation(BaseModel):
    is_correct: bool
    expected_output: SupportTicketResponse | None = None

    @model_validator(mode="after")
    def _ensure_expected_output(self) -> "SampleEvaluation":
        if not self.is_correct and self.expected_output is None:
            raise ValueError("expected_output is required when is_correct is False")
        return self


class PromptOptimization(BaseModel):
    improved_prompt: str


class RegressionResult(BaseModel):
    passed: bool
    failure_context: str | None