import logging

import pytest

from src.models.prompt_version import PromptVersion
from src.models.schemas import (
    AffectedComponent,
    PromptOptimization,
    RegressionResult,
    SampleEvaluation,
    SupportTicketResponse,
    TicketIntent,
    TicketUrgency,
)
from src.models.ticket_sample import TicketSample
from src.services.review_service import ReviewService


class MockStorage:
    def __init__(self, prompt: PromptVersion, samples: list[TicketSample]) -> None:
        self._prompt = prompt
        self._samples = samples
        self.updated_samples: list[TicketSample] = []
        self.saved_golden_samples = []
        self.enforce_called = False

    async def get_unevaluated_samples(self, limit: int) -> list[TicketSample]:
        return self._samples[:limit]

    async def get_active_prompt(self) -> PromptVersion | None:
        return self._prompt

    async def update_ticket_sample(self, sample: TicketSample) -> TicketSample:
        self.updated_samples.append(sample)
        return sample

    async def save_golden_sample(self, sample) -> None:
        self.saved_golden_samples.append(sample)

    async def enforce_golden_dataset_limit(self, max_total: int) -> None:
        self.enforce_called = True


class MockLLMClient:
    def __init__(self, evaluation: SampleEvaluation) -> None:
        self._evaluation = evaluation
        self.optimize_calls: list[str] = []

    async def evaluate_sample(
        self,
        current_prompt: str,
        user_input: str,
        student_output: str,
    ) -> SampleEvaluation:
        return self._evaluation

    async def optimize_prompt(self, current_prompt: str, failures_context: str) -> PromptOptimization:
        self.optimize_calls.append(failures_context)
        return PromptOptimization(improved_prompt=f"{current_prompt}-optimized-{len(self.optimize_calls)}")


class MockRegressionService:
    def __init__(self, results: list[RegressionResult]) -> None:
        self._results = results
        self.calls: list[str] = []

    async def run_regression(
        self,
        new_prompt_content: str,
        parent_prompt_id: int,
        triggering_sample_ids: list[int],
    ) -> RegressionResult:
        self.calls.append(new_prompt_content)
        return self._results[len(self.calls) - 1]


@pytest.mark.asyncio
async def test_review_retry_loop_retries_and_logs_success(caplog: pytest.LogCaptureFixture) -> None:
    prompt = PromptVersion(
        id=10,
        parent_prompt_id=None,
        content="Base prompt",
        version_number=1,
        is_active=True,
        triggering_sample_ids="[]",
        regression_passed=None,
        base_passed=None,
        base_total=None,
        failed_cases="[]",
    )

    sample = TicketSample(
        id=1,
        input_text="App crashes on login",
        output_json='{"intent": "bug_report"}',
        is_correct=None,
        for_evaluation=True,
        prompt_version_id=prompt.id,
    )

    expected_output = SupportTicketResponse(
        intent=TicketIntent.bug_report,
        urgency=TicketUrgency.high,
        affected_component=AffectedComponent.backend_api,
        requires_manager_escalation=True,
    )

    evaluation = SampleEvaluation(is_correct=False, expected_output=expected_output)

    storage = MockStorage(prompt, [sample])
    llm_client = MockLLMClient(evaluation)
    regression = MockRegressionService(
        [
            RegressionResult(passed=False, failure_context="Golden sample 1 failed"),
            RegressionResult(passed=True, failure_context=None),
        ]
    )

    service = ReviewService(storage, llm_client, regression)

    caplog.set_level(logging.INFO)
    await service.run_review_cycle()

    assert len(llm_client.optimize_calls) == 2
    assert "Golden sample 1 failed" in llm_client.optimize_calls[1]
    assert storage.enforce_called
    assert storage.updated_samples
    assert storage.saved_golden_samples
    assert any("Regression passed" in record.message for record in caplog.records)
