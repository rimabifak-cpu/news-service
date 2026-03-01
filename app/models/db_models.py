"""
Модели базы данных
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Enum, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import enum

Base = declarative_base()


class SourceType(str, enum.Enum):
    WEBSITE = "website"
    TELEGRAM = "telegram"
    VK = "vk"
    RSS = "rss"


class PostStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    READY = "ready"
    PUBLISHED = "published"
    REJECTED = "rejected"


class Source(Base):
    """Источники новостей"""
    __tablename__ = "sources"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    url = Column(String(1024), nullable=False)
    source_type = Column(String(50), default=SourceType.WEBSITE.value)
    is_active = Column(Boolean, default=True)
    
    # Настройки парсинга
    selector_title = Column(String(255))
    selector_content = Column(String(255))
    selector_image = Column(String(255))
    selector_date = Column(String(255))
    
    # AI настройки
    ai_prompt = Column(Text)  # Промт для адаптации текста
    ai_enabled = Column(Boolean, default=True)
    
    # Метаданные
    last_parsed = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    posts = relationship("Post", back_populates="source", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Source {self.name} ({self.source_type})>"


class Post(Base):
    """Посты/новости"""
    __tablename__ = "posts"
    
    id = Column(Integer, primary_key=True)
    source_id = Column(Integer, ForeignKey("sources.id"), nullable=False)
    
    # Данные из источника
    original_title = Column(Text, nullable=False)
    original_content = Column(Text)
    original_url = Column(String(1024))
    original_image_url = Column(String(1024))
    original_published_at = Column(DateTime)
    
    # Адаптированные данные
    adapted_title = Column(Text)
    adapted_content = Column(Text)
    
    # Обработанное изображение
    processed_image_path = Column(String(512))
    
    # Статус и публикация
    status = Column(String(50), default=PostStatus.PENDING.value)
    telegram_message_id = Column(Integer)
    published_at = Column(DateTime)
    
    # Метаданные
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    source = relationship("Source", back_populates="posts")
    
    def __repr__(self):
        return f"<Post {self.original_title[:50]}...>"


class TelegramChannel(Base):
    """Telegram каналы для публикации"""
    __tablename__ = "telegram_channels"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    channel_id = Column(String(255), nullable=False)  # @channel или ID
    bot_token = Column(String(255))  # Можно использовать общего бота
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<TelegramChannel {self.name}>"


class LogoSettings(Base):
    """Настройки логотипа"""
    __tablename__ = "logo_settings"
    
    id = Column(Integer, primary_key=True)
    logo_path = Column(String(512))
    position = Column(String(50), default="bottom-right")  # top-left, top-right, bottom-left, bottom-right
    opacity = Column(Float, default=0.7)
    scale = Column(Float, default=1.0)
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
