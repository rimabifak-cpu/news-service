"""
Миграция: добавление колонки content_hash в таблицу posts
"""
import asyncio
from sqlalchemy import text
from app.database import engine

async def migrate():
    async with engine.begin() as conn:
        # Проверяем, существует ли колонка
        result = await conn.execute(text("PRAGMA table_info(posts)"))
        columns = [row[1] for row in result.fetchall()]
        
        if 'content_hash' not in columns:
            await conn.execute(text(
                "ALTER TABLE posts ADD COLUMN content_hash VARCHAR(64)"
            ))
            print("Колонка content_hash добавлена")
        else:
            print("Колонка content_hash уже существует")

if __name__ == "__main__":
    asyncio.run(migrate())
