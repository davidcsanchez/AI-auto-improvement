from src.config.settings import get_settings
from src.core.exceptions import LLMResponseValidationError
from src.core.logger import get_logger, truncate_text
from src.interfaces.llm_interface import ILLMClient
from src.interfaces.storage_interface import ITicketStorage
from src.models.golden_sample import GoldenSample
from src.models.schemas import RegressionResult, SampleEvaluation, SupportTicketResponse
from src.models.ticket_sample import TicketSample
from src.services.regression_service import RegressionService


logger = get_logger(__name__)


class ReviewService:
    def __init__(
        self,
        storage: ITicketStorage,
        llm_client: ILLMClient,
        regression_service: RegressionService,
    ) -> None:
        self._storage = storage
        self._llm_client = llm_client
        self._regression_service = regression_service

    async def run_review_cycle(self) -> None:
        settings = get_settings()
        logger.info("Review cycle started")
        samples = await self._storage.get_unevaluated_samples(settings.REVIEW_BATCH_SIZE)
        active_prompt = await self._storage.get_active_prompt()

        if active_prompt is None:
            logger.error("Review cycle aborted: no active prompt")
            return

        if not samples:
            logger.info("Review cycle skipped: no unevaluated samples")
            return

        failed_samples: list[tuple[TicketSample, SupportTicketResponse]] = []
        triggering_sample_ids: list[int] = []

        for sample in samples:
            if sample.output_json is None:
                logger.error("Sample missing output id=%s", sample.id)
                continue

            evaluation = await self._evaluate_sample(active_prompt.content, sample)
            if evaluation is None:
                continue

            sample.is_correct = evaluation.is_correct
            await self._storage.update_ticket_sample(sample)

            if not evaluation.is_correct:
                if evaluation.expected_output is None:
                    logger.error("Expected output missing for failed sample id=%s", sample.id)
                    continue

                golden_sample = GoldenSample(
                    input_text=sample.input_text,
                    output_json=evaluation.expected_output.model_dump_json(),
                    is_base_case=False,
                )

                await self._storage.save_golden_sample(golden_sample)
                failed_samples.append((sample, evaluation.expected_output))
                if sample.id is not None:
                    triggering_sample_ids.append(sample.id)

        await self._storage.enforce_golden_dataset_limit(settings.MAX_GOLDEN_SAMPLES)

        if not failed_samples:
            logger.info("Review cycle completed: no failures")
            return

        failures_context = self._build_failure_context(failed_samples)
        attempts = 0
        max_attempts = 1 + settings.MAX_PROMPT_RETRIES
        current_failures_context = failures_context
        result: RegressionResult | None = None

        while attempts < max_attempts:
            logger.info("Prompt optimization attempt %s of %s", attempts + 1, max_attempts)
            try:
                optimization = await self._llm_client.optimize_prompt(
                    active_prompt.content,
                    current_failures_context,
                )
            except LLMResponseValidationError:
                logger.warning("Prompt optimization returned invalid schema")
                attempts += 1
                continue

            result = await self._regression_service.run_regression(
                new_prompt_content=optimization.improved_prompt,
                parent_prompt_id=active_prompt.id,
                triggering_sample_ids=triggering_sample_ids,
            )

            if result.passed:
                logger.critical("Regression passed after %s attempts", attempts + 1)
                return

            logger.warning("Regression failed attempt %s", attempts + 1)
            attempts += 1

            if result.failure_context:
                current_failures_context = (
                    f"{current_failures_context}\n\nRegression Failures:\n{result.failure_context}"
                )

        if result is not None or not result.passed:
            logger.critical(
                "System surrendered after %s attempts",
                max_attempts,
            )
        logger.info("Review cycle completed")

    async def _evaluate_sample(
        self,
        current_prompt: str,
        sample: TicketSample,
    ) -> SampleEvaluation | None:
        try:
            return await self._llm_client.evaluate_sample(
                current_prompt=current_prompt,
                user_input=sample.input_text,
                student_output=sample.output_json or "",
            )
        except Exception:
            logger.exception(
                "Sample evaluation failed id=%s input=%s",
                sample.id,
                truncate_text(sample.input_text),
            )
            return None

    def _build_failure_context(self, failed: list[tuple[TicketSample, SupportTicketResponse]]) -> str:
        blocks: list[str] = []
        for sample, expected in failed:
            blocks.append(
                "\n".join(
                    [
                        f"Input: {sample.input_text}",
                        f"Student Output: {sample.output_json}",
                        f"Expected Output: {expected.model_dump_json()}",
                    ]
                )
            )
        return "\n\n".join(blocks)
