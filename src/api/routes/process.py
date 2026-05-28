from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel

from src.api.dependencies import get_llm_client, get_state_manager, get_ticket_storage
from src.core.exceptions import ActivePromptNotFoundError
from src.core.state_manager import SystemStateManager
from src.interfaces.llm_interface import ILLMClient
from src.interfaces.storage_interface import ITicketStorage
from src.models.schemas import SupportTicketResponse
from src.services.inference_service import InferenceService
from src.workers.review_worker import trigger_review_pipeline


class ProcessRequest(BaseModel):
    text: str


router = APIRouter()


@router.post("/process", response_model=SupportTicketResponse)
async def process_ticket(
    request: ProcessRequest,
    background_tasks: BackgroundTasks,
    storage: ITicketStorage = Depends(get_ticket_storage),
    llm_client: ILLMClient = Depends(get_llm_client),
    state_manager: SystemStateManager = Depends(get_state_manager),
) -> SupportTicketResponse:
    service = InferenceService(storage, llm_client)

    try:
        response = await service.process_user_message(request.text)
    except ActivePromptNotFoundError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if await state_manager.increment_and_check_trigger():
        background_tasks.add_task(trigger_review_pipeline)

    return response
