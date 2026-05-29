import json

from google import genai

from src.config.settings import get_settings
from src.core.logger import get_logger, truncate_text
from src.core.utils import strip_markdown_json
from src.interfaces.llm_interface import ILLMClient
from src.models.schemas import PromptOptimization, SampleEvaluation, SupportTicketResponse


logger = get_logger(__name__)


class GeminiLLMClient(ILLMClient):
    def __init__(self) -> None:
        settings = get_settings()
        self._client = genai.Client(api_key=settings.API_KEY)
        self._student_model_name = settings.STUDENT_LLM_MODEL_NAME
        self._professor_model_name = settings.PROFESSOR_LLM_MODEL_NAME

    async def generate_structured_ticket(
        self,
        system_prompt: str,
        user_input: str,
    ) -> SupportTicketResponse:
        response = self._client.models.generate_content(
            model=self._student_model_name,
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
            payload = json.loads(strip_markdown_json(response.text))
            return SupportTicketResponse(**payload)

        logger.error("Gemini response empty input=%s", truncate_text(user_input))
        raise ValueError("LLM response missing structured payload")

    async def evaluate_sample(
        self,
        current_prompt: str,
        user_input: str,
        student_output: str,
    ) -> SampleEvaluation:
        prompt = (
            "Evaluate the student output against the expected JSON based on the prompt and user input. "
            "If incorrect, include the expected output."
        )

        response = self._client.models.generate_content(
            model=self._professor_model_name,
            contents=(
                f"Prompt:\n{current_prompt}\n\n"
                f"User Input:\n{user_input}\n\n"
                f"Student Output:\n{student_output}"
            ),
            config={
                "system_instruction": prompt,
                "response_schema": SampleEvaluation,
                "response_mime_type": "application/json",
            },
        )

        if getattr(response, "parsed", None) is not None:
            return response.parsed

        if getattr(response, "text", None):
            payload = json.loads(strip_markdown_json(response.text))
            return SampleEvaluation(**payload)

        logger.error("Gemini evaluation empty input=%s", truncate_text(user_input))
        raise ValueError("LLM response missing structured payload")

    async def optimize_prompt(self, current_prompt: str, failures_context: str) -> PromptOptimization:
        prompt = (
            "Improve the prompt using the failure context. "
            "Ensure the student outputs enums exactly as defined."
        )

        response = self._client.models.generate_content(
            model=self._professor_model_name,
            contents=(
                f"Current Prompt:\n{current_prompt}\n\n"
                f"Failures Context:\n{failures_context}"
            ),
            config={
                "system_instruction": prompt,
                "response_schema": PromptOptimization,
                "response_mime_type": "application/json",
            },
        )

        if getattr(response, "parsed", None) is not None:
            return response.parsed

        if getattr(response, "text", None):
            payload = json.loads(strip_markdown_json(response.text))
            return PromptOptimization(**payload)

        logger.error("Gemini optimization empty context=%s", truncate_text(failures_context))
        raise ValueError("LLM response missing structured payload")
