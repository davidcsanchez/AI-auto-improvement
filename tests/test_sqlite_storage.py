from pathlib import Path

import pytest

from src.core.sqlite_storage import SQLiteTicketStorage
from src.models.prompt_version import PromptVersion
from src.models.ticket_sample import TicketSample


@pytest.mark.asyncio
async def test_sqlite_storage_prompt_and_sample_save(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    db_path = tmp_path.joinpath("test.db")
    monkeypatch.setenv("DATABASE_URL", f"sqlite+aiosqlite:///{db_path.as_posix()}")

    storage = SQLiteTicketStorage()

    prompt = PromptVersion(
        parent_prompt_id=None,
        content="Initial prompt",
        version_number=1,
        is_active=True,
        triggering_sample_ids="[]",
        regression_passed=None,
        base_passed=None,
        base_total=None,
        failed_cases="[]",
    )

    saved_prompt = await storage.save_prompt(prompt)
    active_prompt = await storage.get_active_prompt()

    assert saved_prompt.id is not None
    assert active_prompt is not None
    assert active_prompt.id == saved_prompt.id

    sample = TicketSample(
        input_text="Hello",
        output_json="{}",
        is_correct=None,
        for_evaluation=False,
        prompt_version_id=saved_prompt.id,
    )

    saved_sample = await storage.save_sample(sample)

    assert saved_sample.id is not None
    assert saved_sample.prompt_version_id == saved_prompt.id
