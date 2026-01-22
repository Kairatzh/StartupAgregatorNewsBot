from datetime import datetime
from typing import List, Dict
from .base import BaseScraper
import requests


class HackerNewsScraper(BaseScraper):
    def __init__(self):
        super().__init__('Hacker News')
        self.api_base = 'https://hacker-news.firebaseio.com/v0'
        self.startup_keywords = [
            'startup', 'funding', 'investment', 'venture', 'vc', 
            'seed round', 'series a', 'series b', 'ipo', 'acquisition',
            'yc', 'y combinator', 'techstars'
        ]
    
    def scrape(self) -> List[Dict]:
        try:
            response = requests.get(f'{self.api_base}/topstories.json', timeout=10)
            response.raise_for_status()
            story_ids = response.json()[:50]  
            
            articles = []
            
            for story_id in story_ids:
                try:
                    story_response = requests.get(f'{self.api_base}/item/{story_id}.json', timeout=5)
                    story_response.raise_for_status()
                    story = story_response.json()
                    
                    if not story or story.get('type') != 'story':
                        continue
                    
                    title = story.get('title', '')
                    url = story.get('url', f'https://news.ycombinator.com/item?id={story_id}')
                    
                    title_lower = title.lower()
                    if not any(keyword in title_lower for keyword in self.startup_keywords):
                        continue
                    
                    timestamp = story.get('time', None)
                    published_date = datetime.fromtimestamp(timestamp) if timestamp else datetime.utcnow()
                    
                    description = story.get('text', '')[:500] if story.get('text') else ''
                    
                    articles.append({
                        'title': title,
                        'url': url,
                        'description': description,
                        'published_date': published_date
                    })
                    
                    if len(articles) >= 10:  
                        break
                        
                except Exception as e:
                    print(f"Error fetching HN story {story_id}: {e}")
                    continue
            
            return articles
            
        except Exception as e:
            print(f"Error fetching HN top stories: {e}")
            return []


if __name__ == '__main__':
    scraper = HackerNewsScraper()
    articles = scraper.safe_scrape()
    for article in articles[:3]:
        print(f"\nTitle: {article['title']}")
        print(f"URL: {article['url']}")
        print(f"Date: {article['published_date']}")
