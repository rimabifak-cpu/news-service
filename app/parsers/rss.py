"""
RSS/Atom парсер
"""
import httpx
import feedparser
from typing import Optional, List, Dict, Any
from datetime import datetime
from loguru import logger

from app.parsers.base import BaseParser, ParsedItem


class RSSParser(BaseParser):
    """Парсер для RSS/Atom лент"""
    
    def __init__(self, source_config: Dict[str, Any]):
        super().__init__(source_config)
    
    async def parse(self) -> List[ParsedItem]:
        """Парсинг RSS ленты"""
        items = []
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(self.url)
                response.raise_for_status()
                
                feed = feedparser.parse(response.text)
                
                for entry in feed.entries[:10]:  # Лимит 10
                    item = ParsedItem(
                        title=entry.title if hasattr(entry, 'title') else "Без названия",
                        content=entry.get('summary', '') or entry.get('description', ''),
                        url=entry.get('link', ''),
                        image_url=self._extract_image(entry),
                        published_at=self._parse_date(entry)
                    )
                    items.append(item)
                    
        except Exception as e:
            logger.error(f"Ошибка парсинга RSS {self.url}: {e}")
        
        return items
    
    async def parse_single(self, url: str) -> Optional[ParsedItem]:
        """Для RSS не поддерживается парсинг отдельной страницы"""
        logger.warning("RSSParser не поддерживает parse_single")
        return None
    
    def _extract_image(self, entry) -> Optional[str]:
        """Извлечение изображения из RSS entry"""
        # media:content
        if hasattr(entry, 'media_content'):
            for media in entry.media_content:
                if media.get('medium') == 'image' or media.get('url', '').endswith(('.jpg', '.png', '.webp')):
                    return media.get('url')
        
        # enclosures
        if hasattr(entry, 'enclosures'):
            for enclosure in entry.enclosures:
                if enclosure.get('type', '').startswith('image/'):
                    return enclosure.get('url')
        
        # content с img
        if hasattr(entry, 'content') and entry.content:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(entry.content[0].get('value', ''), 'lxml')
            img = soup.find('img')
            if img:
                return img.get('src')
        
        # description с img
        if hasattr(entry, 'summary'):
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(entry.summary, 'lxml')
            img = soup.find('img')
            if img:
                return img.get('src')
        
        return None
    
    def _parse_date(self, entry) -> Optional[datetime]:
        """Парсинг даты из RSS entry"""
        if hasattr(entry, 'published_parsed') and entry.published_parsed:
            return datetime(*entry.published_parsed[:6])
        if hasattr(entry, 'updated_parsed') and entry.updated_parsed:
            return datetime(*entry.updated_parsed[:6])
        return None
