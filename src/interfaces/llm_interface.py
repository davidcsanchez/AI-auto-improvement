from typing import Protocol

from src.models.schemas import PromptOptimization, SampleEvaluation, SupportTicketResponse


class ILLMClient(Protocol):
    async def generate_structured_ticket(
        self,
        system_prompt: str,
        user_input: str,
    ) -> SupportTicketResponse:
        ...

    async def evaluate_sample(
        self,
        current_prompt: str,
        user_input: str,
        student_output: str,
    ) -> SampleEvaluation:
        ...

    async def optimize_prompt(self, current_prompt: str, failures_context: str) -> PromptOptimization:
        ...
