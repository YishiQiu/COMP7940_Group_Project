import csv
import logging
from datetime import datetime, timezone
from io import StringIO
from typing import Any

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)


class StockServiceError(Exception):
    pass


class StockService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.default_headers = {
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            "Accept": "application/json,text/plain,*/*",
        }

    def get_quotes(self, symbols: list[str]) -> list[dict[str, Any]]:
        if not symbols:
            return []

        normalized_symbols = [symbol.upper() for symbol in symbols]

        if self.settings.twelve_data_api_key:
            try:
                quotes = self._get_quotes_from_twelve_data(normalized_symbols)
                if quotes:
                    return quotes
            except httpx.HTTPStatusError as exc:
                logger.warning("Twelve Data HTTP error, falling back: %s", exc)
            except Exception as exc:
                logger.warning("Twelve Data request failed, falling back: %s", exc)

        try:
            quotes = self._get_quotes_from_yahoo(normalized_symbols)
            if quotes:
                return quotes
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 429:
                logger.warning("Yahoo Finance rate-limited the request, falling back: %s", exc)
            else:
                logger.warning("Yahoo Finance HTTP error, falling back: %s", exc)
        except Exception as exc:
            logger.warning("Yahoo Finance request failed, falling back: %s", exc)

        fallback_quotes = self._get_quotes_from_stooq(normalized_symbols)
        if fallback_quotes:
            return fallback_quotes

        raise StockServiceError("Stock data providers are temporarily unavailable.")

    def _get_quotes_from_twelve_data(self, symbols: list[str]) -> list[dict[str, Any]]:
        parsed: list[dict[str, Any]] = []
        with httpx.Client(timeout=self.settings.request_timeout_seconds, headers=self.default_headers) as client:
            for symbol in symbols:
                response = client.get(
                    f"{self.settings.twelve_data_base_url.rstrip('/')}/quote",
                    params={
                        "symbol": symbol,
                        "apikey": self.settings.twelve_data_api_key,
                        "interval": "1min",
                    },
                )
                response.raise_for_status()
                payload = response.json()
                if payload.get("code"):
                    raise StockServiceError(
                        f"Twelve Data error {payload.get('code')}: {payload.get('message', 'Unknown error')}"
                    )
                quote = self._parse_twelve_data_quote(payload)
                if quote:
                    parsed.append(quote)
        return parsed

    def _get_quotes_from_yahoo(self, symbols: list[str]) -> list[dict[str, Any]]:
        url = f"{self.settings.stock_api_base_url.rstrip('/')}/v7/finance/quote"
        with httpx.Client(timeout=self.settings.request_timeout_seconds, headers=self.default_headers) as client:
            response = client.get(url, params={"symbols": ",".join(symbols)})
            response.raise_for_status()
            payload = response.json()

        results = payload.get("quoteResponse", {}).get("result", [])
        return [self._parse_yahoo_quote(item) for item in results if item.get("symbol")]

    def _get_quotes_from_stooq(self, symbols: list[str]) -> list[dict[str, Any]]:
        parsed: list[dict[str, Any]] = []
        with httpx.Client(timeout=self.settings.request_timeout_seconds, headers=self.default_headers) as client:
            for symbol in symbols:
                stooq_symbol = self._to_stooq_symbol(symbol)
                url = "https://stooq.com/q/l/"
                response = client.get(url, params={"s": stooq_symbol, "f": "sd2t2ohlcvn", "h": "", "e": "csv"})
                response.raise_for_status()
                quote = self._parse_stooq_csv(symbol, response.text)
                if quote:
                    parsed.append(quote)
        return parsed

    def _parse_yahoo_quote(self, item: dict[str, Any]) -> dict[str, Any]:
        market_time = item.get("regularMarketTime")
        query_time = None
        if market_time:
            query_time = datetime.fromtimestamp(market_time, tz=timezone.utc).isoformat()

        return {
            "symbol": item.get("symbol", ""),
            "name": item.get("shortName") or item.get("longName") or item.get("symbol", ""),
            "price": item.get("regularMarketPrice"),
            "change": item.get("regularMarketChange"),
            "change_percent": item.get("regularMarketChangePercent"),
            "currency": item.get("currency"),
            "exchange": item.get("fullExchangeName") or item.get("exchange"),
            "market_state": item.get("marketState"),
            "query_time": query_time,
        }

    def _parse_twelve_data_quote(self, item: dict[str, Any]) -> dict[str, Any] | None:
        symbol = item.get("symbol")
        close_value = self._to_float(item.get("close"))
        if not symbol or close_value is None:
            return None

        percent_change = self._to_float(item.get("percent_change"))
        change_value = self._to_float(item.get("change"))
        query_time = None
        dt = item.get("datetime")
        if isinstance(dt, str) and dt:
            query_time = dt.replace(" ", "T")

        return {
            "symbol": symbol,
            "name": item.get("name") or symbol,
            "price": close_value,
            "change": change_value,
            "change_percent": percent_change,
            "currency": item.get("currency") or "USD",
            "exchange": item.get("exchange") or item.get("mic_code") or "Twelve Data",
            "market_state": item.get("is_market_open"),
            "query_time": query_time,
        }

    def _parse_stooq_csv(self, requested_symbol: str, csv_text: str) -> dict[str, Any] | None:
        reader = csv.DictReader(StringIO(csv_text))
        row = next(reader, None)
        if not row:
            return None

        close_value = row.get("Close")
        if not close_value or close_value in {"N/D", "0"}:
            return None

        date_value = row.get("Date")
        time_value = row.get("Time")
        query_time = None
        if date_value and time_value and date_value != "N/D" and time_value != "N/D":
            query_time = f"{date_value}T{time_value}"
        elif date_value and date_value != "N/D":
            query_time = date_value

        return {
            "symbol": requested_symbol,
            "name": row.get("Name") or requested_symbol,
            "price": self._to_float(close_value),
            "change": None,
            "change_percent": None,
            "currency": "USD",
            "exchange": "Stooq",
            "market_state": "DELAYED",
            "query_time": query_time,
        }

    def _to_stooq_symbol(self, symbol: str) -> str:
        if "." in symbol:
            return symbol.lower()
        return f"{symbol.lower()}.us"

    def _to_float(self, value: str | None) -> float | None:
        if not value or value == "N/D":
            return None
        try:
            return float(value)
        except ValueError:
            return None
