import html
from typing import Any

import httpx

from app.config import get_settings


class TelegramService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.base_url = f"https://api.telegram.org/bot{self.settings.telegram_bot_token}"

    def send_message(self, chat_id: int, text: str) -> dict[str, Any]:
        escaped_text = html.escape(text)
        payload = {
            "chat_id": chat_id,
            "text": escaped_text,
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        }
        with httpx.Client(timeout=self.settings.request_timeout_seconds) as client:
            response = client.post(f"{self.base_url}/sendMessage", json=payload)
            return self._parse_response(response)

    def set_webhook(self) -> dict[str, Any] | None:
        if not self.settings.webhook_url or not self.settings.telegram_bot_token:
            return None
        payload = {
            "url": self.settings.webhook_url,
            "secret_token": self.settings.telegram_webhook_secret_token,
        }
        with httpx.Client(timeout=self.settings.request_timeout_seconds) as client:
            response = client.post(f"{self.base_url}/setWebhook", json=payload)
            return self._parse_response(response)

    def delete_webhook(self, drop_pending_updates: bool = False) -> dict[str, Any]:
        payload = {"drop_pending_updates": drop_pending_updates}
        with httpx.Client(timeout=self.settings.request_timeout_seconds) as client:
            response = client.post(f"{self.base_url}/deleteWebhook", json=payload)
            return self._parse_response(response)

    def get_webhook_info(self) -> dict[str, Any]:
        with httpx.Client(timeout=self.settings.request_timeout_seconds) as client:
            response = client.get(f"{self.base_url}/getWebhookInfo")
            return self._parse_response(response)

    def get_updates(self, offset: int | None = None, timeout: int = 20) -> dict[str, Any]:
        params: dict[str, Any] = {"timeout": timeout}
        if offset is not None:
            params["offset"] = offset
        with httpx.Client(timeout=timeout + 5) as client:
            response = client.get(f"{self.base_url}/getUpdates", params=params)
            return self._parse_response(response)

    def _parse_response(self, response: httpx.Response) -> dict[str, Any]:
        response.raise_for_status()
        payload = response.json()
        if not payload.get("ok", False):
            description = payload.get("description", "Unknown Telegram API error")
            error_code = payload.get("error_code", "unknown")
            raise RuntimeError(f"Telegram API error {error_code}: {description}")
        return payload
