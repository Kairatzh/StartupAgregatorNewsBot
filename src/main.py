import os
import asyncio
from dotenv import load_dotenv
from telegram.ext import Application, CommandHandler
from src.models import init_db
from src.bot.handlers import (
    start_command,
    now_command,
    help_command,
    subscribe_command,
    unsubscribe_command,
    summary_command,
    insights_command,
    trends_command,
    sentiment_command
)
from src.scheduler import NewsScheduler
from src.processor import process_all_sources

load_dotenv()


def main():
    print("Initializing database...")
    init_db()
    
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not token:
        print("[ERROR] TELEGRAM_BOT_TOKEN not set in .env file!")
        print("Please create a .env file with your bot token.")
        print("Example: TELEGRAM_BOT_TOKEN=your_token_here")
        return
    
    print("[*] Starting News Aggregator Bot...")
    print("\n[*] Running initial news scraping...")
    try:
        process_all_sources()
    except Exception as e:
        print(f"Warning: Initial scraping failed: {e}")
    
    app = Application.builder().token(token).build()
    
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("now", now_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("subscribe", subscribe_command))
    app.add_handler(CommandHandler("unsubscribe", unsubscribe_command))
    
    app.add_handler(CommandHandler("summary", summary_command))
    app.add_handler(CommandHandler("insights", insights_command))
    app.add_handler(CommandHandler("trends", trends_command))
    app.add_handler(CommandHandler("sentiment", sentiment_command))
    
    scheduler = NewsScheduler(app)
    scheduler.start()
    
    print("\n[OK] Bot is running! Press Ctrl+C to stop.\n")
    app.run_polling(allowed_updates=["message"])


if __name__ == '__main__':
    main()
