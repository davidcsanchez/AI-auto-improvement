import json

from src.config.settings import get_settings
from src.core.logger import get_logger, truncate_text
from src.interfaces.llm_interface import ILLMClient
from src.interfaces.storage_interface import ITicketStorage
from src.models.prompt_version import PromptVersion
from src.models.schemas import RegressionResult, SupportTicketResponse


logger = get_logger(__name__)


class RegressionService:
    def __init__(self, storage: ITicketStorage, llm_client: ILLMClient) -> None:
        self._storage = storage
        self._llm_client = llm_client

    async def run_regression(
        self,
        new_prompt_content: str,
        parent_prompt_id: int,
        triggering_sample_ids: list[int],
    ) -> RegressionResult:
        golden_samples = await self._storage.get_golden_samples()
        failures: list[str] = []
        passed = 0

        for sample in golden_samples:
            try:
                response = await self._llm_client.generate_structured_ticket(
                    system_prompt=new_prompt_content,
                    user_input=sample.input_text,
                )
            except Exception as exc:
                logger.exception(
                    "Regression LLM failure input=%s",
                    truncate_text(sample.input_text),
                )
                failures.append(f"Input: {sample.input_text}\nError: {exc}")
                continue

            try:
                expected = SupportTicketResponse.model_validate_json(sample.output_json)
            except Exception as exc:
                logger.exception(
                    "Invalid golden sample output id=%s",
                    sample.id,
                )
                failures.append(f"Input: {sample.input_text}\nError: {exc}")
                continue

            if response == expected:
                passed += 1
                continue

            failures.append(
                "\n".join(
                    [
                        f"Input: {sample.input_text}",
                        f"Expected: {expected.model_dump_json()}",
                        f"Actual: {response.model_dump_json()}",
                    ]
                )
            )

        base_total = len(golden_samples)
        base_passed = passed
        settings = get_settings()
        accuracy = (base_passed / base_total) if base_total else 0.0
        regression_passed = accuracy >= settings.MIN_REGRESSION_ACCURACY

        version_number = await self._get_next_version_number()
        failure_context = "\n\n".join(failures) if failures else None
        failed_cases = json.dumps(failures)

        prompt_version = PromptVersion(
            parent_prompt_id=parent_prompt_id,
            content=new_prompt_content,
            version_number=version_number,
            is_active=regression_passed,
            triggering_sample_ids=json.dumps(triggering_sample_ids),
            regression_passed=regression_passed,
            base_passed=base_passed,
            base_total=base_total,
            failed_cases=failed_cases,
        )

        await self._storage.save_prompt(prompt_version)

        if regression_passed:
            logger.critical(
                "Regression passed with base_passed=%s base_total=%s",
                base_passed,
                base_total,
            )
            return RegressionResult(passed=True, failure_context=None)

        logger.warning(
            "Regression failed with base_passed=%s base_total=%s",
            base_passed,
            base_total,
        )
        return RegressionResult(passed=False, failure_context=failure_context)

    async def _get_next_version_number(self) -> int:
        active_prompt = await self._storage.get_active_prompt()
        if active_prompt is None:
            return 1
        return active_prompt.version_number + 1
