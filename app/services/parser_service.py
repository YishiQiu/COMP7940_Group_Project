import re
from dataclasses import dataclass


WATCHLIST_SHOW_TERMS = ("watchlist", "my list", "show list", "tracked stocks")
WATCHLIST_SUMMARY_TERMS = ("watchlist summary", "summarize watchlist", "summary of my watchlist")

COMPANY_ALIASES = {
    "apple": "AAPL",
    "tesla": "TSLA",
    "nvidia": "NVDA",
    "microsoft": "MSFT",
    "amazon": "AMZN",
    "google": "GOOGL",
    "alphabet": "GOOGL",
    "meta": "META",
    "netflix": "NFLX",
}

STOPWORDS = {
    "TODAY",
    "WHAT",
    "WITH",
    "ABOUT",
    "PLEASE",
    "STOCK",
    "PRICE",
    "QUERY",
    "COMPARE",
    "CHECK",
    "HELP",
    "LIST",
    "ADD",
    "REMOVE",
    "WATCHLIST",
    "SUMMARY",
}


@dataclass
class ParsedCommand:
    intent: str
    symbols: list[str]
    normalized_text: str


def parse_user_message(text: str) -> ParsedCommand:
    raw = (text or "").strip()
    lowered = raw.lower()
    symbols = extract_symbols(raw)

    if raw.startswith("/start"):
        return ParsedCommand(intent="start", symbols=[], normalized_text=raw)
    if raw.startswith("/help"):
        return ParsedCommand(intent="help", symbols=[], normalized_text=raw)
    if raw.startswith("/add"):
        return ParsedCommand(intent="add_watchlist", symbols=_extract_command_symbols(raw), normalized_text=raw)
    if raw.startswith("/remove"):
        return ParsedCommand(intent="remove_watchlist", symbols=_extract_command_symbols(raw), normalized_text=raw)
    if raw.startswith("/watchlist"):
        return ParsedCommand(intent="show_watchlist", symbols=[], normalized_text=raw)
    if raw.startswith("/summary"):
        return ParsedCommand(intent="summary_watchlist", symbols=[], normalized_text=raw)

    if any(term in lowered for term in WATCHLIST_SUMMARY_TERMS):
        return ParsedCommand(intent="summary_watchlist", symbols=symbols, normalized_text=raw)

    if any(term in lowered for term in WATCHLIST_SHOW_TERMS):
        return ParsedCommand(intent="show_watchlist", symbols=symbols, normalized_text=raw)

    if ("add" in lowered or "track" in lowered) and symbols:
        return ParsedCommand(intent="add_watchlist", symbols=symbols, normalized_text=raw)

    if ("remove" in lowered or "delete" in lowered or "untrack" in lowered) and symbols:
        return ParsedCommand(intent="remove_watchlist", symbols=symbols, normalized_text=raw)

    if symbols:
        return ParsedCommand(intent="stock_query", symbols=symbols[:2], normalized_text=raw)

    return ParsedCommand(intent="unknown", symbols=[], normalized_text=raw)


def extract_symbols(text: str) -> list[str]:
    lowered = text.lower()
    resolved = [symbol for name, symbol in COMPANY_ALIASES.items() if name in lowered]
    uppercase_hits = re.findall(r"\b[A-Z]{1,5}\b", text)
    for token in uppercase_hits:
        candidate = token.upper()
        if candidate not in STOPWORDS:
            resolved.append(candidate)

    deduped: list[str] = []
    for item in resolved:
        if item not in deduped:
            deduped.append(item)
    return deduped


def _extract_command_symbols(text: str) -> list[str]:
    parts = text.split()
    if len(parts) < 2:
        return []
    candidate = parts[1].strip().upper()
    if re.fullmatch(r"[A-Z]{1,5}", candidate):
        return [candidate]
    return []
