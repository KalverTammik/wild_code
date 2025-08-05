import requests

class BookQuoteLogic:
    """Logic for fetching book quotes."""
    QUOTE_API_URL = "https://zenquotes.io/api/random"
    HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}

    @staticmethod
    def fetch_quote():
        try:
            response = requests.get(BookQuoteLogic.QUOTE_API_URL, headers=BookQuoteLogic.HEADERS, timeout=10)
            response.raise_for_status()
            if "application/json" not in response.headers.get("Content-Type", ""):
                raise ValueError("Invalid content type from quote API. Expected JSON.")
            data = response.json()
            if not isinstance(data, list) or not data:
                raise ValueError("Invalid response format from quote API.")
            content = data[0].get("q", "No quote available.")
            author = data[0].get("a", "Unknown Author")
            return content, author, None
        except Exception as e:
            return None, None, str(e)
