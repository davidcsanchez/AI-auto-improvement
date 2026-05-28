import asyncio

from src.config.settings import get_settings


class SystemStateManager():
    _instance: "SystemStateManager | None" = None
    _initialized: bool = False

    def __new__(cls) -> "SystemStateManager":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        if self.__class__._initialized:
            return

        settings = get_settings()
        self._lock = asyncio.Lock()
        self._process_count = 0
        self._review_trigger_limit = settings.REVIEW_TRIGGER_LIMIT

        if self._review_trigger_limit <= 0:
            raise ValueError("REVIEW_TRIGGER_LIMIT must be greater than zero")

        self.__class__._initialized = True

    async def increment_process_count(self) -> int:
        self._process_count += 1
        return self._process_count

    async def should_trigger_review(self) -> bool:
        if self._process_count <= 0:
            return False
        return self._process_count % self._review_trigger_limit == 0

    async def acquire_lock(self) -> None:
        await self._lock.acquire()

    async def release_lock(self) -> None:
        if self._lock.locked():
            self._lock.release()
