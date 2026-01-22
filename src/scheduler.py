from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime
import os
from dotenv import load_dotenv
from src.processor import process_all_sources

load_dotenv()


class NewsScheduler:
    def __init__(self, bot_context):
        self.scheduler = AsyncIOScheduler()
        self.bot_context = bot_context
        self.parsing_interval = int(os.getenv('PARSING_INTERVAL_HOURS', 2))
        self.digest_time = os.getenv('DIGEST_TIME', '09:00')
    
    def scraping_job(self):
        print(f"\n[SCHEDULED] [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Running scheduled scraping...")
        try:
            process_all_sources()
        except Exception as e:
            print(f"Error in scraping job: {e}")
    
    def start(self):
        self.scheduler.add_job(
            self.scraping_job,
            'interval',
            hours=self.parsing_interval,
            id='scraping_job',
            name='Scrape news sources'
        )
        
        hour, minute = self.digest_time.split(':')
        self.scheduler.add_job(
            self.send_daily_digest,
            'cron',
            hour=int(hour),
            minute=int(minute),
            id='daily_digest',
            name='Send daily digest'
        )
        
        self.scheduler.start()
        print(f"[OK] Scheduler started:")
        print(f"   - Scraping: every {self.parsing_interval} hours")
        print(f"   - Daily digest: {self.digest_time} UTC")
    
    async def send_daily_digest(self):
        from src.bot.handlers import send_digest_to_subscribers
        await send_digest_to_subscribers(self.bot_context)
    
    def stop(self):
        self.scheduler.shutdown()
