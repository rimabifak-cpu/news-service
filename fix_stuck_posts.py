"""
Скрипт для исправления застрявших постов в PROCESSING
И проверки работы scheduler
"""
import asyncio
import sys
sys.path.insert(0, '/app')

from sqlalchemy import select
from sqlalchemy.orm import joinedload
from app.database import async_session_maker
from app.models.db_models import Source, Channel, Post, PostStatus

async def fix():
    async with async_session_maker() as session:
        # Находим посты в PROCESSING
        processing_posts = (await session.execute(
            select(Post)
            .options(joinedload(Post.source))
            .where(Post.status == PostStatus.PROCESSING.value)
        )).scalars().all()
        
        if not processing_posts:
            print("✅ Нет постов в статусе PROCESSING")
            return
        
        print(f"Найдено постов в PROCESSING: {len(processing_posts)}\n")
        
        fixed = 0
        for post in processing_posts:
            # Получаем канал из источника
            channel_id = post.source.channel_id if post.source else None
            
            if channel_id:
                post.channel_id = channel_id
                post.status = PostStatus.READY.value
                print(f"  ✓ Пост {post.id}: channel_id={channel_id}, статус=READY")
                fixed += 1
            else:
                print(f"  ⚠️ Пост {post.id}: источник не имеет канала")
        
        await session.commit()
        print(f"\n✅ Исправлено постов: {fixed}")

asyncio.run(fix())
