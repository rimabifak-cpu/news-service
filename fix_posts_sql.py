"""
Прямое исправление постов через SQL
Обходит ORM проблемы с асинхронностью
"""
import asyncio
import sys
from sqlalchemy import text
from loguru import logger

sys.path.insert(0, '.')

from app.database import async_session_maker
from app.models.db_models import Post, PostStatus, Source


async def fix_posts():
    """Исправление постов через SQL"""
    logger.info("=" * 60)
    logger.info("ИСПРАВЛЕНИЕ ПОСТОВ ЧЕРЕЗ SQL")
    logger.info("=" * 60)
    
    async with async_session_maker() as session:
        # Находим все посты в PROCESSING
        result = await session.execute(
            text("""
                SELECT p.id, p.source_id, p.channel_id, s.channel_id as source_channel_id
                FROM posts p
                JOIN sources s ON p.source_id = s.id
                WHERE p.status = 'processing'
            """)
        )
        processing_posts = result.all()
        
        logger.info(f"\nНайдено постов в PROCESSING: {len(processing_posts)}")
        
        if not processing_posts:
            logger.info("Нет постов в PROCESSING - все чисто!")
            return
        
        # Проверяем каналы у источников
        result = await session.execute(
            text("""
                SELECT id, name, channel_id 
                FROM sources 
                WHERE channel_id IS NOT NULL
            """)
        )
        sources_with_channels = {row[0]: {'name': row[1], 'channel_id': row[2]} for row in result.all()}
        
        result = await session.execute(
            text("""
                SELECT id, name 
                FROM sources 
                WHERE channel_id IS NULL
            """)
        )
        sources_without_channels = result.all()
        
        if sources_without_channels:
            logger.warning("\n⚠️ Источники без канала:")
            for src in sources_without_channels:
                logger.warning(f"  • {src[1]} (ID={src[0]})")
        
        fixed_count = 0
        error_count = 0
        
        for post in processing_posts:
            post_id = post[0]
            source_id = post[1]
            current_channel_id = post[2]
            source_channel_id = post[3]
            
            try:
                if not source_channel_id:
                    logger.warning(f"Пост {post_id}: у источника {source_id} нет канала, пропускаем")
                    error_count += 1
                    continue
                
                if current_channel_id == source_channel_id:
                    # Канал уже установлен, просто меняем статус на READY
                    await session.execute(
                        text("""
                            UPDATE posts 
                            SET status = :status,
                                adapted_content = COALESCE(adapted_content, original_content),
                                adapted_title = COALESCE(adapted_title, original_title)
                            WHERE id = :post_id
                        """),
                        {"status": "ready", "post_id": post_id}
                    )
                    logger.info(f"Пост {post_id}: статус изменён на READY")
                else:
                    # Устанавливаем канал и меняем статус
                    await session.execute(
                        text("""
                            UPDATE posts 
                            SET channel_id = :channel_id,
                                status = :status,
                                adapted_content = COALESCE(adapted_content, original_content),
                                adapted_title = COALESCE(adapted_title, original_title)
                            WHERE id = :post_id
                        """),
                        {"channel_id": source_channel_id, "status": "ready", "post_id": post_id}
                    )
                    logger.info(f"Пост {post_id}: установлен канал {source_channel_id}, статус READY")
                
                fixed_count += 1
                
            except Exception as e:
                logger.error(f"Пост {post_id}: ошибка - {e}")
                error_count += 1
        
        await session.commit()
        
        logger.info("\n" + "=" * 60)
        logger.info("РЕЗУЛЬТАТ:")
        logger.info(f"  ✓ Исправлено: {fixed_count}")
        logger.info(f"  ✗ Ошибок: {error_count}")
        logger.info("=" * 60)
        
        if error_count > 0:
            logger.warning("\n⚠️ Некоторые посты не исправлены - проверьте, привязаны ли источники к каналам!")


async def main():
    await fix_posts()


if __name__ == "__main__":
    asyncio.run(main())
