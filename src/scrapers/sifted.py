from bs4 import BeautifulSoup
from datetime import datetime
from typing import List, Dict
from .base import BaseScraper
import re


class SiftedScraper(BaseScraper):
    def __init__(self):
        super().__init__('Sifted')
        self.base_url = 'https://sifted.eu/'
    
    def scrape(self) -> List[Dict]:
        html = self.fetch_page(self.base_url)
        soup = BeautifulSoup(html, 'lxml')
        articles = []
        
        article_elements = soup.find_all('article')
        
        for article_elem in article_elements[:20]:
            try:
                title_elem = article_elem.find('h2') or article_elem.find('h3')
                if not title_elem:
                    continue
                
                link_elem = title_elem.find('a')
                if not link_elem:
                    continue
                
                title = title_elem.get_text(strip=True)
                url = link_elem.get('href', '')
                
                if url.startswith('/'):
                    url = 'https://sifted.eu' + url
                
                desc_elem = article_elem.find('p')
                description = desc_elem.get_text(strip=True) if desc_elem else ''
                
                time_elem = article_elem.find('time')
                published_date = None
                if time_elem and time_elem.get('datetime'):
                    try:
                        published_date = datetime.fromisoformat(time_elem['datetime'].replace('Z', '+00:00'))
                    except:
                        published_date = datetime.utcnow()
                else:
                    published_date = datetime.utcnow()
                
                if title and url:
                    articles.append({
                        'title': title,
                        'url': url,
                        'description': description[:500] if description else '',
                        'published_date': published_date
                    })
            except Exception as e:
                print(f"Error parsing Sifted article: {e}")
                continue
        
        return articles


if __name__ == '__main__':
    scraper = SiftedScraper()
    articles = scraper.safe_scrape()
    for article in articles[:3]:
        print(f"\nTitle: {article['title']}")
        print(f"URL: {article['url']}")
        print(f"Date: {article['published_date']}")
