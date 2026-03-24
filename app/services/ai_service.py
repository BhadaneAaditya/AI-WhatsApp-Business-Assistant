from typing import List, Dict
from openai import OpenAI
import json

from app.models.message import Message, MessageRole
from app.utils.config import config
from app.utils.logging import logger


class AIService:
    def __init__(self):
        self.client = None
        if config.OPENAI_API_KEY:
            self.client = OpenAI(api_key=config.OPENAI_API_KEY)

    def generate_response(self, conversation_history: List[Message], current_message: str) -> str:
        if not self.client:
            return "AI service is not configured. Please set OPENAI_API_KEY."

        messages = self._build_messages(conversation_history, current_message)
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                temperature=0.7,
                max_tokens=500
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Error generating AI response: {e}")
            return "I apologize, but I'm having trouble responding right now. Please try again later."

    def _build_messages(self, conversation_history: List[Message], current_message: str) -> List[Dict]:
        system_prompt = """You are a helpful and professional business sales assistant for an e-commerce store.
Your goal is to assist customers, answer their questions, help them find products, and encourage purchases.
Be friendly, concise, and helpful. If you don't have specific product information, acknowledge that and offer to help in other ways.
Never make up specific prices or product details unless provided in the conversation.
Always end with a helpful question or offer to assist further."""

        messages = [{"role": "system", "content": system_prompt}]

        for msg in conversation_history:
            role = "assistant" if msg.role == MessageRole.ASSISTANT else "user"
            messages.append({"role": role, "content": msg.content})

        messages.append({"role": "user", "content": current_message})
        
        return messages

    def generate_followup_message(self, user_name: str = None) -> str:
        if not self.client:
            return "Hi! I wanted to follow up on our conversation. Is there anything else I can help you with?"

        prefix = f"Hi {user_name}! " if user_name else "Hi! "
        
        prompt = f"""Generate a friendly follow-up message for a WhatsApp customer who hasn't responded in a while.
The message should be brief, polite, and offer to help with any questions.
Start with: "{prefix}" """

        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=100
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Error generating follow-up message: {e}")
            return f"{prefix}I wanted to check in - are you still interested in our products? Let me know if you have any questions!"


ai_service = AIService()