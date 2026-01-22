
from typing import List, Optional
from langchain.prompts import ChatPromptTemplate
from langchain.callbacks import get_openai_callback
from src.ai.llm_manager import get_llm_manager
from src.models import NewsArticle


class InsightsGenerator:
    
    def __init__(self):
        self.llm_manager = get_llm_manager()
        self.llm = self.llm_manager.get_llm(temperature=0.5)
        
        self.insights_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a venture capital analyst. Analyze startup news and identify key insights.

Focus on:
- Funding trends (rounds, amounts, investors)
- Emerging sectors/technologies
- Notable acquisitions or exits
- Market patterns

Be concise and data-driven."""),
            ("user", """Analyze these startup news articles and provide key insights:

{articles_text}

Provide 5-7 key insights in bullet points:""")
        ])
        
        self.trends_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a market analyst. Identify trending topics and patterns in startup news.

Highlight:
- Hot sectors/technologies
- Funding patterns
- Geographic trends
- Emerging companies

Be specific and actionable."""),
            ("user", """Identify trending topics from these articles:

{articles_text}

Provide 3-5 trending topics with brief explanations:""")
        ])
    
    def generate_insights(self, articles: List[NewsArticle]) -> Optional[str]:
        """
        Generate insights from recent articles.
        
        Args:
            articles: List of NewsArticle objects
            
        Returns:
            AI-generated insights or None
        """
        if not self.llm_manager.is_enabled() or not self.llm or not articles:
            return None
        
        try:
            articles_text = self._format_articles_for_llm(articles)
            
            with get_openai_callback() as cb:
                chain = self.insights_prompt | self.llm
                result = chain.invoke({"articles_text": articles_text})
                
                self.llm_manager.track_usage(cb.total_tokens)
                
                if hasattr(result, 'content'):
                    return result.content.strip()
                return str(result).strip()
                
        except Exception as e:
            print(f"[AI] Insights generation error: {e}")
            return None
    
    def analyze_trends(self, articles: List[NewsArticle]) -> Optional[str]:
        if not self.llm_manager.is_enabled() or not self.llm or not articles:
            return None
        
        try:
            articles_text = self._format_articles_for_llm(articles)
            
            with get_openai_callback() as cb:
                chain = self.trends_prompt | self.llm
                result = chain.invoke({"articles_text": articles_text})
                
                self.llm_manager.track_usage(cb.total_tokens)
                
                if hasattr(result, 'content'):
                    return result.content.strip()
                return str(result).strip()
                
        except Exception as e:
            print(f"[AI] Trend analysis error: {e}")
            return None
    
    def _format_articles_for_llm(self, articles: List[NewsArticle], max_articles: int = 20) -> str:
        formatted = []
        
        for i, article in enumerate(articles[:max_articles], 1):
            text = f"{i}. [{article.source.upper()}] {article.title}"
            if article.description:
                text += f"\n   {article.description[:200]}"
            formatted.append(text)
        
        return "\n\n".join(formatted)


if __name__ == '__main__':
    from src.models import get_session
    
    generator = InsightsGenerator()
    session = get_session()
    
    articles = session.query(NewsArticle).order_by(
        NewsArticle.published_date.desc()
    ).limit(15).all()
    
    session.close()
    
    if articles:
        print(f"\nAnalyzing {len(articles)} articles...\n")
        
        insights = generator.generate_insights(articles)
        if insights:
            print("=== INSIGHTS ===")
            print(insights)
        
        print("\n" + "="*50 + "\n")
        
        trends = generator.analyze_trends(articles)
        if trends:
            print("=== TRENDS ===")
            print(trends)
    else:
        print("No articles in database. Run scrapers first.")
