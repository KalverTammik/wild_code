"""
PriceCache: Handles local price caching for suppliers (mock implementation)
"""
import json
import os

class PriceCache:
    CACHE_FILE = os.path.join(os.path.dirname(__file__), '../data/price_cache.json')

    @staticmethod
    def load_prices():
        if os.path.exists(PriceCache.CACHE_FILE):
            with open(PriceCache.CACHE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}

    @staticmethod
    def save_prices(data):
        with open(PriceCache.CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
