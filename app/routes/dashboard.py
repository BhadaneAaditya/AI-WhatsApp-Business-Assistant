from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.database import get_db
from app.models.user import User, LeadStatus
from app.models.message import Message
from app.utils.logging import logger

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


class UserResponse(BaseModel):
    id: int
    phone_number: str
    name: Optional[str]
    lead_status: str
    extracted_data: Optional[str]
    last_interaction: datetime
    created_at: datetime
    
    class Config:
        from_attributes = True


class MessageResponse(BaseModel):
    id: int
    role: str
    content: str
    timestamp: datetime
    
    class Config:
        from_attributes = True


@router.get("/users", response_model=List[UserResponse])
async def get_users(
    db: Session = Depends(get_db),
    lead_status: Optional[str] = None
):
    query = db.query(User)
    
    if lead_status:
        try:
            status = LeadStatus(lead_status)
            query = query.filter(User.lead_status == status)
        except ValueError:
            pass
    
    users = query.order_by(User.last_interaction.desc()).all()
    return users


@router.get("/users/{phone_number}", response_model=UserResponse)
async def get_user(
    phone_number: str,
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.phone_number == phone_number).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.get("/users/{phone_number}/messages")
async def get_user_messages(
    phone_number: str,
    db: Session = Depends(get_db),
    limit: int = 50
):
    user = db.query(User).filter(User.phone_number == phone_number).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    messages = (
        db.query(Message)
        .filter(Message.user_id == user.id)
        .order_by(Message.timestamp.desc())
        .limit(limit)
        .all()
    )
    
    return [
        {
            "id": m.id,
            "role": m.role.value,
            "content": m.content,
            "timestamp": m.timestamp.isoformat()
        }
        for m in reversed(messages)
    ]


@router.get("/stats")
async def get_stats(db: Session = Depends(get_db)):
    total_users = db.query(User).count()
    hot_users = db.query(User).filter(User.lead_status == LeadStatus.HOT).count()
    warm_users = db.query(User).filter(User.lead_status == LeadStatus.WARM).count()
    cold_users = db.query(User).filter(User.lead_status == LeadStatus.COLD).count()
    total_messages = db.query(Message).count()
    
    recent_users = (
        db.query(User)
        .order_by(User.created_at.desc())
        .limit(10)
        .all()
    )
    
    return {
        "total_users": total_users,
        "lead_breakdown": {
            "hot": hot_users,
            "warm": warm_users,
            "cold": cold_users
        },
        "total_messages": total_messages,
        "recent_users": [
            {
                "phone_number": u.phone_number,
                "lead_status": u.lead_status.value,
                "created_at": u.created_at.isoformat()
            }
            for u in recent_users
        ]
    }