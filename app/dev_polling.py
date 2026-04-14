import logging
import time

from app.database import Base, SessionLocal, engine
from app.logging_config import configure_logging
from app.services.bot_handler import BotHandler
from app.services.telegram_service import TelegramService

configure_logging()
logger = logging.getLogger(__name__)


def main() -> None:
    Base.metadata.create_all(bind=engine)
    handler = BotHandler()
    telegram = TelegramService()
    offset = None

    logger.info("Starting Telegram polling mode")
    try:
        webhook_info = telegram.get_webhook_info()
        result = webhook_info.get("result", {})
        if result.get("url"):
            logger.info("Webhook detected for polling mode, deleting webhook first")
            telegram.delete_webhook(drop_pending_updates=False)
        logger.info("Telegram polling is ready")
    except Exception as exc:
        logger.warning("Could not verify Telegram webhook state: %s", exc)

    while True:
        try:
            payload = telegram.get_updates(offset=offset, timeout=20)
            updates = payload.get("result", [])
            if updates:
                logger.info("Received %s Telegram update(s)", len(updates))
            for update in updates:
                db = SessionLocal()
                try:
                    handler.handle_update(db, update)
                finally:
                    db.close()
                offset = update["update_id"] + 1
        except KeyboardInterrupt:
            logger.info("Polling stopped by user")
            break
        except Exception as exc:
            logger.warning("Polling error: %s", exc)
            time.sleep(5)


if __name__ == "__main__":
    main()
