"""
Диагностика и исправление постов со статусом PROCESSING
"""
import asyncio
import sys
from sqlalchemy import select, update
from sqlalchemy.orm import joinedload
from loguru import logger

sys.path.insert(0, '.')

from app.database import async_session_maker
from app.models.db_models import Post, PostStatus, Source, Channel


async def diagnose():
    """Диагностика проблемы"""
    logger.info("=" * 60)
    logger.info("ДИАГНОСТИКА ПРОБЛЕМЫ")
    logger.info("=" * 60)
    
    async with async_session_maker() as session:
        # 1. Проверяем каналы
        logger.info("\n📺 КАНАЛЫ:")
        channels = (await session.execute(select(Channel))).scalars().all()
        for ch in channels:
            logger.info(f"  • {ch.name} (ID={ch.id}, channel_id={ch.channel_id})")
            logger.info(f"    AI промт: {'✅ есть' if ch.ai_prompt else '❌ нет'}")
        
        if not channels:
            logger.error("❌ КАНАЛЫ НЕ НАЙДЕНЫ! Создайте канал в админ-панели.")
            return
        
        # 2. Проверяем источники
        logger.info("\n📡 ИСТОЧНИКИ:")
        sources = (await session.execute(
            select(Source).options(joinedload(Source.channel))
        )).scalars().all()
        
        for src in sources:
            channel_name = src.channel.name if src.channel else "❌ НЕ ПРИВЯЗАН"
            logger.info(f"  • {src.name} (ID={src.id})")
            logger.info(f"    Канал: {channel_name}")
            logger.info(f"    AI включён: {src.ai_enabled}")
            logger.info(f"    AI промт: {'✅ есть' if src.ai_prompt else '❌ нет (будет использовать промт канала)'}")
            logger.info(f"    Автопубликация: {src.auto_publish}")
        
        # 3. Проверяем посты
        logger.info("\n📝 ПОСТЫ:")
        posts = (await session.execute(
            select(Post)
            .options(joinedload(Post.source))
            .order_by(Post.created_at.desc())
            .limit(20)
        )).scalars().unique().all()
        
        status_counts = {}
        for post in posts:
            status_counts[post.status] = status_counts.get(post.status, 0) + 1
            
            if post.status == PostStatus.PROCESSING.value:
                source = post.source
                channel_via_source = source.channel if source else None
                
                logger.warning(f"\n  ⚠️ ПРОБЛЕМА: Пост ID={post.id}")
                logger.warning(f"    Заголовок: {post.original_title[:60]}...")
                logger.warning(f"    Статус: {post.status}")
                logger.warning(f"    Канал в посте: {post.channel_id}")
                logger.warning(f"    Источник ID: {post.source_id}")
                logger.warning(f"    Канал источника: {channel_via_source.id if channel_via_source else '❌ НЕ ПРИВЯЗАН'}")
                logger.warning(f"    adapted_content: {'✅ есть' if post.adapted_content else '❌ пустой'}")
                logger.warning(f"    original_content: {'✅ есть' if post.original_content else '❌ пустой'}")
        
        logger.info("\n📊 СТАТИСТИКА ПО СТАТУСАМ:")
        for status, count in status_counts.items():
            logger.info(f"  {status}: {count}")
        
        # 4. Проверяем настройки AI
        logger.info("\n🤖 НАСТРОЙКИ AI:")
        from app.config import settings
        logger.info(f"  AI API URL: {settings.AI_API_URL}")
        logger.info(f"  AI Model: {settings.AI_MODEL}")
        logger.info(f"  AI API Key: {'✅ настроен' if settings.AI_API_KEY else '❌ НЕ НАСТРОЕН'}")


async def fix_processing_posts():
    """Исправление застрявших постов"""
    logger.info("\n" + "=" * 60)
    logger.info("ИСПРАВЛЕНИЕ ПОСТОВ")
    logger.info("=" * 60)
    
    async with async_session_maker() as session:
        # Находим посты в PROCESSING без канала
        result = await session.execute(
            select(Post)
            .options(joinedload(Post.source))
            .where(Post.status == PostStatus.PROCESSING.value)
        )
        posts = result.scalars().unique().all()
        
        logger.info(f"\nНайдено постов в PROCESSING: {len(posts)}")
        
        fixed_count = 0
        error_count = 0
        
        for post in posts:
            try:
                # Получаем источник
                source = post.source
                if not source:
                    logger.error(f"Пост {post.id}: источник не найден")
                    error_count += 1
                    continue
                
                # Получаем канал из источника
                channel = source.channel
                if not channel:
                    logger.error(f"Пост {post.id}: канал источника не найден")
                    error_count += 1
                    continue
                
                # Обновляем пост
                post.channel_id = channel.id
                post.status = PostStatus.READY.value
                
                # Если нет адаптированного контента — ставим оригинал
                if not post.adapted_content:
                    post.adapted_content = post.original_content or ""
                    post.adapted_title = post.original_title or ""
                    logger.info(f"Пост {post.id}: установлен оригинальный контент (AI не сработал)")
                else:
                    logger.info(f"Пост {post.id}: готов к публикации")
                
                await session.commit()
                fixed_count += 1
                
            except Exception as e:
                logger.error(f"Пост {post.id}: ошибка при исправлении - {e}")
                await session.rollback()
                error_count += 1
        
        logger.info("\n" + "=" * 60)
        logger.info("РЕЗУЛЬТАТ:")
        logger.info(f"  ✓ Исправлено: {fixed_count}")
        logger.info(f"  ✗ Ошибок: {error_count}")
        logger.info("=" * 60)


async def main():
    await diagnose()
    
    response = input("\n🔧 Исправить застрявшие посты? (y/n): ")
    if response.lower() == 'y':
        await fix_processing_posts()
    else:
        logger.info("Отменено")


if __name__ == "__main__":
    asyncio.run(main())
