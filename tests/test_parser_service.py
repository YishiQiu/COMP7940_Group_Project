import unittest

from app.services.parser_service import extract_symbols, parse_user_message


class ParserServiceTests(unittest.TestCase):
    def test_extract_symbols_from_company_name(self):
        self.assertEqual(extract_symbols("How is Apple stock doing today?"), ["AAPL"])

    def test_extract_symbols_from_tickers(self):
        self.assertEqual(extract_symbols("Compare AAPL and MSFT"), ["AAPL", "MSFT"])

    def test_parse_add_watchlist(self):
        parsed = parse_user_message("/add nvda")
        self.assertEqual(parsed.intent, "add_watchlist")
        self.assertEqual(parsed.symbols, ["NVDA"])

    def test_parse_watchlist_summary(self):
        parsed = parse_user_message("summarize watchlist")
        self.assertEqual(parsed.intent, "summary_watchlist")


if __name__ == "__main__":
    unittest.main()
