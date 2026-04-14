import logging
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Header, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import Base, engine, get_db
from app.logging_config import configure_logging
from app.metrics import MetricsMiddleware, metrics_response
from app.services.bot_handler import BotHandler
from app.services.telegram_service import TelegramService

configure_logging()
settings = get_settings()
logger = logging.getLogger(__name__)
bot_handler = BotHandler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    if settings.set_telegram_webhook_on_startup and settings.telegram_bot_token and settings.public_base_url:
        try:
            TelegramService().set_webhook()
            logger.info("Telegram webhook configured: %s", settings.webhook_url)
        except Exception as exc:
            logger.warning("Failed to set Telegram webhook: %s", exc)
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)
app.add_middleware(MetricsMiddleware)


@app.get("/")
def root() -> dict[str, str]:
    return {
        "app": settings.app_name,
        "environment": settings.app_env,
        "status": "ok",
    }


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "healthy"}


@app.get("/readyz")
def readyz(db: Session = Depends(get_db)) -> dict[str, str]:
    db.execute(text("SELECT 1"))
    return {"status": "ready"}


@app.get("/metrics")
def metrics():
    return metrics_response()


@app.post("/webhook/telegram")
def telegram_webhook(
    update: dict,
    db: Session = Depends(get_db),
    x_telegram_bot_api_secret_token: str | None = Header(default=None),
):
    expected = settings.telegram_webhook_secret_token
    if expected and x_telegram_bot_api_secret_token != expected:
        raise HTTPException(status_code=403, detail="Invalid Telegram secret token")

    bot_handler.handle_update(db, update)
    return {"ok": True}

