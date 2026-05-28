from src.core.exceptions import ActivePromptNotFoundError
from src.interfaces.llm_interface import ILLMClient
from src.interfaces.storage_interface import ITicketStorage
from src.models.schemas import SupportTicketResponse
from src.models.ticket_sample import TicketSample


class InferenceService:
    def __init__(self, storage: ITicketStorage, llm_client: ILLMClient) -> None:
        self._storage = storage
        self._llm_client = llm_client

    async def process_user_message(self, message: str) -> SupportTicketResponse:
        active_prompt = await self._storage.get_active_prompt()
        if active_prompt is None:
            raise ActivePromptNotFoundError("Active prompt not found")

        response = await self._llm_client.generate_structured_ticket(
            system_prompt=active_prompt.content,
            user_input=message,
        )

        sample = TicketSample(
            input_text=message,
            output_json=response.model_dump_json(),
            is_correct=None,
            for_evaluation=False,
            prompt_version_id=active_prompt.id,
        )

        await self._storage.save_sample(sample)
        return response
