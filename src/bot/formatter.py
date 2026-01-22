from src.models import NewsArticle
from typing import List
from datetime import datetime


class MessageFormatter:
    
    SOURCE_EMOJIS = {
        'techcrunch': '🚀',
        'sifted': '🇪🇺',
        'vcru': '🇷🇺',
        'rusbase': '💼',
        'hackernews': '🔶'
    }
    
    @staticmethod
    def format_article(article: NewsArticle, index: int = None, include_ai: bool = False) -> str:
        emoji = MessageFormatter.SOURCE_EMOJIS.get(article.source, '📰')
        
        date_str = article.published_date.strftime('%d.%m.%Y %H:%M')
        
        parts = []
        
        if index:
            parts.append(f"*{index}.* {emoji} *{article.title}*")
        else:
            parts.append(f"{emoji} *{article.title}*")
        
        if include_ai and article.ai_summary:
            parts.append(f"\n\n_AI Summary:_ {article.ai_summary}")
        elif article.description:
            desc = article.description[:200]
            if len(article.description) > 200:
                desc += '...'
            parts.append(f"\n{desc}")
        
        if include_ai and article.sentiment_score is not None:
            sentiment_emoji = "📈" if article.sentiment_score > 0.3 else "📉" if article.sentiment_score < -0.3 else "➡️"
            parts.append(f"\n{sentiment_emoji} Sentiment: {article.sentiment_score:.2f}")
        
        parts.append(f"\n\n🔗 [Читать полностью]({article.url})")
        parts.append(f"\n📅 {date_str} | 📊 {article.source.upper()}")
        
        return ''.join(parts)
    
    @staticmethod
    def format_digest(articles: List[NewsArticle]) -> str:
        if not articles:
            return "📭 Пока нет новостей за последние 24 часа."
        
        header = f"📰 *ТОП-{len(articles)} НОВОСТЕЙ О СТАРТАПАХ*\n"
        header += f"_{datetime.utcnow().strftime('%d.%m.%Y')}_\n"
        header += "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        
        formatted_articles = []
        for i, article in enumerate(articles, 1):
            formatted_articles.append(MessageFormatter.format_article(article, i))
        
        return header + '\n\n━━━━━━━━━━━━━━━━━━━━━━\n\n'.join(formatted_articles)
    
    @staticmethod
    def get_welcome_message() -> str:
        return """👋 *Добро пожаловать в Агрегатор Стартап-Новостей!*

Я собираю самые важные новости о стартапах, венчурных инвестициях и технологических прорывах из ведущих источников:

🚀 TechCrunch
🇪🇺 Sifted
🇷🇺 VC.ru
💼 Rusbase
🔶 Hacker News

*Доступные команды:*

/now — получить топ-5 новостей прямо сейчас
/subscribe — подписаться на ежедневный дайджест
/unsubscribe — отписаться от дайджеста
/help — показать эту справку

Ежедневный дайджест приходит каждый день в 9:00 UTC.
"""
    
    @staticmethod
    def get_help_message(ai_enabled: bool = False) -> str:
        base_help = """*📚 СПРАВКА*

*Команды бота:*

/start — приветственное сообщение
/now — мгновенно получить топ-5 актуальных новостей
/subscribe — включить ежедневную рассылку дайджеста
/unsubscribe — отключить ежедневную рассылку
/help — показать эту справку"""
        
        if ai_enabled:
            base_help += """\n
*🤖 AI-команды:*

/summary — AI-сводки топ новостей
/insights — еженедельные инсайты и анализ
/trends — трендовые темы за последние 3 дня
/sentiment — анализ настроения рынка"""
        
        base_help += """

*Источники новостей:*

🚀 TechCrunch — мировые стартап-новости
🇪🇺 Sifted — европейская экосистема стартапов
🇷🇺 VC.ru — новости рынка СНГ
💼 Rusbase — венчурные сделки и инвестиции
🔶 Hacker News — технологические тренды

*Как работает ранжирование?*

Новости ранжируются по:
1. Релевантности (ключевые слова: инвестиции, раунды, сделки)
2. Свежести (самые новые статьи в приоритете)

По вопросам: напишите в поддержку
"""
