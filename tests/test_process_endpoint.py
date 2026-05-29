from fastapi.testclient import TestClient

from src.api import dependencies
from src.api.routes import process as process_routes
from src.main import app
from src.models.prompt_version import PromptVersion
from src.models.schemas import AffectedComponent, SupportTicketResponse, TicketIntent, TicketUrgency


class MockStorage:
    def __init__(self, prompt: PromptVersion) -> None:
        self._prompt = prompt

    async def get_active_prompt(self) -> PromptVersion | None:
        return self._prompt

    async def save_sample(self, sample):
        return sample


class MockLLMClient:
    def __init__(self, response: SupportTicketResponse) -> None:
        self._response = response

    async def generate_structured_ticket(self, system_prompt: str, user_input: str) -> SupportTicketResponse:
        return self._response


class MockStateManager:
    def __init__(self, should_trigger: bool) -> None:
        self._should_trigger = should_trigger
        self.increment_calls = 0

    async def increment_and_check_trigger(self) -> bool:
        self.increment_calls += 1
        return self._should_trigger


def test_process_endpoint_triggers_background_task(monkeypatch) -> None:
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
        intent=TicketIntent.bug_report,
        urgency=TicketUrgency.high,
        affected_component=AffectedComponent.frontend,
        requires_manager_escalation=False,
    )

    storage = MockStorage(prompt)
    llm_client = MockLLMClient(response)
    state_manager = MockStateManager(should_trigger=True)
    was_called = {"value": False}

    async def fake_trigger_review_pipeline() -> None:
        was_called["value"] = True

    monkeypatch.setattr(process_routes, "trigger_review_pipeline", fake_trigger_review_pipeline)

    app.dependency_overrides[dependencies.get_ticket_storage] = lambda: storage
    app.dependency_overrides[dependencies.get_llm_client] = lambda: llm_client
    app.dependency_overrides[dependencies.get_state_manager] = lambda: state_manager

    with TestClient(app) as client:
        result = client.post("/process", json={"text": "My phone is overheating"})

    assert result.status_code == 200
    assert result.json()["intent"] == TicketIntent.bug_report.value
    assert was_called["value"] is True

    app.dependency_overrides.clear()
