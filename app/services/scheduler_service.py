from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta

from app.database import SessionLocal
from app.services.user_service import UserService
from app.services.whatsapp_service import whatsapp_service
from app.services.ai_service import ai_service
from app.utils.config import config
from app.utils.logging import logger


class SchedulerService:
    def __init__(self):
        self.scheduler = BackgroundScheduler()

    def start(self):
        self.scheduler.add_job(
            self.check_followups,
            "interval",
            hours=1,
            id="followup_check"
        )
        self.scheduler.start()
        logger.info("Scheduler started")

    def stop(self):
        self.scheduler.shutdown()
        logger.info("Scheduler stopped")

    def check_followups(self):
        db = SessionLocal()
        try:
            timeout_hours = config.FOLLOWUP_TIMEOUT_HOURS
            users = UserService.get_users_needing_followup(db, timeout_hours)
            
            for user in users:
                followup_message = ai_service.generate_followup_message(user.name)
                result = whatsapp_service.send_message(user.phone_number, followup_message)
                
                if result["success"]:
                    logger.info(f"Sent follow-up to user {user.phone_number}")
                else:
                    logger.error(f"Failed to send follow-up to user {user.phone_number}: {result.get('error')}")
        except Exception as e:
            logger.error(f"Error in follow-up scheduler: {e}")
        finally:
            db.close()


scheduler_service = SchedulerService()