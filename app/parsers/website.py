"""
Парсер сайтов
"""
import httpx
from typing import Optional, List, Dict, Any
from datetime import datetime
from loguru import logger

from app.parsers.base import BaseParser, ParsedItem


class WebsiteParser(BaseParser):
    """Парсер для веб-сайтов"""
    
    def __init__(self, source_config: Dict[str, Any]):
        super().__init__(source_config)
        self.selector_title = source_config.get("selector_title", "h1")
        self.selector_content = source_config.get("selector_content", "article, .content, .post-content")
        self.selector_image = source_config.get("selector_image", "img.featured, .post-image img")
        self.selector_date = source_config.get("selector_date", "time, .date, .published")
    
    async def parse(self) -> List[ParsedItem]:
        """Парсинг главной страницы или ленты новостей"""
        items = []
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(self.url)
                response.raise_for_status()
                
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(response.text, 'lxml')
                
                # Ищем ссылки на статьи
                links = soup.select('a[href]')
                seen_urls = set()
                
                for link in links:
                    href = link.get('href', '')
                    if href and href not in seen_urls:
                        # Проверяем, что это внутренняя ссылка
                        if href.startswith('/') or self.url.split('/')[2] in href:
                            if not href.startswith('/') and self.url.split('/')[2] not in href:
                                continue
                            
                            full_url = self._make_full_url(href)
                            if full_url not in seen_urls:
                                seen_urls.add(full_url)
                                
                                # Парсим отдельную страницу
                                item = await self.parse_single(full_url)
                                if item:
                                    items.append(item)
                                    if len(items) >= 10:  # Лимит
                                        break
        except Exception as e:
            logger.error(f"Ошибка парсинга {self.url}: {e}")
        
        return items
    
    async def parse_single(self, url: str) -> Optional[ParsedItem]:
        """Парсинг отдельной страницы"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url)
                response.raise_for_status()
                
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(response.text, 'lxml')
                
                # Извлекаем заголовок
                title = self.extract_text(str(soup), self.selector_title)
                if not title:
                    title = soup.find('title')
                    title = title.get_text(strip=True) if title else "Без названия"
                
                # Извлекаем контент
                content = self.extract_text(str(soup), self.selector_content)
                
                # Извлекаем изображение
                image_url = None
                img_elem = soup.select_one(self.selector_image)
                if img_elem:
                    image_url = img_elem.get('src') or img_elem.get('data-src')
                    if image_url:
                        image_url = self._make_full_url(image_url)
                
                # Извлекаем дату
                published_at = None
                date_elem = soup.select_one(self.selector_date)
                if date_elem:
                    date_text = date_elem.get_text(strip=True)
                    published_at = self._parse_date(date_text)
                
                return ParsedItem(
                    title=title[:500],
                    content=content[:5000] if content else "",
                    url=url,
                    image_url=image_url,
                    published_at=published_at
                )
        except Exception as e:
            logger.error(f"Ошибка парсинга страницы {url}: {e}")
            return None
    
    def _make_full_url(self, href: str) -> str:
        """Преобразование относительной ссылки в абсолютную"""
        if href.startswith('http'):
            return href
        
        from urllib.parse import urljoin
        return urljoin(self.url, href)
    
    def _parse_date(self, date_text: str) -> Optional[datetime]:
        """Парсинг даты из текста"""
        if not date_text:
            return None
        
        from dateutil import parser as date_parser
        try:
            return date_parser.parse(date_text, fuzzy=True)
        except:
            return None
