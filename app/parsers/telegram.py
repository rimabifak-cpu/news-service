"""
Парсер Telegram каналов
"""
import httpx
import asyncio
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
        # Максимум постов для получения (можно настроить)
        self.max_posts = source_config.get("max_posts", 100)

    def _extract_username(self) -> str:
        """Извлечение username канала из URL"""
        # https://t.me/durov -> durov
        # https://t.me/s/durov -> durov
        if '/s/' in self.url:
            return self.url.split('/s/')[-1].split('?')[0].rstrip('/')
        return self.url.split('t.me/')[-1].split('?')[0].rstrip('/')

    async def parse(self) -> List[ParsedItem]:
        """Парсинг канала через t.me/s/ с пагинацией"""
        items = []
        seen_urls = set()

        logger.info(f"Начинаем парсинг канала: {self.channel_username}")

        # Пагинация: ?offset=20, ?offset=40, etc.
        offset = 0
        max_pages = self.max_posts // 20 + 1  # 20 постов на странице

        try:
            async with httpx.AsyncClient(
                timeout=30.0,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.5',
                },
                follow_redirects=True,
                verify=False
            ) as client:
                for page in range(max_pages):
                    parse_url = f"https://t.me/s/{self.channel_username}"
                    if offset > 0:
                        parse_url += f"?offset={offset}"

                    logger.info(f"Парсинг страницы {page+1}: {parse_url}")

                    response = await client.get(parse_url)

                    if response.status_code != 200:
                        logger.warning(f"Статус ответа: {response.status_code}, прекращаем пагинацию")
                        break

                    if 'Page not found' in response.text or 'channel not found' in response.text.lower():
                        logger.error(f"Канал не найден: {self.channel_username}")
                        break

                    from bs4 import BeautifulSoup
                    soup = BeautifulSoup(response.text, 'lxml')

                    posts = soup.select('div.tgme_widget_message')
                    logger.info(f"Найдено постов на странице: {len(posts)}")

                    if not posts:
                        logger.info("Больше нет постов, прекращаем пагинацию")
                        break

                    new_posts_count = 0
                    for post in posts:
                        item = self._parse_post(post)
                        if item and item.url not in seen_urls:
                            seen_urls.add(item.url)
                            items.append(item)
                            new_posts_count += 1

                    logger.info(f"Добавлено {new_posts_count} новых постов")

                    # Если новых постов нет или меньше 20 — дальше нет смысла
                    if new_posts_count == 0 or new_posts_count < 20:
                        logger.info("Достигли конца ленты")
                        break

                    offset += 20

                    # Небольшая задержка между страницами
                    await asyncio.sleep(1)

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
