from functools import lru_cache

from src.core.sqlite_storage import SQLiteTicketStorage
from src.core.state_manager import SystemStateManager
from src.interfaces.llm_interface import ILLMClient
from src.interfaces.storage_interface import ITicketStorage
from src.llm.groq_client import GroqLLMClient


@lru_cache
def get_ticket_storage() -> ITicketStorage:
    return SQLiteTicketStorage()


@lru_cache
def get_state_manager() -> SystemStateManager:
    return SystemStateManager()


@lru_cache
def get_llm_client() -> ILLMClient:
    return GroqLLMClient()
