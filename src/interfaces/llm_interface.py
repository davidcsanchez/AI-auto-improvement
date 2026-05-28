from typing import Protocol

from src.models.schemas import SupportTicketResponse


class ILLMClient(Protocol):
    async def generate_structured_ticket(
        self,
        system_prompt: str,
        user_input: str,
    ) -> SupportTicketResponse:
        ...
