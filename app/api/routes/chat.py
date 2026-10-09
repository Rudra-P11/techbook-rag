from fastapi import APIRouter
from app.api.schemas.chat import ChatRequest, ChatResponse
from app.services.chat_service import chat_service

router = APIRouter(prefix="/api/v1/chat", tags=["Chat"])


@router.post("", response_model=ChatResponse)
def chat_endpoint(request: ChatRequest):
    return chat_service.answer_query(request)
