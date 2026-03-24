import httpx
from typing import Dict, Any
import json

from app.utils.config import config
from app.utils.logging import logger


class WhatsAppService:
    API_URL = "https://graph.facebook.com/v18.0"

    @staticmethod
    def send_message(phone_number: str, message: str) -> Dict[str, Any]:
        if not config.WHATSAPP_ACCESS_TOKEN or not config.WHATSAPP_PHONE_NUMBER_ID:
            logger.warning("WhatsApp API credentials not configured")
            return {"success": False, "error": "WhatsApp API not configured"}

        url = f"{WhatsAppService.API_URL}/{config.WHATSAPP_PHONE_NUMBER_ID}/messages"
        
        headers = {
            "Authorization": f"Bearer {config.WHATSAPP_ACCESS_TOKEN}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "messaging_product": "whatsapp",
            "to": phone_number,
            "type": "text",
            "text": {"body": message}
        }
        
        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.post(url, headers=headers, json=payload)
                
                if response.status_code == 200:
                    result = response.json()
                    message_id = result.get("messages", [{}])[0].get("id")
                    logger.info(f"Message sent to {phone_number}, message_id: {message_id}")
                    return {"success": True, "message_id": message_id}
                else:
                    error = response.json()
                    logger.error(f"Failed to send message: {error}")
                    return {"success": False, "error": error}
        except Exception as e:
            logger.error(f"Error sending WhatsApp message: {e}")
            return {"success": False, "error": str(e)}

    @staticmethod
    def verify_webhook(mode: str, token: str, challenge: str) -> bool:
        return mode == "subscribe" and token == config.WHATSAPP_WEBHOOK_VERIFY_TOKEN

    @staticmethod
    def parse_webhook_payload(payload: Dict) -> Dict:
        entry = payload.get("entry", [{}])[0]
        changes = entry.get("changes", [{}])[0]
        value = changes.get("value", {})
        
        messages = value.get("messages", [])
        if messages:
            message = messages[0]
            return {
                "phone_number": message.get("from"),
                "message_id": message.get("id"),
                "text": message.get("text", {}).get("body", ""),
                "timestamp": value.get("metadata", {}).get("timestamp")
            }
        
        return {}


whatsapp_service = WhatsAppService()