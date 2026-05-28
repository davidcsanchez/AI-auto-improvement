import json
from groq import AsyncGroq
from pydantic import ValidationError

from src.config.settings import get_settings
from src.interfaces.llm_interface import ILLMClient
from src.models.schemas import SupportTicketResponse

class GroqLLMClient(ILLMClient):
    def __init__(self) -> None:
        settings = get_settings()
        self._client = AsyncGroq(api_key=settings.API_KEY)
        self._model_name = settings.llm_model_name 

    async def generate_structured_ticket(
        self,
        system_prompt: str,
        user_input: str,
    ) -> SupportTicketResponse:
        
        schema_json = SupportTicketResponse.model_json_schema()
        full_system_prompt = (
            f"{system_prompt}\n\n"
            f"You MUST respond with valid JSON that matches exactly the following schema:\n"
            f"{json.dumps(schema_json)}"
        )

        response = await self._client.chat.completions.create(
            model=self._model_name,
            messages=[
                {"role": "system", "content": full_system_prompt},
                {"role": "user", "content": user_input},
            ],
            response_format={"type": "json_object"}, 
            temperature=0.0, 
        )

        content = response.choices[0].message.content

        if not content:
            raise ValueError("LLM response is empty")

        try:
            return SupportTicketResponse.model_validate_json(content)
        except ValidationError as e:
            raise ValueError(f"LLM response missing structured payload or invalid schema: {e}")