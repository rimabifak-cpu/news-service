"""
Скрипт для исправления постов, застрявших в статусе PROCESSING
Переводит их в статус READY
"""
import asyncio
import sys
import os

# Добавляем путь к приложению
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select, update
from app.database import async_session_maker
from app.models.db_models import Post, PostStatus


async def fix_processing_posts():
    """Исправление постов со статусом PROCESSING"""
    
    async with async_session_maker() as session:
        # Находим все посты в статусе PROCESSING
        result = await session.execute(
            select(Post).where(Post.status == PostStatus.PROCESSING.value)
        )
        processing_posts = result.scalars().all()
        
        if not processing_posts:
            print("✅ Постов со статусом PROCESSING не найдено")
            return
        
        print(f"Найдено постов в статусе PROCESSING: {len(processing_posts)}")
        
        # Переводим их в статус READY
        fixed_count = 0
        for post in processing_posts:
            # Проверяем, есть ли channel_id
            if post.channel_id:
                post.status = PostStatus.READY.value
                fixed_count += 1
                print(f"  ✓ Пост {post.id} переведён в READY")
            else:
                print(f"  ⚠️ Пост {post.id} не имеет channel_id, пропускаем")
        
        await session.commit()
        
        print(f"\n✅ Исправлено постов: {fixed_count}")


if __name__ == "__main__":
    asyncio.run(fix_processing_posts())
