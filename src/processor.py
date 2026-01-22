from datetime import datetime, timedelta
from typing import List, Dict
from sqlalchemy import and_
from src.models import NewsArticle, get_session


class NewsProcessor:
    PRIORITY_KEYWORDS = [
        'investment', 'funding', 'round', 'venture', 'capital', 'vc',
        'seed', 'series a', 'series b', 'series c', 'ipo', 'acquisition',
        'exit', 'merger', 'raised', 'million', 'billion',
        'breakthrough', 'innovation', 'launch', 'partnership',
        'инвестиции', 'финансирование', 'раунд', 'венчур',
        'стартап', 'проект', 'запуск', 'партнерство'
    ]
    
    def __init__(self):
        self.session = get_session()
    
    def calculate_keywords_score(self, text: str) -> float:
        if not text:
            return 0.0
        
        text_lower = text.lower()
        score = 0.0
        
        for keyword in self.PRIORITY_KEYWORDS:
            if keyword in text_lower:
                score += 1.0
        
        return score
    
    def is_duplicate(self, url: str, title: str) -> bool:
        existing = self.session.query(NewsArticle).filter_by(url=url).first()
        if existing:
            return True
        
        similar = self.session.query(NewsArticle).filter(
            NewsArticle.title == title
        ).first()
        
        return similar is not None
    
    def save_article(self, article_data: Dict, source: str, process_ai: bool = False) -> bool:
        if self.is_duplicate(article_data['url'], article_data['title']):
            return False
        
        combined_text = f"{article_data['title']} {article_data.get('description', '')}"
        keywords_score = self.calculate_keywords_score(combined_text)
        
        article = NewsArticle(
            title=article_data['title'],
            url=article_data['url'],
            description=article_data.get('description', ''),
            source=source,
            published_date=article_data.get('published_date', datetime.utcnow()),
            keywords_score=keywords_score
        )
        
        if process_ai:
            try:
                from src.ai.llm_manager import get_llm_manager
                from src.ai.summarizer import ArticleSummarizer
                from src.ai.sentiment import SentimentAnalyzer
                
                llm_manager = get_llm_manager()
                if llm_manager.is_enabled():
                    summarizer = ArticleSummarizer()
                    article.ai_summary = summarizer.summarize(
                        article.title, 
                        article.description or ""
                    )
                    
                    analyzer = SentimentAnalyzer()
                    article.sentiment_score = analyzer.analyze_sentiment(
                        article.title,
                        article.description or ""
                    )
                    
                    article.processed_by_ai = True
            except Exception as e:
                print(f"[AI] Processing error: {e}")
        
        self.session.add(article)
        self.session.commit()
        return True
    
    def process_scraped_articles(self, articles: List[Dict], source: str, enable_ai: bool = False) -> int:
        saved_count = 0
        
        for article in articles:
            try:
                if self.save_article(article, source, process_ai=enable_ai):
                    saved_count += 1
            except Exception as e:
                print(f"Error saving article: {e}")
                self.session.rollback()
                continue
        
        return saved_count
    
    def get_top_news(self, limit: int = 5, hours: int = 24) -> List[NewsArticle]:
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        articles = self.session.query(NewsArticle).filter(
            NewsArticle.published_date >= cutoff_time
        ).order_by(
            NewsArticle.keywords_score.desc(),
            NewsArticle.published_date.desc()
        ).limit(limit).all()
        
        if len(articles) < limit:
            additional = self.session.query(NewsArticle).filter(
                NewsArticle.published_date < cutoff_time
            ).order_by(
                NewsArticle.keywords_score.desc(),
                NewsArticle.published_date.desc()
            ).limit(limit - len(articles)).all()
            articles.extend(additional)
        
        return articles
    
    def close(self):
        self.session.close()


def process_all_sources(enable_ai: bool = None):
    from src.scrapers.techcrunch import TechCrunchScraper
    from src.scrapers.sifted import SiftedScraper
    from src.scrapers.vcru import VCruScraper
    from src.scrapers.rusbase import RusbaseScraper
    from src.scrapers.hackernews import HackerNewsScraper
    
    if enable_ai is None:
        from src.ai.llm_manager import get_llm_manager
        enable_ai = get_llm_manager().is_enabled()
    
    if enable_ai:
        print("[AI] AI processing enabled for new articles")
    
    processor = NewsProcessor()
    total_saved = 0
    
    scrapers = [
        (TechCrunchScraper(), 'techcrunch'),
        (SiftedScraper(), 'sifted'),
        (VCruScraper(), 'vcru'),
        (RusbaseScraper(), 'rusbase'),
        (HackerNewsScraper(), 'hackernews')
    ]
    
    print("Starting news aggregation...")
    
    for scraper, source_name in scrapers:
        print(f"\n[*] Scraping {source_name}...")
        articles = scraper.safe_scrape()
        saved = processor.process_scraped_articles(articles, source_name, enable_ai=enable_ai)
        total_saved += saved
        print(f"   Saved {saved} new articles from {source_name}")
    
    print(f"\n[DONE] Total: {total_saved} new articles saved")
    processor.close()
    
    return total_saved


if __name__ == '__main__':
    process_all_sources()
