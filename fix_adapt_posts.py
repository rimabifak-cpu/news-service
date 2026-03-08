"""
Скрипт для AI-адаптации всех постов в очереди
Запускает адаптацию текста для постов со статусом READY или PROCESSING
у которых пустые adapted_title и adapted_content
"""
import asyncio
import sys
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

# Добавляем путь к приложению
sys.path.insert(0, '.')

from app.database import async_session_maker
from app.models.db_models import Post, PostStatus, Source, Channel
from app.services.ai_service import ai_service


async def adapt_post(session: AsyncSession, post: Post, source: Source, channel: Channel) -> bool:
    """Адаптировать один пост"""
    try:
        # Получаем оригинальный контент
        original_text = post.original_content or ""
        original_title = post.original_title or ""
        
        if not original_text:
            logger.warning(f"Пост {post.id}: пустой контент, пропускаем")
            return False
        
        # Получаем промт (источник → канал)
        ai_prompt = source.ai_prompt or (channel.ai_prompt if channel else None)
        
        logger.info(f"Пост {post.id}: адаптация текста...")
        
        # Адаптируем контент
        adapted_content = await ai_service.adapt_text(original_text, ai_prompt)
        
        # Генерируем заголовок
        adapted_title = await ai_service.generate_title(original_text)
        
        # Сохраняем результат
        post.adapted_content = adapted_content
        post.adapted_title = adapted_title
        
        await session.commit()
        
        logger.success(f"Пост {post.id}: адаптация завершена")
        logger.info(f"  Заголовок: {adapted_title[:80]}...")
        logger.info(f"  Контент: {len(adapted_content)} символов")
        
        return True
        
    except Exception as e:
        logger.error(f"Пост {post.id}: ошибка адаптации - {e}")
        await session.rollback()
        return False


async def main():
    """Основная функция"""
    logger.info("=" * 60)
    logger.info("AI-адаптация постов в очереди")
    logger.info("=" * 60)
    
    async with async_session_maker() as session:
        # Находим посты без адаптированного контента
        query = select(Post).where(
            Post.status.in_([PostStatus.READY.value, PostStatus.PROCESSING.value, PostStatus.PENDING.value])
        )
        result = await session.execute(query)
        posts = result.scalars().all()
        
        # Фильтруем посты без адаптированного контента
        posts_to_adapt = [
            p for p in posts 
            if not p.adapted_content or not p.adapted_title
        ]
        
        logger.info(f"Найдено постов в очереди: {len(posts)}")
        logger.info(f"Требуют адаптации: {len(posts_to_adapt)}")
        logger.info("=" * 60)
        
        if not posts_to_adapt:
            logger.info("Все посты уже адаптированы!")
            return
        
        # Адаптируем каждый пост
        success_count = 0
        error_count = 0
        
        for post in posts_to_adapt:
            # Получаем источник и канал
            source_result = await session.execute(
                select(Source).where(Source.id == post.source_id)
            )
            source = source_result.scalar_one_or_none()
            
            if not source:
                logger.warning(f"Пост {post.id}: источник не найден, пропускаем")
                error_count += 1
                continue
            
            channel = source.channel
            
            if not channel:
                logger.warning(f"Пост {post.id}: канал не найден, пропускаем")
                error_count += 1
                continue
            
            # Адаптируем
            result = await adapt_post(session, post, source, channel)
            if result:
                success_count += 1
            else:
                error_count += 1
            
            # Небольшая пауза между запросами к API
            await asyncio.sleep(0.5)
        
        logger.info("=" * 60)
        logger.info("Результаты:")
        logger.info(f"  ✓ Успешно адаптировано: {success_count}")
        logger.info(f"  ✗ Ошибок: {error_count}")
        logger.info("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
