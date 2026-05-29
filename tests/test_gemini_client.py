from unittest.mock import MagicMock

import pytest

from src.llm.gemini_client import GeminiLLMClient
from src.models.schemas import AffectedComponent, SupportTicketResponse, TicketIntent, TicketUrgency


class DummySettings:
    API_KEY = "test-key"
    STUDENT_LLM_MODEL_NAME = "test-student"
    PROFESSOR_LLM_MODEL_NAME = "test-professor"


@pytest.mark.asyncio
async def test_gemini_client_returns_structured_response(monkeypatch: pytest.MonkeyPatch) -> None:
    expected = SupportTicketResponse(
        intent=TicketIntent.bug_report,
        urgency=TicketUrgency.high,
        affected_component=AffectedComponent.backend_api,
        requires_manager_escalation=False,
    )

    response = MagicMock()
    response.parsed = expected

    models = MagicMock()
    models.generate_content.return_value = response

    client_instance = MagicMock()
    client_instance.models = models

    genai_module = MagicMock()
    genai_module.Client.return_value = client_instance

    monkeypatch.setattr("src.llm.gemini_client.genai", genai_module)
    monkeypatch.setattr("src.llm.gemini_client.get_settings", lambda: DummySettings())

    client = GeminiLLMClient()
    result = await client.generate_structured_ticket("system", "user input")

    assert result == expected
    models.generate_content.assert_called_once()
