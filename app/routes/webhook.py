from fastapi import APIRouter, Request, Query, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.services.user_service import UserService
from app.services.ai_service import ai_service
from app.services.whatsapp_service import whatsapp_service
from app.models.message import Message, MessageRole
from app.utils.logging import logger

router = APIRouter(prefix="/webhook", tags=["webhook"])


@router.get("")
async def verify_webhook(
    mode: str = Query(...),
    token: str = Query(...),
    challenge: Optional[str] = Query(None)
):
    if whatsapp_service.verify_webhook(mode, token, challenge):
        logger.info("Webhook verified successfully")
        return {"status": "success"}
    logger.warning("Webhook verification failed")
    raise HTTPException(status_code=403, detail="Verification failed")


@router.post("")
async def receive_webhook(
    request: Request,
    db: Session = Depends(get_db)
):
    try:
        payload = await request.json()
        logger.info(f"Received webhook payload: {payload}")
        
        message_data = whatsapp_service.parse_webhook_payload(payload)
        
        if not message_data or not message_data.get("text"):
            return {"status": "ok"}
        
        phone_number = message_data["phone_number"]
        message_text = message_data["text"]
        message_id = message_data.get("message_id")
        
        user = UserService.get_or_create_user(db, phone_number)
        
        user_message = Message(
            user_id=user.id,
            role=MessageRole.USER,
            content=message_text,
            whatsapp_message_id=message_id
        )
        db.add(user_message)
        
        UserService.update_user_lead_status(db, user, message_text)
        UserService.update_extracted_data(db, user, message_text)
        
        db.commit()
        
        conversation_history = UserService.get_conversation_history(db, user)
        
        ai_response = ai_service.generate_response(conversation_history, message_text)
        
        assistant_message = Message(
            user_id=user.id,
            role=MessageRole.ASSISTANT,
            content=ai_response
        )
        db.add(assistant_message)
        db.commit()
        
        send_result = whatsapp_service.send_message(phone_number, ai_response)
        
        if not send_result["success"]:
            logger.error(f"Failed to send response to {phone_number}")
        
        return {"status": "ok"}
        
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        return {"status": "error", "message": str(e)}