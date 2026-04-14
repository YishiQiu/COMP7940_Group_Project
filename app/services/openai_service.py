import json
import logging
from typing import Any

from openai import OpenAI

from app.config import get_settings

logger = logging.getLogger(__name__)


class OpenAIService:
    def __init__(self) -> None:
        self.settings = get_settings()
        api_key = self.settings.effective_llm_api_key
        kwargs: dict[str, Any] = {"api_key": api_key} if api_key else {}
        if self.settings.llm_base_url:
            kwargs["base_url"] = self.settings.llm_base_url
        self.client = OpenAI(**kwargs) if api_key else None

    def summarize_stock_reply(self, user_message: str, quotes: list[dict[str, Any]]) -> str:
        if not quotes:
            return "I could not find market data for that symbol."

        if not self.client:
            return self._fallback_summary(quotes)

        system_prompt = (
            "You are a stock query assistant for a Telegram bot. "
            "Summarize the provided stock data in plain English. "
            "Keep it short, factual, and safe. "
            "Do not give financial advice. "
            "Always include a short risk reminder."
        )

        user_prompt = (
            f"User message: {user_message}\n"
            f"Market data JSON: {json.dumps(quotes, ensure_ascii=True)}\n"
            "Return a concise answer with 3 parts:\n"
            "1. quick summary\n"
            "2. key numbers\n"
            "3. risk reminder"
        )

        try:
            response = self.client.chat.completions.create(
                model=self.settings.effective_llm_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.2,
            )
            text = (response.choices[0].message.content or "").strip()
            return text or self._fallback_summary(quotes)
        except Exception as exc:
            logger.warning("OpenAI summary failed: %s", exc)
            return self._fallback_summary(quotes)

    def summarize_watchlist(self, quotes: list[dict[str, Any]]) -> str:
        if not quotes:
            return "Your watchlist is empty."
        return self.summarize_stock_reply("Summarize my watchlist today.", quotes)

    def _fallback_summary(self, quotes: list[dict[str, Any]]) -> str:
        lines = []
        for quote in quotes:
            lines.append(
                f"{quote['symbol']}: {quote['price']} {quote['currency']} "
                f"({quote['change']} / {quote['change_percent']}%)"
            )
        lines.append("Risk reminder: this bot is for information only, not investment advice.")
        return "\n".join(lines)
