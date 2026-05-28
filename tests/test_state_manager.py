import pytest

from src.config.settings import get_settings
from src.core.state_manager import SystemStateManager


@pytest.mark.asyncio
async def test_state_manager_singleton_and_lock_behavior() -> None:
    manager_one = SystemStateManager()
    manager_two = SystemStateManager()

    assert manager_one is manager_two

    await manager_one.acquire_lock()
    assert manager_one._lock.locked()

    await manager_one.release_lock()
    assert not manager_one._lock.locked()


@pytest.mark.asyncio
async def test_state_manager_counter_and_trigger() -> None:
    settings = get_settings()
    manager = SystemStateManager()

    manager._process_count = settings.REVIEW_TRIGGER_LIMIT - 1
    updated_count = await manager.increment_process_count()

    assert updated_count == settings.REVIEW_TRIGGER_LIMIT
    assert await manager.should_trigger_review()

    manager._process_count = settings.REVIEW_TRIGGER_LIMIT - 2
    await manager.increment_process_count()

    assert not await manager.should_trigger_review()
