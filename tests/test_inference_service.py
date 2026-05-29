import pytest

from src.models.prompt_version import PromptVersion
from src.models.schemas import AffectedComponent, SupportTicketResponse, TicketIntent, TicketUrgency
from src.services.inference_service import InferenceService


class MockStorage:
    def __init__(self, prompt: PromptVersion) -> None:
        self._prompt = prompt
        self.saved_sample = None

    async def get_active_prompt(self) -> PromptVersion | None:
        return self._prompt

    async def save_sample(self, sample):
        self.saved_sample = sample
        return sample


class MockLLMClient:
    def __init__(self, response: SupportTicketResponse) -> None:
        self._response = response

    async def generate_structured_ticket(self, system_prompt: str, user_input: str) -> SupportTicketResponse:
        return self._response


@pytest.mark.asyncio
async def test_inference_service_processes_message_and_saves_sample() -> None:
    prompt = PromptVersion(
        id=1,
        parent_prompt_id=None,
        content="Prompt",
        version_number=1,
        is_active=True,
        triggering_sample_ids="[]",
        regression_passed=None,
        base_passed=None,
        base_total=None,
        failed_cases="[]",
    )

    response = SupportTicketResponse(
        intent=TicketIntent.feature_request,
        urgency=TicketUrgency.medium,
        affected_component=AffectedComponent.frontend,
        requires_manager_escalation=False,
    )

    storage = MockStorage(prompt)
    llm_client = MockLLMClient(response)
    service = InferenceService(storage, llm_client)

    result = await service.process_user_message("Please add dark mode")

    assert result == response
    assert storage.saved_sample is not None
    assert storage.saved_sample.prompt_version_id == prompt.id
    assert storage.saved_sample.input_text == "Please add dark mode"
    assert storage.saved_sample.output_json is not None
