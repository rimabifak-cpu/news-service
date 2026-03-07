"""
Диагностика AI адаптации
"""
import asyncio
import sys
sys.path.insert(0, '/app')

from sqlalchemy import select
from sqlalchemy.orm import joinedload
from app.database import async_session_maker
from app.models.db_models import Source, Channel, Post
from app.config import settings

async def diagnose():
    async with async_session_maker() as session:
        print("=== AI Настройки ===")
        print(f"AI_API_KEY: {settings.AI_API_KEY[:20] + '...' if settings.AI_API_KEY else '❌ НЕ НАСТРОЕН'}")
        print(f"AI_API_URL: {settings.AI_API_URL}")
        print(f"AI_MODEL: {settings.AI_MODEL}")
        
        print("\n=== Каналы ===")
        channels = (await session.execute(select(Channel))).scalars().all()
        for c in channels:
            prompt_preview = (c.ai_prompt[:40] + '...') if c.ai_prompt else '❌ НЕТ ПРОМТА'
            print(f"  ID:{c.id} | {c.name} | AI промт: {prompt_preview}")
        
        print("\n=== Источники ===")
        sources = (await session.execute(
            select(Source).options(joinedload(Source.channel))
        )).scalars().all()
        
        for s in sources:
            channel_name = s.channel.name if s.channel else '❌ НЕТ КАНАЛА'
            ai_status = '✅ ВКЛ' if s.ai_enabled else '❌ ВЫКЛ'
            prompt_preview = (s.ai_prompt[:40] + '...') if s.ai_prompt else '→ использует промт канала'
            print(f"  ID:{s.id} | {s.name} | AI: {ai_status} | Канал: {channel_name} | Промт: {prompt_preview}")
        
        print("\n=== Последние посты ===")
        posts = (await session.execute(
            select(Post).order_by(Post.created_at.desc()).limit(5)
        )).scalars().all()
        
        for p in posts:
            adapted = p.adapted_content if p.adapted_content else '❌ НЕ АДАПТИРОВАН'
            print(f"  ID:{p.id} | Статус: {p.status} | Адаптация: {adapted[:50]}...")

asyncio.run(diagnose())
