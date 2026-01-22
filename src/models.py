from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, Float, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

Base = declarative_base()


class NewsArticle(Base):
    __tablename__ = 'news_articles'
    
    id = Column(Integer, primary_key=True)
    title = Column(String(500), nullable=False)
    url = Column(String(1000), nullable=False, unique=True)
    description = Column(Text)
    source = Column(String(50), nullable=False)  
    published_date = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    keywords_score = Column(Float, default=0.0)  
    
    
    ai_summary = Column(Text) 
    sentiment_score = Column(Float)  
    processed_by_ai = Column(Boolean, default=False)  
    
    def __repr__(self):
        return f"<NewsArticle(title='{self.title[:50]}...', source='{self.source}')>"


class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, nullable=False, unique=True)
    username = Column(String(100))
    subscribed = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<User(telegram_id={self.telegram_id}, subscribed={self.subscribed})>"


DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///news_aggregator.db')
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine)


def init_db():
    Base.metadata.create_all(engine)
    print("Database initialized successfully!")


def get_session():
    return SessionLocal()


if __name__ == '__main__':
    init_db()
