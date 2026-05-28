from pydantic import BaseModel


class SupportTicketResponse(BaseModel):
    intent: str
    urgency: str
    entities: dict[str, str]
