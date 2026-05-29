import json

from groq import AsyncGroq
from pydantic import ValidationError

from src.config.settings import get_settings
from src.core.exceptions import LLMResponseValidationError
from src.core.logger import get_logger, truncate_text
from src.core.utils import strip_markdown_json
from src.interfaces.llm_interface import ILLMClient
from src.models.schemas import PromptOptimization, SampleEvaluation, SupportTicketResponse


logger = get_logger(__name__)

class GroqLLMClient(ILLMClient):
    def __init__(self) -> None:
        settings = get_settings()
        self._client = AsyncGroq(api_key=settings.API_KEY)
        self._student_model_name = settings.STUDENT_LLM_MODEL_NAME
        self._professor_model_name = settings.PROFESSOR_LLM_MODEL_NAME
        self._optimize_prompt = settings.OPTIMIZE_PROMPT

    async def generate_structured_ticket(
        self,
        system_prompt: str,
        user_input: str,
    ) -> SupportTicketResponse:
        schema_json = SupportTicketResponse.model_json_schema()
        full_system_prompt = (
            f"{system_prompt}\n\n"
            f"You MUST respond with valid JSON that matches exactly the following schema:\n"
            f"{json.dumps(schema_json)}\n\n"
            "You MUST output ONLY a valid JSON object with the exact keys: "
            "'intent', 'urgency', 'affected_component', 'requires_manager_escalation'. "
            "DO NOT nest the response. DO NOT return error messages as JSON keys."
        )

        response = await self._client.chat.completions.create(
            model=self._student_model_name,
            messages=[
                {"role": "system", "content": full_system_prompt},
                {"role": "user", "content": user_input},
            ],
            response_format={"type": "json_object"},
            temperature=0.0,
        )

        content = response.choices[0].message.content

        if not content:
            logger.error("Groq response empty input=%s", truncate_text(user_input))
            raise ValueError("LLM response is empty")

        clean_content = strip_markdown_json(content)

        try:
            return SupportTicketResponse.model_validate_json(clean_content)
        except ValidationError as exc:
            logger.error("LLM Schema Hallucination")
            raise ValueError(f"LLM response missing structured payload or invalid schema: {exc}") from exc

    async def evaluate_sample(
        self,
        current_prompt: str,
        user_input: str,
        student_output: str,
    ) -> SampleEvaluation:
        schema_json = SampleEvaluation.model_json_schema()
        system_prompt = (
            "You are an evaluator. Compare the student output to the expected JSON based on the prompt and user input. "
            "If incorrect, provide the expected output using the schema. "
            "You MUST output ONLY a valid JSON object with keys: 'is_correct' (boolean) and "
            "'expected_output' (object, ONLY if is_correct is false). If is_correct is False, "
            "you MUST include the expected_output."
        )
        messages = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": (
                    f"Prompt:\n{current_prompt}\n\n"
                    f"User Input:\n{user_input}\n\n"
                    f"Student Output:\n{student_output}\n\n"
                    f"Return JSON that matches:\n{json.dumps(schema_json)}"
                ),
            },
        ]

        response = await self._client.chat.completions.create(
            model=self._professor_model_name,
            messages=messages,
            response_format={"type": "json_object"},
            temperature=0.0,
        )

        content = response.choices[0].message.content
        if not content:
            logger.error("Groq evaluation empty input=%s", truncate_text(user_input))
            raise ValueError("LLM response is empty")

        clean_content = strip_markdown_json(content)

        try:
            return SampleEvaluation.model_validate_json(clean_content)
        except ValidationError as exc:
            logger.error("LLM Schema Hallucination")
            raise LLMResponseValidationError("Evaluation schema validation failed") from exc

    async def optimize_prompt(self, current_prompt: str, failures_context: str) -> PromptOptimization:
        schema_json = PromptOptimization.model_json_schema()
        system_prompt = (
            f"{self._optimize_prompt}\n\n"
            "You MUST output ONLY a valid JSON object with the single key 'improved_prompt' "
            "containing the new prompt string. DO NOT output JSON schema definitions."
        )
        messages = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": (
                    f"Current Prompt:\n{current_prompt}\n\n"
                    f"Failures Context:\n{failures_context}\n\n"
                    f"Return JSON that matches:\n{json.dumps(schema_json)}"
                ),
            },
        ]

        response = await self._client.chat.completions.create(
            model=self._professor_model_name,
            messages=messages,
            response_format={"type": "json_object"},
            temperature=0.0,
        )

        content = response.choices[0].message.content
        if not content:
            logger.error("Groq optimization empty context=%s", truncate_text(failures_context))
            raise ValueError("LLM response is empty")

        clean_content = strip_markdown_json(content)

        try:
            return PromptOptimization.model_validate_json(clean_content)
        except ValidationError as exc:
            logger.error("LLM Schema Hallucination")
            raise LLMResponseValidationError("Optimization schema validation failed") from exc