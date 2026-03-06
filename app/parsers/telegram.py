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
        # https://t.me/s/durov -> durov
        if '/s/' in self.url:
            return self.url.split('/s/')[-1].split('?')[0].rstrip('/')
        return self.url.split('t.me/')[-1].split('?')[0].rstrip('/')
    
    async def parse(self) -> List[ParsedItem]:
        """Парсинг канала через t.me/s/"""
        items = []
        
        logger.info(f"Начинаем парсинг канала: {self.channel_username}")
        
        try:
            parse_url = f"https://t.me/s/{self.channel_username}"
            logger.info(f"URL для парсинга: {parse_url}")
            
            async with httpx.AsyncClient(
                timeout=30.0,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.5',
                },
                follow_redirects=True,
                verify=False  # Отключаем проверку SSL для обхода проблем
            ) as client:
                logger.info("Отправляем запрос к Telegram...")
                response = await client.get(parse_url)
                logger.info(f"Статус ответа: {response.status_code}")
                response.raise_for_status()
                
                if 'Page not found' in response.text or 'channel not found' in response.text.lower():
                    logger.error(f"Канал не найден: {self.channel_username}")
                    return items
                
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(response.text, 'lxml')
                
                posts = soup.select('div.tgme_widget_message')
                logger.info(f"Найдено постов через CSS selector: {len(posts)}")
                
                for idx, post in enumerate(posts):  # Без лимита
                    logger.info(f"Обработка поста {idx+1}")
                    item = self._parse_post(post)
                    if item:
                        logger.info(f"Пост добавлен: {item.title[:50]}...")
                        items.append(item)
                    else:
                        logger.warning(f"Пост {idx+1} не распарсен")
                        
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP ошибка: {e.response.status_code} - {e}")
        except httpx.RequestError as e:
            logger.error(f"Ошибка запроса: {e}")
        except Exception as e:
            logger.error(f"Критическая ошибка парсинга: {e}", exc_info=True)
        
        logger.info(f"Парсинг завершён. Всего постов: {len(items)}")
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
