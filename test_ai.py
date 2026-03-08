"""
Диагностика AI адаптации
"""
import asyncio
import sys
from sqlalchemy import select, text
from sqlalchemy.orm import selectinload
from loguru import logger

sys.path.insert(0, '.')

from app.database import async_session_maker
from app.models.db_models import Source, Channel, Post, PostStatus
from app.services.ai_service import ai_service


async def diagnose():
    logger.info("=" * 60)
    logger.info("ДИАГНОСТИКА AI АДАПТАЦИИ")
    logger.info("=" * 60)
    
    async with async_session_maker() as session:
        # 1. Проверка настроек AI
        logger.info("\n🤖 НАСТРОЙКИ AI:")
        from app.config import settings
        logger.info(f"  AI API URL: {settings.AI_API_URL}")
        logger.info(f"  AI Model: {settings.AI_MODEL}")
        logger.info(f"  AI API Key: {'✅ ' + settings.AI_API_KEY[:20] + '...' if settings.AI_API_KEY else '❌ НЕ НАСТРОЕН'}")
        
        # 2. Тест AI API
        logger.info("\n🧪 ТЕСТ AI API:")
        try:
            result = await ai_service.adapt_text("Тест", "Сократи до 10 символов")
            logger.info(f"  ✅ AI работает: {result[:50]}...")
        except Exception as e:
            logger.error(f"  ❌ AI не работает: {e}")
        
        # 3. Проверка каналов
        logger.info("\n📺 КАНАЛЫ:")
        channels = (await session.execute(select(Channel))).scalars().all()
        for ch in channels:
            logger.info(f"  • {ch.name} (ID={ch.id})")
            logger.info(f"    AI промт: {'✅ ' + ch.ai_prompt[:50] + '...' if ch.ai_prompt else '❌ ПУСТОЙ'}")
        
        # 4. Проверка источников
        logger.info("\n📡 ИСТОЧНИКИ:")
        sources = (await session.execute(
            select(Source).options(selectinload(Source.channel))
        )).scalars().all()
        
        for src in sources:
            logger.info(f"  • {src.name} (ID={src.id})")
            logger.info(f"    Канал: {src.channel.name if src.channel else '❌ НЕ ПРИВЯЗАН'}")
            logger.info(f"    AI включён: {'✅' if src.ai_enabled else '❌'}")
            logger.info(f"    AI промт: {'✅ ' + src.ai_prompt[:50] + '...' if src.ai_prompt else '❌ ПУСТОЙ (использует промт канала)'}")
            logger.info(f"    Автопубликация: {'✅' if src.auto_publish else '❌'}")
        
        # 5. Проверка последних постов
        logger.info("\n📝 ПОСЛЕДНИЕ ПОСТЫ:")
        posts_result = await session.execute(
            select(Post)
            .options(selectinload(Post.source).selectinload(Source.channel))
            .order_by(Post.created_at.desc())
            .limit(5)
        )
        posts = posts_result.scalars().unique().all()
        
        for post in posts:
            source = post.source
            logger.info(f"\n  Пост ID={post.id}")
            logger.info(f"    Заголовок: {post.original_title[:60]}...")
            logger.info(f"    Статус: {post.status}")
            logger.info(f"    Канал: {post.channel_id}")
            logger.info(f"    AI включён у источника: {'✅' if source.ai_enabled else '❌'}")
            logger.info(f"    original_content: {len(post.original_content) if post.original_content else 0} символов")
            logger.info(f"    adapted_content: {'✅ ' + post.adapted_content[:50] + '...' if post.adapted_content else '❌ ПУСТОЙ'}")
            logger.info(f"    adapted_title: {'✅ ' + post.adapted_title[:50] + '...' if post.adapted_title else '❌ ПУСТОЙ'}")
            
            # Если нет адаптации
            if not post.adapted_content and post.original_content:
                logger.warning(f"    ⚠️ НЕТ AI АДАПТАЦИИ!")
                if not source.ai_enabled:
                    logger.warning(f"    Причина: AI отключён в источнике")
                elif not post.original_content:
                    logger.warning(f"    Причина: Пустой original_content")
        
        # 6. Статистика
        logger.info("\n📊 СТАТИСТИКА:")
        result = await session.execute(
            select(Post.status, text("COUNT(*)")).group_by(Post.status)
        )
        for row in result.all():
            logger.info(f"  {row[0]}: {row[1]}")


async def test_ai():
    """Тест AI с реальным текстом"""
    logger.info("\n" + "=" * 60)
    logger.info("ТЕСТ AI АДАПТАЦИИ")
    logger.info("=" * 60)
    
    test_text = """
    Президент России Владимир Путин провёл совещание с правительством.
    Обсуждались вопросы экономики и социальной поддержки граждан.
    Президент подчеркнул важность выполнения всех социальных обязательств.
    """
    
    logger.info(f"\nИсходный текст:\n{test_text}")
    
    try:
        adapted = await ai_service.adapt_text(test_text, "Адаптируй для Telegram: добавь эмодзи, разбей на абзацы")
        logger.info(f"\n✅ Адаптированный текст:\n{adapted}")
    except Exception as e:
        logger.error(f"\n❌ Ошибка AI: {e}")


async def main():
    await diagnose()
    await test_ai()


if __name__ == "__main__":
    asyncio.run(main())
