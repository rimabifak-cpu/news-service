"""
Сервис обработки новостей
"""
from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger
import os
import hashlib

from app.models.db_models import Source, Post, PostStatus
from app.database import async_session_maker
from app.parsers.base import ParsedItem
from app.services.ai_service import ai_service
from app.services.image_service import image_service
from app.config import settings


def _to_naive_datetime(dt: Optional[datetime]) -> Optional[datetime]:
    """Конвертировать timezone-aware datetime в naive (без timezone)"""
    if dt is None:
        return None
    if dt.tzinfo is not None:
        # Конвертируем в UTC и убираем tzinfo
        dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt


class NewsProcessor:
    """Сервис для обработки новостей"""
    
    async def process_source(self, source_id: int) -> int:
        """
        Обработка источника новостей
        
        Args:
            source_id: ID источника
        
        Returns:
            Количество обработанных постов
        """
        async with async_session_maker() as session:
            # Получаем источник
            result = await session.execute(
                select(Source).where(Source.id == source_id)
            )
            source = result.scalar_one_or_none()
            
            if not source or not source.is_active:
                logger.warning(f"Источник {source_id} не найден или не активен")
                return 0
            
            logger.info(f"Начинаем обработку источника: {source.name}")
            
            # Получаем парсер
            parser = self._get_parser(source)
            if not parser:
                logger.error(f"Не удалось создать парсер для {source.source_type}")
                return 0
            
            # Парсим
            items = await parser.parse()
            logger.info(f"Найдено {len(items)} постов")
            
            # Обрабатываем каждый пост
            processed_count = 0
            for item in items:
                try:
                    await self._process_item(session, source, item)
                    processed_count += 1
                except Exception as e:
                    logger.error(f"Ошибка обработки поста {item.url}: {e}")
            
            # Обновляем время последнего парсинга
            source.last_parsed = datetime.utcnow()
            await session.commit()
            
            logger.info(f"Обработано {processed_count} постов из {source.name}")
            return processed_count
    
    def _get_parser(self, source: Source):
        """Получение парсера для источника"""
        from app.parsers.website import WebsiteParser
        from app.parsers.rss import RSSParser
        from app.parsers.telegram import TelegramParser
        from app.parsers.vk import VKParser
        
        source_config = {
            "name": source.name,
            "url": source.url,
            "selector_title": source.selector_title,
            "selector_content": source.selector_content,
            "selector_image": source.selector_image,
            "selector_date": source.selector_date,
        }
        
        source_type = source.source_type.lower()
        
        if source_type == "rss":
            return RSSParser(source_config)
        elif source_type == "telegram":
            return TelegramParser(source_config)
        elif source_type == "vk":
            return VKParser(source_config)
        else:
            return WebsiteParser(source_config)
    
    async def _process_item(
        self,
        session: AsyncSession,
        source: Source,
        item: ParsedItem
    ):
        """Обработка отдельного поста"""
        # Вычисляем хеш контента
        content_for_hash = f"{item.title}|{item.content}".encode('utf-8')
        content_hash = hashlib.sha256(content_for_hash).hexdigest()
        
        # Проверяем, нет ли уже такого поста по URL или хешу
        result = await session.execute(
            select(Post).where(
                (Post.original_url == item.url) | 
                (Post.content_hash == content_hash)
            )
        )
        if result.scalar_one_or_none():
            logger.debug(f"Пост уже существует: {item.url} (hash: {content_hash[:8]}...)")
            return
        
        # Создаём пост
        post = Post(
            source_id=source.id,
            original_title=item.title,
            original_content=item.content,
            original_url=item.url,
            original_image_url=item.image_url,
            original_published_at=_to_naive_datetime(item.published_at),
            content_hash=content_hash,  # Сохраняем хеш для дедупликации
            status=PostStatus.PROCESSING.value
        )
        
        session.add(post)
        await session.flush()  # Получаем ID
        
        # Адаптируем текст через AI
        if source.ai_enabled:
            adapted_content = await ai_service.adapt_text(
                item.content,
                source.ai_prompt
            )
            adapted_title = await ai_service.generate_title(item.content)
            
            post.adapted_content = adapted_content
            post.adapted_title = adapted_title
        else:
            post.adapted_content = item.content
            post.adapted_title = item.title
        
        # Обрабатываем изображение
        if item.image_url:
            image_path = await self._process_image(item.image_url, post.id)
            if image_path:
                post.processed_image_path = image_path
        
        post.status = PostStatus.READY.value
        await session.commit()
        
        logger.info(f"Пост {post.id} готов к публикации")
    
    async def _process_image(
        self,
        image_url: str,
        post_id: int
    ) -> Optional[str]:
        """Обработка изображения"""
        try:
            # Создаём директорию для поста
            post_dir = os.path.join(settings.UPLOAD_FOLDER, f"post_{post_id}")
            os.makedirs(post_dir, exist_ok=True)
            
            # Скачиваем изображение
            temp_path = os.path.join(post_dir, "original.jpg")
            downloaded_path = await image_service.download_image(image_url, temp_path)
            
            if not downloaded_path:
                return None
            
            # Добавляем логотип
            output_path = os.path.join(post_dir, "processed.jpg")
            result_path = await image_service.add_logo(downloaded_path, output_path)
            
            return result_path
            
        except Exception as e:
            logger.error(f"Ошибка обработки изображения: {e}")
            return None
    
    async def get_pending_posts(self, limit: int = 10) -> List[Post]:
        """Получение постов, ожидающих обработки"""
        async with async_session_maker() as session:
            result = await session.execute(
                select(Post)
                .where(Post.status == PostStatus.PENDING.value)
                .limit(limit)
            )
            return list(result.scalars().all())
    
    async def get_ready_posts(self, limit: int = 20) -> List[Post]:
        """Получение готовых к публикации постов"""
        async with async_session_maker() as session:
            result = await session.execute(
                select(Post)
                .where(Post.status == PostStatus.READY.value)
                .order_by(Post.created_at.desc())
                .limit(limit)
            )
            return list(result.scalars().all())


# Singleton
news_processor = NewsProcessor()
