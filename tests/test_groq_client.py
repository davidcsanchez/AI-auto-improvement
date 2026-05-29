from unittest.mock import AsyncMock, MagicMock

import pytest

from src.llm.groq_client import GroqLLMClient
from src.models.schemas import AffectedComponent, SupportTicketResponse, TicketIntent, TicketUrgency


class DummySettings:
    API_KEY = "test-key"
    STUDENT_LLM_MODEL_NAME = "test-student"
    PROFESSOR_LLM_MODEL_NAME = "test-professor"


@pytest.mark.asyncio
async def test_groq_client_returns_structured_response(monkeypatch: pytest.MonkeyPatch) -> None:
    expected = SupportTicketResponse(
        intent=TicketIntent.access_issue,
        urgency=TicketUrgency.medium,
        affected_component=AffectedComponent.frontend,
        requires_manager_escalation=False,
    )

    content = expected.model_dump_json()
    response = MagicMock()
    response.choices = [MagicMock(message=MagicMock(content=content))]

    completions = MagicMock()
    completions.create = AsyncMock(return_value=response)

    chat = MagicMock()
    chat.completions = completions

    client_instance = MagicMock()
    client_instance.chat = chat

    groq_module = MagicMock()
    groq_module.AsyncGroq.return_value = client_instance

    monkeypatch.setattr("src.llm.groq_client.AsyncGroq", groq_module.AsyncGroq)
    monkeypatch.setattr("src.llm.groq_client.get_settings", lambda: DummySettings())

    client = GroqLLMClient()
    result = await client.generate_structured_ticket("system", "user input")

    assert result == expected
    completions.create.assert_called_once()
