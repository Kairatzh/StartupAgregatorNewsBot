from abc import ABC, abstractmethod
from typing import List, Dict
import time
import requests
from datetime import datetime


class BaseScraper(ABC):
    
    def __init__(self, source_name: str):
        self.source_name = source_name
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        self.timeout = 10
        self.max_retries = 3
    
    @abstractmethod
    def scrape(self) -> List[Dict]:
        pass
    
    def fetch_page(self, url: str) -> str:
        for attempt in range(self.max_retries):
            try:
                response = requests.get(url, headers=self.headers, timeout=self.timeout)
                response.raise_for_status()
                return response.text
            except requests.RequestException as e:
                if attempt == self.max_retries - 1:
                    print(f"Failed to fetch {url} after {self.max_retries} attempts: {e}")
                    raise
                time.sleep(2 ** attempt) 
        return ""
    
    def safe_scrape(self) -> List[Dict]:
        try:
            articles = self.scrape()
            print(f"[OK] {self.source_name}: Successfully scraped {len(articles)} articles")
            return articles
        except Exception as e:
            print(f"[ERROR] {self.source_name}: Error during scraping - {e}")
            return []
