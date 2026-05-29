from src.api.dependencies import get_review_service
from src.core.logger import get_logger
from src.core.state_manager import SystemStateManager


logger = get_logger(__name__)


async def trigger_review_pipeline(state_manager: SystemStateManager) -> None:
    logger.info("Triggering review pipeline")
    service = get_review_service()
    try:
        await service.run_review_cycle()
    finally: 
        await state_manager.release_review_lock
        logger.info("Review pipeline lock released")
