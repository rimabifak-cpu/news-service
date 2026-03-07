"""
Миграция: Добавление поля is_advertisement в таблицу posts
"""
import asyncio
from sqlalchemy import text
from app.database import engine


async def run_migration():
    """Добавление колонки is_advertisement"""
    async with engine.begin() as conn:
        try:
            # Проверяем, существует ли уже колонка
            result = await conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'posts' AND column_name = 'is_advertisement'
            """))
            
            if result.fetchone():
                print("✅ Колонка is_advertisement уже существует")
                return
            
            # Добавляем колонку
            await conn.execute(text("""
                ALTER TABLE posts 
                ADD COLUMN is_advertisement BOOLEAN DEFAULT FALSE
            """))
            
            print("✅ Колонка is_advertisement добавлена")
            
        except Exception as e:
            print(f"❌ Ошибка миграции: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(run_migration())
