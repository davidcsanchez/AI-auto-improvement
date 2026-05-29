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
        self._is_review_running = False
        if self._review_trigger_limit <= 0:
            raise ValueError("REVIEW_TRIGGER_LIMIT must be greater than zero")

        self.__class__._initialized = True

    async def increment_and_check_trigger(self) -> bool:
        async with self._lock:
            self._process_count += 1
            if self._process_count % self._review_trigger_limit == 0:
                if not self._is_review_running:
                    self._is_review_running = True
                    return True
            return False
        
    async def release_review_lock(self) -> None:
        async with self._lock:
            self._is_review_running = False

