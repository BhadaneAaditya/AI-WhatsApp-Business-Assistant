import json
import re
from datetime import datetime
from typing import Optional, List, Dict
from sqlalchemy.orm import Session

from app.models.user import User, LeadStatus
from app.models.message import Message, MessageRole
from app.utils.logging import logger


class UserService:
    @staticmethod
    def get_or_create_user(db: Session, phone_number: str) -> User:
        user = db.query(User).filter(User.phone_number == phone_number).first()
        if not user:
            user = User(phone_number=phone_number)
            db.add(user)
            db.commit()
            db.refresh(user)
            logger.info(f"Created new user: {phone_number}")
        return user

    @staticmethod
    def classify_lead(message_content: str) -> LeadStatus:
        content_lower = message_content.lower()
        
        hot_keywords = ["buy", "purchase", "order", "interested", "price", "cost", "discount", "deal", "shipping", "delivery"]
        warm_keywords = ["more info", "details", "tell me", "what is", "how much", "when", "can i", "questions"]
        
        hot_score = sum(1 for keyword in hot_keywords if keyword in content_lower)
        warm_score = sum(1 for keyword in warm_keywords if keyword in content_lower)
        
        if hot_score >= 2:
            return LeadStatus.HOT
        elif hot_score >= 1:
            return LeadStatus.WARM
        elif warm_score >= 1:
            return LeadStatus.WARM
        return LeadStatus.COLD

    @staticmethod
    def extract_order_data(message_content: str) -> Optional[Dict]:
        extracted = {}
        
        product_patterns = [
            r"(?:i want|i need|want|need|buy|order)\s+(?:a\s+)?(\w+)",
            r"(?:product|item|product is|item is)\s+(\w+)",
            r"(\w+)\s+(?:please|now|immediately)"
        ]
        for pattern in product_patterns:
            match = re.search(pattern, message_content.lower())
            if match:
                extracted["product_name"] = match.group(1).strip()
                break
        
        quantity_match = re.search(r"(\d+)\s*(?:pcs|pieces|units|items)?", message_content.lower())
        if quantity_match:
            extracted["quantity"] = int(quantity_match.group(1))
        
        price_match = re.search(r"(?:rs\.?|₹|USD|\$)\s*(\d+(?:,\d+)*)", message_content.lower())
        if price_match:
            extracted["price"] = price_match.group(1).replace(",", "")
        
        return extracted if extracted else None

    @staticmethod
    def update_user_lead_status(db: Session, user: User, message_content: str) -> User:
        new_status = UserService.classify_lead(message_content)
        
        if new_status == LeadStatus.HOT:
            user.lead_status = LeadStatus.HOT
        elif user.lead_status == LeadStatus.COLD and new_status in [LeadStatus.WARM, LeadStatus.HOT]:
            user.lead_status = new_status
        
        user.last_interaction = datetime.utcnow()
        db.commit()
        return user

    @staticmethod
    def update_extracted_data(db: Session, user: User, message_content: str) -> User:
        order_data = UserService.extract_order_data(message_content)
        
        if order_data:
            existing_data = json.loads(user.extracted_data) if user.extracted_data else {}
            existing_data.update(order_data)
            user.extracted_data = json.dumps(existing_data)
            db.commit()
            logger.info(f"Updated extracted data for user {user.phone_number}: {order_data}")
        
        return user

    @staticmethod
    def get_conversation_history(db: Session, user: User, limit: int = 10) -> List[Message]:
        messages = (
            db.query(Message)
            .filter(Message.user_id == user.id)
            .order_by(Message.timestamp.desc())
            .limit(limit)
            .all()
        )
        return list(reversed(messages))

    @staticmethod
    def get_users_needing_followup(db: Session, hours: int) -> List[User]:
        from datetime import timedelta
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        users = (
            db.query(User)
            .filter(User.last_interaction < cutoff_time)
            .all()
        )
        
        needing_followup = []
        for user in users:
            last_message = (
                db.query(Message)
                .filter(Message.user_id == user.id)
                .order_by(Message.timestamp.desc())
                .first()
            )
            if last_message and last_message.role == MessageRole.USER:
                if last_message.timestamp < cutoff_time:
                    needing_followup.append(user)
        
        return needing_followup