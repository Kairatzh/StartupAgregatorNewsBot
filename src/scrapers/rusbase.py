from bs4 import BeautifulSoup
from datetime import datetime
from typing import List, Dict
from .base import BaseScraper
import re


class RusbaseScraper(BaseScraper):
    def __init__(self):
        super().__init__('Rusbase')
        self.base_url = 'https://rb.ru/'
    
    def scrape(self) -> List[Dict]:
        html = self.fetch_page(self.base_url)
        soup = BeautifulSoup(html, 'lxml')
        articles = []
        
        article_elements = soup.find_all(['article', 'div'], class_=re.compile('article|post|news'))
        
        for article_elem in article_elements[:20]:
            try:
                title_elem = (article_elem.find('h2') or 
                             article_elem.find('h3') or 
                             article_elem.find('a', class_=re.compile('title|headline')))
                
                if not title_elem:
                    continue
                
                title = title_elem.get_text(strip=True)
                
                link_elem = title_elem if title_elem.name == 'a' else title_elem.find('a')
                if not link_elem:
                    continue
                
                url = link_elem.get('href', '')
                
                if url.startswith('/'):
                    url = 'https://rb.ru' + url
                
                desc_elem = article_elem.find(['p', 'div'], class_=re.compile('description|excerpt|preview'))
                description = desc_elem.get_text(strip=True) if desc_elem else ''
                
                time_elem = article_elem.find('time')
                published_date = None
                if time_elem:
                    datetime_attr = time_elem.get('datetime') or time_elem.get('data-time')
                    if datetime_attr:
                        try:
                            published_date = datetime.fromisoformat(datetime_attr.replace('Z', '+00:00'))
                        except:
                            published_date = datetime.utcnow()
                    else:
                        published_date = datetime.utcnow()
                else:
                    published_date = datetime.utcnow()
                
                if title and url and len(title) > 10:
                    articles.append({
                        'title': title,
                        'url': url,
                        'description': description[:500] if description else '',
                        'published_date': published_date
                    })
            except Exception as e:
                print(f"Error parsing Rusbase article: {e}")
                continue
        
        return articles


if __name__ == '__main__':
    scraper = RusbaseScraper()
    articles = scraper.safe_scrape()
    for article in articles[:3]:
        print(f"\nTitle: {article['title']}")
        print(f"URL: {article['url']}")
        print(f"Date: {article['published_date']}")
