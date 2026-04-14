import json
import logging
from typing import Any

from sqlalchemy.orm import Session

from app.metrics import TELEGRAM_MESSAGES
from app.models import QueryLog, User
from app.services.openai_service import OpenAIService
from app.services.parser_service import ParsedCommand, parse_user_message
from app.services.stock_service import StockService, StockServiceError
from app.services.telegram_service import TelegramService
from app.services.watchlist_service import WatchlistService

logger = logging.getLogger(__name__)


class BotHandler:
    def __init__(self) -> None:
        self.stock_service = StockService()
        self.openai_service = OpenAIService()
        self.telegram_service = TelegramService()
        self.watchlist_service = WatchlistService()

    def handle_update(self, db: Session, update: dict[str, Any]) -> None:
        message = update.get("message") or update.get("edited_message")
        if not message:
            return

        text = (message.get("text") or "").strip()
        chat = message.get("chat") or {}
        from_user = message.get("from") or {}
        chat_id = chat.get("id")

        if not text or not chat_id:
            return

        user = self._get_or_create_user(db, from_user)
        command = parse_user_message(text)

        try:
            reply = self._dispatch(db, user, command, text)
            self.telegram_service.send_message(chat_id=chat_id, text=reply)
            TELEGRAM_MESSAGES.labels(intent=command.intent, status="success").inc()
        except Exception as exc:
            logger.exception("Failed to process update")
            self._log_query(
                db=db,
                user_id=user.id if user else None,
                intent=command.intent,
                user_message=text,
                symbols=command.symbols,
                market_data=None,
                llm_reply=None,
                status="error",
                error_message=str(exc),
            )
            TELEGRAM_MESSAGES.labels(intent=command.intent, status="error").inc()
            self.telegram_service.send_message(
                chat_id=chat_id,
                text="Something went wrong while processing your request. Please try again.",
            )

    def _dispatch(self, db: Session, user: User, command: ParsedCommand, text: str) -> str:
        if command.intent == "start":
            reply = self._start_message()
            self._log_query(db, user.id, command.intent, text, [], None, reply)
            return reply

        if command.intent == "help":
            reply = self._help_message()
            self._log_query(db, user.id, command.intent, text, [], None, reply)
            return reply

        if command.intent == "add_watchlist":
            if not command.symbols:
                reply = "Use /add AAPL to add a stock to your watchlist."
            else:
                added = self.watchlist_service.add_symbol(db, user.id, command.symbols[0])
                reply = (
                    f"Added {command.symbols[0]} to your watchlist."
                    if added
                    else f"{command.symbols[0]} is already in your watchlist."
                )
            self._log_query(db, user.id, command.intent, text, command.symbols, None, reply)
            return reply

        if command.intent == "remove_watchlist":
            if not command.symbols:
                reply = "Use /remove AAPL to remove a stock from your watchlist."
            else:
                removed = self.watchlist_service.remove_symbol(db, user.id, command.symbols[0])
                reply = (
                    f"Removed {command.symbols[0]} from your watchlist."
                    if removed
                    else f"{command.symbols[0]} was not in your watchlist."
                )
            self._log_query(db, user.id, command.intent, text, command.symbols, None, reply)
            return reply

        if command.intent == "show_watchlist":
            symbols = self.watchlist_service.list_symbols(db, user.id)
            reply = (
                "Your watchlist is empty."
                if not symbols
                else "Your watchlist:\n" + "\n".join(f"- {symbol}" for symbol in symbols)
            )
            self._log_query(db, user.id, command.intent, text, symbols, None, reply)
            return reply

        if command.intent == "summary_watchlist":
            symbols = self.watchlist_service.list_symbols(db, user.id)
            try:
                quotes = self.stock_service.get_quotes(symbols) if symbols else []
                reply = self.openai_service.summarize_watchlist(quotes)
            except StockServiceError:
                quotes = []
                reply = "The stock data provider is temporarily busy. Please try your watchlist summary again later."
            self._log_query(db, user.id, command.intent, text, symbols, quotes, reply)
            return reply

        if command.intent == "stock_query":
            try:
                quotes = self.stock_service.get_quotes(command.symbols)
                if not quotes:
                    reply = "I could not find that stock. Try a symbol like AAPL, TSLA, NVDA, or MSFT."
                else:
                    reply = self._format_quote_block(quotes) + "\n\n" + self.openai_service.summarize_stock_reply(
                        text, quotes
                    )
            except StockServiceError:
                quotes = []
                reply = "The stock data provider is temporarily busy. Please try again in a minute."
            self._log_query(db, user.id, command.intent, text, command.symbols, quotes, reply)
            return reply

        reply = self._help_message()
        self._log_query(db, user.id, command.intent, text, command.symbols, None, reply)
        return reply

    def _get_or_create_user(self, db: Session, from_user: dict[str, Any]) -> User:
        telegram_user_id = from_user.get("id")
        if telegram_user_id is None:
            raise ValueError("Missing Telegram user id")

        user = db.query(User).filter(User.telegram_user_id == telegram_user_id).first()
        if user:
            if from_user.get("username") and user.username != from_user.get("username"):
                user.username = from_user.get("username")
            if from_user.get("first_name") and user.first_name != from_user.get("first_name"):
                user.first_name = from_user.get("first_name")
            db.commit()
            return user

        user = User(
            telegram_user_id=telegram_user_id,
            username=from_user.get("username"),
            first_name=from_user.get("first_name"),
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    def _log_query(
        self,
        db: Session,
        user_id: int | None,
        intent: str,
        user_message: str,
        symbols: list[str],
        market_data: list[dict[str, Any]] | None,
        llm_reply: str | None,
        status: str = "success",
        error_message: str | None = None,
    ) -> None:
        log = QueryLog(
            user_id=user_id,
            intent=intent,
            user_message=user_message,
            detected_symbols=json.dumps(symbols),
            market_data=json.dumps(market_data) if market_data is not None else None,
            llm_reply=llm_reply,
            status=status,
            error_message=error_message,
        )
        db.add(log)
        db.commit()

    def _format_quote_block(self, quotes: list[dict[str, Any]]) -> str:
        sections = []
        for quote in quotes:
            sections.append(
                "\n".join(
                    [
                        f"{quote['name']} ({quote['symbol']})",
                        f"Price: {quote['price']} {quote['currency']}",
                        f"Change: {quote['change']} ({quote['change_percent']}%)",
                        f"Exchange: {quote['exchange']}",
                        f"Market state: {quote['market_state']}",
                        f"Query time: {quote['query_time']}",
                    ]
                )
            )
        return "\n\n".join(sections)

    def _start_message(self) -> str:
        return (
            "Welcome to Telegram Stock Query Assistant.\n\n"
            "Try:\n"
            "- AAPL today\n"
            "- Compare AAPL and MSFT\n"
            "- /add NVDA\n"
            "- /watchlist\n"
            "- /summary\n"
            "- /help"
        )

    def _help_message(self) -> str:
        return (
            "Commands:\n"
            "/start - start the bot\n"
            "/help - show help\n"
            "/add AAPL - add a stock to your watchlist\n"
            "/remove AAPL - remove a stock from your watchlist\n"
            "/watchlist - show your watchlist\n"
            "/summary - summarize your watchlist\n\n"
            "You can also type stock questions such as:\n"
            "- AAPL today\n"
            "- Compare TSLA and NVDA\n"
            "- How is Microsoft stock doing?"
        )
