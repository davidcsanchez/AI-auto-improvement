import pytest

from src.config.settings import get_settings
from src.core.state_manager import SystemStateManager


@pytest.mark.asyncio
async def test_state_manager_singleton_and_lock_behavior() -> None:
    manager_one = SystemStateManager()
    manager_two = SystemStateManager()

    assert manager_one is manager_two


@pytest.mark.asyncio
async def test_state_manager_counter_and_trigger() -> None:
    settings = get_settings()
    manager = SystemStateManager()

    manager._process_count = settings.REVIEW_TRIGGER_LIMIT - 1
    should_trigger = await manager.increment_and_check_trigger()

    assert should_trigger

    manager._process_count = settings.REVIEW_TRIGGER_LIMIT - 2
    should_trigger = await manager.increment_and_check_trigger()

    assert not should_trigger
