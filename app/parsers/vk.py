"""
Парсер ВКонтакте
"""
import httpx
from typing import Optional, List, Dict, Any
from datetime import datetime
from loguru import logger

from app.parsers.base import BaseParser, ParsedItem


class VKParser(BaseParser):
    """Парсер для ВКонтакте (публичные страницы)"""
    
    def __init__(self, source_config: Dict[str, Any]):
        super().__init__(source_config)
        self.group_id = self._extract_group_id()
    
    def _extract_group_id(self) -> str:
        """Извлечение ID группы из URL"""
        # https://vk.com/public123456 или https://vk.com/club123456
        if '/public' in self.url:
            return self.url.split('/public')[-1].rstrip('/')
        elif '/club' in self.url:
            return self.url.split('/club')[-1].rstrip('/')
        elif '/vk.com/' in self.url:
            return self.url.split('/vk.com/')[-1].rstrip('/')
        return self.url
    
    async def parse(self) -> List[ParsedItem]:
        """Парсинг стены группы"""
        items = []
        
        try:
            # Используем мобильную версию для упрощения парсинга
            parse_url = f"https://m.vk.com/wall-{self.group_id}"
            
            async with httpx.AsyncClient(timeout=30.0, headers={
                'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)'
            }) as client:
                response = await client.get(parse_url)
                response.raise_for_status()
                
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(response.text, 'lxml')
                
                # Ищем посты на стене
                posts = soup.select('div.post')
                
                for post in posts[:10]:  # Лимит 10
                    item = self._parse_post(post)
                    if item:
                        items.append(item)
                        
        except Exception as e:
            logger.error(f"Ошибка парсинга VK {self.group_id}: {e}")
        
        return items
    
    def _parse_post(self, post) -> Optional[ParsedItem]:
        """Парсинг отдельного поста"""
        try:
            # Текст поста
            text_elem = post.select_one('div.post_text')
            content = text_elem.get_text(strip=True) if text_elem else ""
            
            # Заголовок
            title = content[:100] + "..." if len(content) > 100 else content
            
            # Изображение
            image_url = None
            img_elem = post.select_one('img.post_img')
            if img_elem:
                image_url = img_elem.get('src')
            
            # Дата
            published_at = None
            date_elem = post.select_one('span.post_date')
            if date_elem:
                date_text = date_elem.get_text(strip=True)
                published_at = self._parse_date(date_text)
            
            # Ссылка на пост
            link_elem = post.select_one('a.post_link')
            url = link_elem.get('href') if link_elem else self.url
            if url.startswith('/'):
                url = f"https://vk.com{url}"
            
            return ParsedItem(
                title=title,
                content=content,
                url=url,
                image_url=image_url,
                published_at=published_at
            )
        except Exception as e:
            logger.error(f"Ошибка парсинга поста VK: {e}")
            return None
    
    def _parse_date(self, date_text: str) -> Optional[datetime]:
        """Парсинг даты из текста"""
        try:
            # Форматы: "сегодня в 14:30", "вчера в 10:00", "2 мар в 18:45"
            from dateutil import parser as date_parser
            return date_parser.parse(date_text, fuzzy=True)
        except:
            return None
    
    async def parse_single(self, url: str) -> Optional[ParsedItem]:
        """Парсинг отдельного поста по URL"""
        logger.warning("VKParser.parse_single не реализован")
        return None
