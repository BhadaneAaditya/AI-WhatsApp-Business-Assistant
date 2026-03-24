from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.whatsapp_service import whatsapp_service
from app.services.user_service import UserService
from app.services.ai_service import ai_service
from app.models.message import Message, MessageRole
from app.utils.logging import logger

router = APIRouter(prefix="/send-message", tags=["message"])


class SendMessageRequest(BaseModel):
    phone_number: str
    message: str


@router.post("")
async def send_message(
    request: SendMessageRequest,
    db: Session = Depends(get_db)
):
    result = whatsapp_service.send_message(request.phone_number, request.message)
    
    if result["success"]:
        user = UserService.get_or_create_user(db, request.phone_number)
        
        message = Message(
            user_id=user.id,
            role=MessageRole.ASSISTANT,
            content=request.message
        )
        db.add(message)
        db.commit()
        
        return {"status": "success", "message_id": result.get("message_id")}
    
    raise HTTPException(status_code=400, detail=result.get("error", "Failed to send message"))


class AIGenerateRequest(BaseModel):
    phone_number: str
    custom_prompt: str = ""


@router.post("/ai-generate")
async def generate_ai_message(
    request: AIGenerateRequest,
    db: Session = Depends(get_db)
):
    user = UserService.get_or_create_user(db, request.phone_number)
    
    conversation_history = UserService.get_conversation_history(db, user)
    
    ai_response = ai_service.generate_response(
        conversation_history,
        request.custom_prompt or "Please provide more information about your products."
    )
    
    return {"response": ai_response}