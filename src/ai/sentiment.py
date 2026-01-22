
from typing import Optional, List
from langchain.prompts import ChatPromptTemplate
from langchain.callbacks import get_openai_callback
from src.ai.llm_manager import get_llm_manager
from src.models import NewsArticle


class SentimentAnalyzer:
    
    def __init__(self):
        self.llm_manager = get_llm_manager()
        self.llm = self.llm_manager.get_llm(temperature=0.1)  
        
        self.sentiment_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a financial sentiment analyst. Analyze the sentiment of startup/tech news.

Return ONLY a single number between -1 and 1:
- Negative news (layoffs, failures, down rounds): -1 to -0.3
- Neutral news (announcements, updates): -0.3 to 0.3
- Positive news (funding, growth, success): 0.3 to 1

Be objective and data-driven."""),
            ("user", """Title: {title}
Description: {description}

Sentiment score:""")
        ])
        
        self.overview_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a market analyst. Summarize overall market sentiment from multiple news articles.

Provide:
1. Overall sentiment (Positive/Neutral/Negative)
2. Key factors driving sentiment
3. Notable outliers

Be concise (3-4 sentences)."""),
            ("user", """Analyze overall sentiment from these articles with scores:

{articles_with_sentiment}

Market sentiment overview:""")
        ])
    
    def analyze_sentiment(self, title: str, description: str) -> Optional[float]:
        if not self.llm_manager.is_enabled() or not self.llm:
            return None
        
        try:
            with get_openai_callback() as cb:
                chain = self.sentiment_prompt | self.llm
                result = chain.invoke({
                    "title": title,
                    "description": description[:500]
                })
                
                self.llm_manager.track_usage(cb.total_tokens)
                
                content = result.content.strip() if hasattr(result, 'content') else str(result).strip()
                
                try:
                    score = float(content.split()[0])  
                    return max(-1.0, min(1.0, score)) 
                except:
                    return 0.0  
                    
        except Exception as e:
            print(f"[AI] Sentiment analysis error: {e}")
            return None
    
    def get_market_overview(self, articles: List[NewsArticle]) -> Optional[str]:
        if not self.llm_manager.is_enabled() or not self.llm or not articles:
            return None
        
        try:
            articles_text = []
            for article in articles[:15]:  
                score = article.sentiment_score or 0.0
                sentiment_label = self._score_to_label(score)
                articles_text.append(
                    f"[{sentiment_label}] {article.title} (score: {score:.2f})"
                )
            
            with get_openai_callback() as cb:
                chain = self.overview_prompt | self.llm
                result = chain.invoke({
                    "articles_with_sentiment": "\n".join(articles_text)
                })
                
                self.llm_manager.track_usage(cb.total_tokens)
                
                if hasattr(result, 'content'):
                    return result.content.strip()
                return str(result).strip()
                
        except Exception as e:
            print(f"[AI] Market overview error: {e}")
            return None
    
    def _score_to_label(self, score: float) -> str:
        if score >= 0.3:
            return "POSITIVE"
        elif score <= -0.3:
            return "NEGATIVE"
        else:
            return "NEUTRAL"
    
    def get_sentiment_stats(self, articles: List[NewsArticle]) -> dict:
        if not articles:
            return {}
        
        scores = [a.sentiment_score for a in articles if a.sentiment_score is not None]
        
        if not scores:
            return {}
        
        avg_score = sum(scores) / len(scores)
        positive_count = sum(1 for s in scores if s >= 0.3)
        negative_count = sum(1 for s in scores if s <= -0.3)
        neutral_count = len(scores) - positive_count - negative_count
        
        return {
            'average_score': avg_score,
            'total_articles': len(scores),
            'positive': positive_count,
            'neutral': neutral_count,
            'negative': negative_count,
            'overall_sentiment': self._score_to_label(avg_score)
        }


if __name__ == '__main__':
    analyzer = SentimentAnalyzer()
    
    test_articles = [
        {
            'title': 'Startup Raises $100M Series B',
            'description': 'FastGrow announced a massive $100M Series B led by top VCs, signaling strong market confidence.'
        },
        {
            'title': 'Tech Company Announces Layoffs',
            'description': 'SlowTech lays off 30% of workforce amid challenging market conditions and reduced funding.'
        },
        {
            'title': 'New Product Launch',
            'description': 'TechCorp announces  release of new SaaS platform for enterprises.'
        }
    ]
    
    for article in test_articles:
        score = analyzer.analyze_sentiment(article['title'], article['description'])
        if score is not None:
            print(f"\nTitle: {article['title']}")
            print(f"Sentiment: {analyzer._score_to_label(score)} ({score:.2f})")
        else:
            print("\nAI features disabled")
            break
