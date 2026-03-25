from contextlib import asynccontextmanager
from fastapi import FastAPI

from app.database import init_db
from app.routes import webhook_router, message_router, dashboard_router
from app.services.scheduler_service import scheduler_service
from app.utils.config import config
from app.utils.logging import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting AI WhatsApp Assistant")
    init_db()
    scheduler_service.start()
    yield
    scheduler_service.stop()
    logger.info("Shutting down AI WhatsApp Assistant")


app = FastAPI(
    title="AI WhatsApp Business Assistant",
    description="A production-ready MVP for WhatsApp AI assistant with LLM integration",
    version="1.0.0",
    lifespan=lifespan
)

app.include_router(webhook_router)
app.include_router(message_router)
app.include_router(dashboard_router)


@app.get("/")
async def root():
    return {
        "name": "AI WhatsApp Business Assistant",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=config.APP_HOST,
        port=config.APP_PORT,
        reload=True
    )
