import os
from typing import Optional
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.callbacks import get_openai_callback

load_dotenv()


class LLMManager:
    def __init__(self):
        self.api_key = os.getenv('OPENAI_API_KEY')
        self.model = os.getenv('AI_MODEL', 'gpt-3.5-turbo')
        self.enabled = os.getenv('ENABLE_AI_FEATURES', 'false').lower() == 'true'
        self.total_tokens_used = 0
        self._llm = None
    
    def is_enabled(self) -> bool:
        """Check if AI features are enabled."""
        return self.enabled and self.api_key is not None
    
    def get_llm(self, temperature: float = 0.3) -> Optional[ChatOpenAI]:
        """Get LangChain ChatOpenAI instance."""
        if not self.is_enabled():
            return None
        
        if self._llm is None:
            self._llm = ChatOpenAI(
                model=self.model,
                temperature=temperature,
                openai_api_key=self.api_key
            )
        
        return self._llm
    
    def track_usage(self, tokens: int):
        self.total_tokens_used += tokens
    
    def estimate_cost(self) -> float:
        cost_per_1k = 0.002
        return (self.total_tokens_used / 1000) * cost_per_1k
    
    def get_stats(self) -> dict:
        return {
            'total_tokens': self.total_tokens_used,
            'estimated_cost': self.estimate_cost(),
            'model': self.model,
            'enabled': self.enabled
        }


llm_manager = LLMManager()


def get_llm_manager() -> LLMManager:
    return llm_manager
