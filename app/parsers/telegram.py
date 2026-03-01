"""
Парсер Telegram каналов
"""
import httpx
from typing import Optional, List, Dict, Any
from datetime import datetime
from loguru import logger

from app.parsers.base import BaseParser, ParsedItem


class TelegramParser(BaseParser):
    """Парсер для Telegram каналов (через t.me)"""
    
    def __init__(self, source_config: Dict[str, Any]):
        super().__init__(source_config)
        # Извлекаем username канала из URL
        self.channel_username = self._extract_username()
    
    def _extract_username(self) -> str:
        """Извлечение username канала из URL"""
        # https://t.me/durov -> durov
        if '/s/' in self.url:
            return self.url.split('/s/')[-1].rstrip('/')
        return self.url.split('t.me/')[-1].rstrip('/')
    
    async def parse(self) -> List[ParsedItem]:
        """Парсинг канала через t.me/s/"""
        items = []
        
        try:
            # Используем публичный веб-интерфейс t.me/s/
            parse_url = f"https://t.me/s/{self.channel_username}"
            
            async with httpx.AsyncClient(timeout=30.0, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }) as client:
                response = await client.get(parse_url)
                response.raise_for_status()
                
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(response.text, 'lxml')
                
                # Ищем посты
                posts = soup.select('div.tgme_widget_message')
                
                for post in posts[:10]:  # Лимит 10
                    item = self._parse_post(post)
                    if item:
                        items.append(item)
                        
        except Exception as e:
            logger.error(f"Ошибка парсинга Telegram {self.channel_username}: {e}")
        
        return items
    
    def _parse_post(self, post) -> Optional[ParsedItem]:
        """Парсинг отдельного поста"""
        try:
            # Текст поста
            text_elem = post.select_one('div.tgme_widget_message_text')
            content = text_elem.get_text(strip=True) if text_elem else ""
            
            # Заголовок (первая строка или обрезанный текст)
            title = content[:100] + "..." if len(content) > 100 else content
            
            # Изображение
            image_url = None
            img_elem = post.select_one('a.tgme_widget_message_photo_wrap')
            if img_elem:
                style = img_elem.get('style', '')
                if 'background-image' in style:
                    import re
                    match = re.search(r"url\('([^']+)'\)", style)
                    if match:
                        image_url = match.group(1)
            
            # Дата
            published_at = None
            date_elem = post.select_one('time')
            if date_elem:
                datetime_attr = date_elem.get('datetime')
                if datetime_attr:
                    published_at = datetime.fromisoformat(datetime_attr)
            
            # Ссылка на пост
            link_elem = post.select_one('a.tgme_widget_message_date')
            url = link_elem.get('href') if link_elem else self.url
            
            return ParsedItem(
                title=title,
                content=content,
                url=url,
                image_url=image_url,
                published_at=published_at
            )
        except Exception as e:
            logger.error(f"Ошибка парсинга поста: {e}")
            return None
    
    async def parse_single(self, url: str) -> Optional[ParsedItem]:
        """Парсинг отдельного поста по URL"""
        logger.warning("TelegramParser.parse_single не реализован")
        return None
