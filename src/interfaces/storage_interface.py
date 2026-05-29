from typing import Protocol

from src.models.golden_sample import GoldenSample
from src.models.prompt_version import PromptVersion
from src.models.ticket_sample import TicketSample


class ITicketStorage(Protocol):
    async def save_prompt(self, prompt: PromptVersion) -> PromptVersion:
        ...

    async def get_active_prompt(self) -> PromptVersion | None:
        ...

    async def save_sample(self, sample: TicketSample) -> TicketSample:
        ...

    async def get_unevaluated_samples(self, limit: int) -> list[TicketSample]:
        ...

    async def update_ticket_sample(self, sample: TicketSample) -> TicketSample:
        ...

    async def get_failed_evaluations(self) -> list[TicketSample]:
        ...

    async def get_golden_samples(self) -> list[GoldenSample]:
        ...

    async def save_golden_sample(self, sample: GoldenSample) -> GoldenSample:
        ...

    async def enforce_golden_dataset_limit(self, max_total: int) -> None:
        ...
