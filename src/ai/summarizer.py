
from typing import Optional
from langchain.prompts import ChatPromptTemplate
from langchain.chains import LLMChain
from langchain.callbacks import get_openai_callback
from src.ai.llm_manager import get_llm_manager


class ArticleSummarizer:
    
    def __init__(self):
        self.llm_manager = get_llm_manager()
        self.llm = self.llm_manager.get_llm(temperature=0.3)
        
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert startup news analyst. Create a concise, informative summary.
            
Rules:
- 2-3 sentences maximum
- Focus on key facts: funding amounts, companies, investors
- Be objective and factual
- Use clear, professional language
- Support both English and Russian"""),
            ("user", """Title: {title}

Description: {description}

Create a brief summary in the same language as the article:""")
        ])
    
    def summarize(self, title: str, description: str) -> Optional[str]:
        if not self.llm_manager.is_enabled() or not self.llm:
            return None
        
        try:
            with get_openai_callback() as cb:
                chain = self.prompt | self.llm
                
                result = chain.invoke({
                    "title": title,
                    "description": description[:1000]  
                })
                
                self.llm_manager.track_usage(cb.total_tokens)
                
                if hasattr(result, 'content'):
                    return result.content.strip()
                return str(result).strip()
                
        except Exception as e:
            print(f"[AI] Summarization error: {e}")
            return None
    
    def summarize_batch(self, articles: list) -> dict:
        summaries = {}
        
        for i, article in enumerate(articles):
            summary = self.summarize(
                article.get('title', ''),
                article.get('description', '')
            )
            if summary:
                summaries[i] = summary
        
        return summaries


if __name__ == '__main__':
    summarizer = ArticleSummarizer()
    
    test_article = {
        'title': 'AI Startup Raises $50M Series A',
        'description': 'TechVenture, an AI-powered analytics platform, announced today that it has raised $50 million in Series A funding led by Sequoia Capital. The company plans to use the funds to expand its engineering team and accelerate product development.'
    }
    
    summary = summarizer.summarize(
        test_article['title'],
        test_article['description']
    )
    
    if summary:
        print(f"Original: {test_article['description']}")
        print(f"\nAI Summary: {summary}")
    else:
        print("AI features disabled. Set ENABLE_AI_FEATURES=true and add OPENAI_API_KEY to .env")
