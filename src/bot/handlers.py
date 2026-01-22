
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from src.models import User, NewsArticle, get_session
from src.processor import NewsProcessor
from src.bot.formatter import MessageFormatter
from src.ai.llm_manager import get_llm_manager
from src.ai.summarizer import ArticleSummarizer
from src.ai.insights import InsightsGenerator
from src.ai.sentiment import SentimentAnalyzer
from datetime import datetime, timedelta


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    session = get_session()
    
    db_user = session.query(User).filter_by(telegram_id=user.id).first()
    if not db_user:
        db_user = User(
            telegram_id=user.id,
            username=user.username,
            subscribed=True
        )
        session.add(db_user)
        session.commit()
    
    session.close()
    
    await update.message.reply_text(
        MessageFormatter.get_welcome_message(),
        parse_mode=ParseMode.MARKDOWN,
        disable_web_page_preview=True
    )


async def now_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⏳ Собираю последние новости...")
    
    processor = NewsProcessor()
    top_news = processor.get_top_news(limit=5, hours=24)
    processor.close()
    
    message = MessageFormatter.format_digest(top_news)
    
    await update.message.reply_text(
        message,
        parse_mode=ParseMode.MARKDOWN,
        disable_web_page_preview=True
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    llm_manager = get_llm_manager()
    help_text = MessageFormatter.get_help_message(ai_enabled=llm_manager.is_enabled())
    
    await update.message.reply_text(
        help_text,
        parse_mode=ParseMode.MARKDOWN,
        disable_web_page_preview=True
    )


async def subscribe_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    session = get_session()
    
    db_user = session.query(User).filter_by(telegram_id=user.id).first()
    if db_user:
        db_user.subscribed = True
        session.commit()
        message = "✅ Вы подписались на ежедневный дайджест!"
    else:
        db_user = User(
            telegram_id=user.id,
            username=user.username,
            subscribed=True
        )
        session.add(db_user)
        session.commit()
        message = "✅ Вы подписались на ежедневный дайджест!"
    
    session.close()
    await update.message.reply_text(message)


async def unsubscribe_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    session = get_session()
    
    db_user = session.query(User).filter_by(telegram_id=user.id).first()
    if db_user:
        db_user.subscribed = False
        session.commit()
        message = "❌ Вы отписались от ежедневного дайджеста."
    else:
        message = "Вы еще не были подписаны."
    
    session.close()
    await update.message.reply_text(message)


async def summary_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    llm_manager = get_llm_manager()
    
    if not llm_manager.is_enabled():
        await update.message.reply_text(
            "AI features are disabled. Set ENABLE_AI_FEATURES=true and add OPENAI_API_KEY to enable."
        )
        return
    
    await update.message.reply_text("Generating AI summaries...")
    
    processor = NewsProcessor()
    top_news = processor.get_top_news(limit=5, hours=24)
    processor.close()
    
    if not top_news:
        await update.message.reply_text("No recent news found.")
        return
    
    summarizer = ArticleSummarizer()
    session = get_session()
    
    response = "*AI SUMMARIES - TOP NEWS*\n\n"
    
    for i, article in enumerate(top_news, 1):
        if not article.ai_summary:
            article.ai_summary = summarizer.summarize(article.title, article.description or "")
            session.commit()
        
        response += f"*{i}. {article.title}*\n"
        if article.ai_summary:
            response += f"AI Summary: {article.ai_summary}\n"
        response += f"[Read more]({article.url})\n\n"
    
    session.close()
    
    stats = llm_manager.get_stats()
    response += f"\n_Tokens used: {stats['total_tokens']} | Est. cost: ${stats['estimated_cost']:.4f}_"
    
    await update.message.reply_text(
        response,
        parse_mode=ParseMode.MARKDOWN,
        disable_web_page_preview=True
    )


async def insights_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    llm_manager = get_llm_manager()
    
    if not llm_manager.is_enabled():
        await update.message.reply_text(
            "AI features are disabled. Enable them in settings."
        )
        return
    
    await update.message.reply_text("Analyzing trends and generating insights...")
    
    session = get_session()
    articles = session.query(NewsArticle).filter(
        NewsArticle.published_date >= datetime.utcnow() - timedelta(days=7)
    ).order_by(NewsArticle.published_date.desc()).limit(30).all()
    session.close()
    
    if not articles:
        await update.message.reply_text("Not enough data for insights.")
        return
    
    generator = InsightsGenerator()
    insights = generator.generate_insights(articles)
    
    if insights:
        response = f"*WEEKLY INSIGHTS*\n_Based on {len(articles)} articles_\n\n{insights}"
        await update.message.reply_text(
            response,
            parse_mode=ParseMode.MARKDOWN
        )
    else:
        await update.message.reply_text("Failed to generate insights.")


async def trends_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    llm_manager = get_llm_manager()
    
    if not llm_manager.is_enabled():
        await update.message.reply_text(
            "AI features are disabled."
        )
        return
    
    await update.message.reply_text("Analyzing trending topics...")
    
    session = get_session()
    articles = session.query(NewsArticle).filter(
        NewsArticle.published_date >= datetime.utcnow() - timedelta(days=3)
    ).order_by(NewsArticle.published_date.desc()).limit(25).all()
    session.close()
    
    if not articles:
        await update.message.reply_text("Not enough recent data.")
        return
    
    generator = InsightsGenerator()
    trends = generator.analyze_trends(articles)
    
    if trends:
        response = f"*TRENDING TOPICS*\n_Last 3 days | {len(articles)} articles_\n\n{trends}"
        await update.message.reply_text(
            response,
            parse_mode=ParseMode.MARKDOWN
        )
    else:
        await update.message.reply_text("Failed to analyze trends.")


async def sentiment_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    llm_manager = get_llm_manager()
    
    if not llm_manager.is_enabled():
        await update.message.reply_text(
            "AI features are disabled."
        )
        return
    
    await update.message.reply_text("Analyzing market sentiment...")
    
    session = get_session()
    articles = session.query(NewsArticle).filter(
        NewsArticle.sentiment_score.isnot(None),
        NewsArticle.published_date >= datetime.utcnow() - timedelta(days=7)
    ).order_by(NewsArticle.published_date.desc()).all()
    session.close()
    
    if not articles:
        await update.message.reply_text(
            "No sentiment data available yet. Sentiment is analyzed during scraping."
        )
        return
    
    analyzer = SentimentAnalyzer()
    stats = analyzer.get_sentiment_stats(articles)
    overview = analyzer.get_market_overview(articles)
    
    if stats:
        response = "*MARKET SENTIMENT*\n\n"
        response += f"Overall: *{stats['overall_sentiment']}* ({stats['average_score']:.2f})\n"
        response += f"Based on {stats['total_articles']} articles\n\n"
        response += f"Positive: {stats['positive']} | "
        response += f"Neutral: {stats['neutral']} | "
        response += f"Negative: {stats['negative']}\n\n"
        
        if overview:
            response += f"*Analysis:*\n{overview}"
        
        await update.message.reply_text(
            response,
            parse_mode=ParseMode.MARKDOWN
        )
    else:
        await update.message.reply_text("Failed to analyze sentiment.")


async def send_digest_to_subscribers(context: ContextTypes.DEFAULT_TYPE):
    print("[*] Sending daily digest to subscribers...")
    
    processor = NewsProcessor()
    top_news = processor.get_top_news(limit=5, hours=24)
    processor.close()
    
    if not top_news:
        print("No news to send")
        return
    
    message = MessageFormatter.format_digest(top_news)
    
    session = get_session()
    subscribers = session.query(User).filter_by(subscribed=True).all()
    session.close()
    
    sent_count = 0
    for user in subscribers:
        try:
            await context.bot.send_message(
                chat_id=user.telegram_id,
                text=message,
                parse_mode=ParseMode.MARKDOWN,
                disable_web_page_preview=True
            )
            sent_count += 1
        except Exception as e:
            print(f"Failed to send to user {user.telegram_id}: {e}")
    
    print(f"[DONE] Digest sent to {sent_count}/{len(subscribers)} subscribers")
