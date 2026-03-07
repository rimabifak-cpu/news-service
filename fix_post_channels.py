"""
Скрипт для исправления channel_id в постах
Привязывает посты к каналу их источника
"""
import asyncio
import sys
sys.path.insert(0, '/app')

from sqlalchemy import select
from sqlalchemy.orm import joinedload
from app.database import async_session_maker
from app.models.db_models import Source, Post

async def fix():
    async with async_session_maker() as session:
        # Получаем все источники с каналами
        sources_result = await session.execute(
            select(Source).options(joinedload(Source.channel))
        )
        sources = sources_result.scalars().all()
        
        # Создаём маппинг source_id -> channel_id
        source_to_channel = {s.id: s.channel_id for s in sources if s.channel_id}
        
        print(f"Источников с каналом: {len(source_to_channel)}")
        
        # Получаем все посты
        posts = (await session.execute(select(Post))).scalars().all()
        print(f"Всего постов: {len(posts)}")
        
        fixed_count = 0
        for post in posts:
            correct_channel_id = source_to_channel.get(post.source_id)
            
            if correct_channel_id is None:
                print(f"  ⚠️ Пост {post.id}: источник {post.source_id} не имеет канала")
                continue
            
            if post.channel_id != correct_channel_id:
                print(f"  ✓ Пост {post.id}: исправляем channel_id {post.channel_id} → {correct_channel_id}")
                post.channel_id = correct_channel_id
                fixed_count += 1
        
        await session.commit()
        print(f"\n✅ Исправлено постов: {fixed_count}")

asyncio.run(fix())
