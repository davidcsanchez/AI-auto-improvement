import json

from google import genai

from src.config.settings import get_settings
from src.interfaces.llm_interface import ILLMClient
from src.models.schemas import SupportTicketResponse


class GeminiLLMClient(ILLMClient):
    def __init__(self) -> None:
        settings = get_settings()
        self._client = genai.Client(api_key=settings.API_KEY)
        self._model_name = settings.llm_model_name

    async def generate_structured_ticket(
        self,
        system_prompt: str,
        user_input: str,
    ) -> SupportTicketResponse:
        response = self._client.models.generate_content(
            model=self._model_name,
            contents=user_input,
            config={
                "system_instruction": system_prompt,
                "response_schema": SupportTicketResponse,
                "response_mime_type": "application/json",
            },
        )

        if getattr(response, "parsed", None) is not None:
            return response.parsed

        if getattr(response, "text", None):
            payload = json.loads(response.text)
            return SupportTicketResponse(**payload)

        raise ValueError("LLM response missing structured payload")
