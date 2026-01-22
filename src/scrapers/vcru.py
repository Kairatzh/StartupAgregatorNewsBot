from bs4 import BeautifulSoup
from datetime import datetime
from typing import List, Dict
from .base import BaseScraper
import re


class VCruScraper(BaseScraper):
    def __init__(self):
        super().__init__('VC.ru')
        self.urls = [
            'https://vc.ru/tribuna',
            'https://vc.ru/tag/startups'
        ]
    
    def scrape(self) -> List[Dict]:
        articles = []
        
        for url in self.urls:
            try:
                html = self.fetch_page(url)
                soup = BeautifulSoup(html, 'lxml')
                
                article_elements = soup.find_all('div', class_='feed__item')
                
                for article_elem in article_elements[:10]:
                    try:
                        title_elem = article_elem.find('a', class_='content-title')
                        if not title_elem:
                            continue
                        
                        title = title_elem.get_text(strip=True)
                        url = title_elem.get('href', '')
                        
                        if url.startswith('/'):
                            url = 'https://vc.ru' + url
                        
                        desc_elem = article_elem.find('div', class_='content-preview')
                        description = desc_elem.get_text(strip=True) if desc_elem else ''
                        
                        time_elem = article_elem.find('time')
                        published_date = None
                        if time_elem and time_elem.get('title'):
                            try:
                                date_str = time_elem.get('title', '')
                                published_date = datetime.utcnow()
                            except:
                                published_date = datetime.utcnow()
                        else:
                            published_date = datetime.utcnow()
                        
                        if title and url and url not in [a['url'] for a in articles]:
                            articles.append({
                                'title': title,
                                'url': url,
                                'description': description[:500] if description else '',
                                'published_date': published_date
                            })
                    except Exception as e:
                        print(f"Error parsing VC.ru article: {e}")
                        continue
            except Exception as e:
                print(f"Error fetching VC.ru page {url}: {e}")
                continue
        
        return articles


if __name__ == '__main__':
    scraper = VCruScraper()
    articles = scraper.safe_scrape()
    for article in articles[:3]:
        print(f"\nTitle: {article['title']}")
        print(f"URL: {article['url']}")
        print(f"Date: {article['published_date']}")
